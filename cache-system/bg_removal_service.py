#!/usr/bin/env python3

"""
Background Removal Service
===========================

Abstract interface for multiple background removal providers (Gemini, Banana).
Handles API calls, error handling, and response caching.
"""

import os
import io
import json
import base64
import requests
import hashlib
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from PIL import Image
from datetime import datetime, timezone
from pymongo import MongoClient


class BackgroundRemovalProvider(ABC):
    """Abstract base class for background removal providers"""
    
    @abstractmethod
    def remove_background(self, image_path: str) -> Tuple[Optional[bytes], Dict[str, Any]]:
        """
        Remove background from image.
        
        Returns:
            Tuple of (processed_image_bytes, metadata_dict)
            Returns (None, error_dict) on failure
        """
        pass
    
    @abstractmethod
    def get_cost_estimate(self) -> float:
        """Return estimated cost per image in USD"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name"""
        pass


class GeminiBackgroundRemoval(BackgroundRemovalProvider):
    """Gemini Vision API background removal provider"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.cost_per_image = 0.002  # Estimated cost in USD
        
    def remove_background(self, image_path: str) -> Tuple[Optional[bytes], Dict[str, Any]]:
        """Remove background using Gemini Vision API"""
        try:
            # Load and prepare image
            with Image.open(image_path) as img:
                # Convert HEIC/other formats to PNG
                if img.format != 'PNG':
                    buffer = io.BytesIO()
                    img.convert('RGBA').save(buffer, format='PNG')
                    image_data = buffer.getvalue()
                else:
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
            
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare request
            payload = {
                "contents": [{
                    "parts": [
                        {
                            "text": "Remove the background from this product image. Return only the foreground object with a transparent background. Output as PNG with transparency."
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_base64
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "response_mime_type": "image/png"
                }
            }
            
            # Make API request
            headers = {
                "Content-Type": "application/json"
            }
            url = f"{self.endpoint}?key={self.api_key}"
            
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract processed image from response
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'inline_data' in part:
                            processed_data = base64.b64decode(part['inline_data']['data'])
                            
                            metadata = {
                                'provider': self.get_provider_name(),
                                'status': 'success',
                                'cost': self.cost_per_image,
                                'timestamp': datetime.now(timezone.utc).isoformat(),
                                'original_size': len(image_data),
                                'processed_size': len(processed_data)
                            }
                            
                            return processed_data, metadata
            
            # No valid response
            return None, {
                'provider': self.get_provider_name(),
                'status': 'error',
                'error': 'No valid image data in response',
                'response': result
            }
            
        except Exception as e:
            return None, {
                'provider': self.get_provider_name(),
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_cost_estimate(self) -> float:
        return self.cost_per_image
    
    def get_provider_name(self) -> str:
        return "gemini"


class RemoveBgProvider(BackgroundRemovalProvider):
    """Remove.bg API background removal provider (specialized for background removal)"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://api.remove.bg/v1.0/removebg"
        self.cost_per_image = 0.002  # Estimated cost in USD per image
    
    def remove_background(self, image_path: str) -> Tuple[Optional[bytes], Dict[str, Any]]:
        """Remove background using Remove.bg API"""
        try:
            # Load image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Prepare request
            response = requests.post(
                self.endpoint,
                files={'image_file': image_data},
                data={'size': 'auto'},
                headers={'X-Api-Key': self.api_key},
                timeout=60
            )
            response.raise_for_status()
            
            # Get processed image
            processed_data = response.content
            
            metadata = {
                'provider': self.get_provider_name(),
                'status': 'success',
                'cost': self.cost_per_image,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'original_size': len(image_data),
                'processed_size': len(processed_data)
            }
            
            return processed_data, metadata
            
        except Exception as e:
            return None, {
                'provider': self.get_provider_name(),
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_cost_estimate(self) -> float:
        return self.cost_per_image
    
    def get_provider_name(self) -> str:
        return "remove_bg"


class BananaBackgroundRemoval(BackgroundRemovalProvider):
    """Banana API background removal provider (serverless GPU)"""
    
    def __init__(self, api_key: str, model_key: Optional[str] = None):
        self.api_key = api_key
        self.model_key = model_key or os.getenv('BANANA_MODEL_KEY', '')
        self.endpoint = "https://api.banana.dev/run"
        self.cost_per_image = 0.005  # Estimated cost in USD
        
    def remove_background(self, image_path: str) -> Tuple[Optional[bytes], Dict[str, Any]]:
        """Remove background using Banana API"""
        try:
            # Load and prepare image
            with Image.open(image_path) as img:
                buffer = io.BytesIO()
                img.convert('RGB').save(buffer, format='PNG')
                image_data = buffer.getvalue()
            
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare request
            payload = {
                "apiKey": self.api_key,
                "modelKey": self.model_key,
                "modelInputs": {
                    "image": image_base64,
                    "task": "background_removal"
                }
            }
            
            # Make API request
            response = requests.post(self.endpoint, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract processed image from response
            if 'modelOutputs' in result and 'image' in result['modelOutputs']:
                processed_data = base64.b64decode(result['modelOutputs']['image'])
                
                metadata = {
                    'provider': self.get_provider_name(),
                    'status': 'success',
                    'cost': self.cost_per_image,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'original_size': len(image_data),
                    'processed_size': len(processed_data),
                    'processing_time': result.get('executionTime', 0)
                }
                
                return processed_data, metadata
            
            return None, {
                'provider': self.get_provider_name(),
                'status': 'error',
                'error': 'No valid image data in response',
                'response': result
            }
            
        except Exception as e:
            return None, {
                'provider': self.get_provider_name(),
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_cost_estimate(self) -> float:
        return self.cost_per_image
    
    def get_provider_name(self) -> str:
        return "banana"


class BackgroundRemovalService:
    """Main service orchestrating background removal operations"""
    
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/"):
        self.providers: Dict[str, BackgroundRemovalProvider] = {}
        self.default_provider = None
        
        # Connect to MongoDB for caching
        self.client = MongoClient(mongo_uri)
        self.db = self.client['square_cache']
        self.cache_collection = self.db['bg_removal_cache']
        
        # Create indexes
        self.cache_collection.create_index("image_hash", unique=True)
        
        # Initialize providers from environment
        self._init_providers()
    
    def _init_providers(self):
        """Initialize available providers from environment variables"""
        # Remove.bg is the recommended provider for background removal
        removebg_key = os.getenv('REMOVEBG_API_KEY')
        if removebg_key:
            self.providers['remove_bg'] = RemoveBgProvider(removebg_key)
            if not self.default_provider:
                self.default_provider = 'remove_bg'
        
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            self.providers['gemini'] = GeminiBackgroundRemoval(gemini_key)
            if not self.default_provider:
                self.default_provider = 'gemini'
        
        banana_key = os.getenv('BANANA_API_KEY')
        if banana_key:
            self.providers['banana'] = BananaBackgroundRemoval(banana_key)
            if not self.default_provider:
                self.default_provider = 'banana'
        
        # Set default from environment or first available
        env_provider = os.getenv('BG_REMOVAL_PROVIDER', 'auto')
        if env_provider != 'auto' and env_provider in self.providers:
            self.default_provider = env_provider
    
    def _calculate_image_hash(self, image_path: str) -> str:
        """Calculate SHA256 hash of image file"""
        sha256_hash = hashlib.sha256()
        with open(image_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _check_cache(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """Check if processed image exists in cache"""
        cached = self.cache_collection.find_one({"image_hash": image_hash})
        return cached
    
    def _save_to_cache(self, image_hash: str, processed_path: str, metadata: Dict[str, Any]):
        """Save processed image metadata to cache"""
        cache_entry = {
            "image_hash": image_hash,
            "processed_path": processed_path,
            "metadata": metadata,
            "cached_at": datetime.now(timezone.utc)
        }
        self.cache_collection.update_one(
            {"image_hash": image_hash},
            {"$set": cache_entry},
            upsert=True
        )
    
    def remove_background(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        provider: Optional[str] = None,
        use_cache: bool = True
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Remove background from image.
        
        Args:
            image_path: Path to input image
            output_path: Optional path for output (auto-generated if None)
            provider: Provider to use ('gemini', 'banana', or None for default)
            use_cache: Whether to use cached results
            
        Returns:
            Tuple of (output_path, metadata_dict)
        """
        # Check cache if enabled
        if use_cache:
            image_hash = self._calculate_image_hash(image_path)
            cached = self._check_cache(image_hash)
            if cached and os.path.exists(cached['processed_path']):
                print(f"✅ Using cached processed image")
                return cached['processed_path'], {**cached['metadata'], 'from_cache': True}
        
        # Select provider
        provider_name = provider or self.default_provider
        if not provider_name or provider_name not in self.providers:
            return None, {
                'status': 'error',
                'error': f'No provider available. Requested: {provider_name}, Available: {list(self.providers.keys())}'
            }
        
        selected_provider = self.providers[provider_name]
        print(f"🎨 Processing with {provider_name} (estimated cost: ${selected_provider.get_cost_estimate():.4f})")
        
        # Process image
        processed_data, metadata = selected_provider.remove_background(image_path)
        
        if processed_data is None:
            return None, metadata
        
        # Generate output path if not provided
        if output_path is None:
            input_path = Path(image_path)
            output_path = str(input_path.parent / f"{input_path.stem}_no_bg.png")
        
        # Save processed image
        with open(output_path, 'wb') as f:
            f.write(processed_data)
        
        print(f"✅ Background removed: {output_path}")
        
        # Cache result
        if use_cache:
            self._save_to_cache(image_hash, output_path, metadata)
        
        return output_path, metadata
    
    def get_available_providers(self) -> list[str]:
        """Return list of available provider names"""
        return list(self.providers.keys())
    
    def get_provider_info(self) -> Dict[str, Dict[str, Any]]:
        """Return info about all available providers"""
        return {
            name: {
                'cost_estimate': provider.get_cost_estimate(),
                'is_default': name == self.default_provider
            }
            for name, provider in self.providers.items()
        }


if __name__ == "__main__":
    # CLI test interface
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python bg_removal_service.py <image_path> [provider]")
        print(f"\nAvailable providers: gemini, banana")
        print(f"\nRequired environment variables:")
        print(f"  GEMINI_API_KEY - For Gemini provider")
        print(f"  BANANA_API_KEY - For Banana provider")
        sys.exit(1)
    
    service = BackgroundRemovalService()
    
    print(f"Available providers: {service.get_available_providers()}")
    print(f"Provider info: {json.dumps(service.get_provider_info(), indent=2)}")
    
    image_path = sys.argv[1]
    provider = sys.argv[2] if len(sys.argv) > 2 else None
    
    output_path, metadata = service.remove_background(image_path, provider=provider)
    
    if output_path:
        print(f"\n✅ Success!")
        print(f"   Output: {output_path}")
        print(f"   Metadata: {json.dumps(metadata, indent=2, default=str)}")
    else:
        print(f"\n❌ Failed!")
        print(f"   Error: {json.dumps(metadata, indent=2, default=str)}")
