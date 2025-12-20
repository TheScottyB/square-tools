#!/usr/bin/env python3
"""
Quick test script for background removal service
"""

import os
import sys

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    try:
        import PIL
        print("  ✅ PIL (Pillow) installed")
    except ImportError:
        print("  ❌ PIL missing - run: pip3 install Pillow")
        return False
    
    try:
        import pymongo
        print("  ✅ pymongo installed")
    except ImportError:
        print("  ❌ pymongo missing - run: pip3 install pymongo")
        return False
    
    try:
        import requests
        print("  ✅ requests installed")
    except ImportError:
        print("  ❌ requests missing - run: pip3 install requests")
        return False
    
    return True

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("\n🧪 Testing MongoDB connection...")
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.server_info()
        print("  ✅ MongoDB connected")
        return True
    except Exception as e:
        print(f"  ❌ MongoDB connection failed: {e}")
        print("  💡 Run: brew services start mongodb-community@8.0")
        return False

def test_api_keys():
    """Check if API keys are configured"""
    print("\n🧪 Checking API keys...")
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    banana_key = os.getenv('BANANA_API_KEY')
    square_token = os.getenv('SQUARE_TOKEN')
    
    if gemini_key:
        print(f"  ✅ GEMINI_API_KEY set ({gemini_key[:10]}...)")
    else:
        print("  ⚠️  GEMINI_API_KEY not set")
    
    if banana_key:
        print(f"  ✅ BANANA_API_KEY set ({banana_key[:10]}...)")
    else:
        print("  ⚠️  BANANA_API_KEY not set")
    
    if square_token:
        print(f"  ✅ SQUARE_TOKEN set ({square_token[:10]}...)")
    else:
        print("  ⚠️  SQUARE_TOKEN not set (required for upload)")
    
    if not gemini_key and not banana_key:
        print("\n  ❌ No background removal provider configured!")
        print("  💡 Set at least one: export GEMINI_API_KEY='your_key'")
        return False
    
    return True

def test_service_initialization():
    """Test that BackgroundRemovalService can be initialized"""
    print("\n🧪 Testing service initialization...")
    try:
        from bg_removal_service import BackgroundRemovalService
        service = BackgroundRemovalService()
        
        providers = service.get_available_providers()
        print(f"  ✅ Service initialized")
        print(f"  Available providers: {providers}")
        
        if not providers:
            print("  ⚠️  No providers available - check API keys")
            return False
        
        info = service.get_provider_info()
        for name, data in info.items():
            print(f"    - {name}: ${data['cost_estimate']:.4f} per image" +
                  (" [DEFAULT]" if data['is_default'] else ""))
        
        return True
    except Exception as e:
        print(f"  ❌ Service initialization failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Background Removal Service - System Check")
    print("=" * 60)
    
    results = []
    
    results.append(("Dependencies", test_imports()))
    results.append(("MongoDB", test_mongodb_connection()))
    results.append(("API Keys", test_api_keys()))
    results.append(("Service Init", test_service_initialization()))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed! System ready for background removal.")
        print("\n💡 Try: process_and_upload.sh 27569 --remove-bg --skip-upload")
        return 0
    else:
        print("\n⚠️  Some tests failed. Fix issues above before using the system.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
