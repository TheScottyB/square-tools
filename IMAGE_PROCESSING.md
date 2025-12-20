# Automated Image Processing with Background Removal

AI-powered image processing pipeline for Square catalog photos with automated background removal using Gemini and Banana APIs.

## Quick Start

### 1. Install Dependencies

```bash
pip3 install Pillow pymongo requests
```

### 2. Set API Keys

```bash
# For Gemini API (recommended)
export GEMINI_API_KEY="your_gemini_api_key_here"

# For Banana API (optional alternative)
export BANANA_API_KEY="your_banana_api_key_here"
export BANANA_MODEL_KEY="your_model_key_here"  # if using custom model

# Square token (for upload)
export SQUARE_TOKEN="your_square_access_token"
```

### 3. Process and Upload a Photo

```bash
# With background removal and preview
process_and_upload.sh 27569 --remove-bg --preview

# Process only, skip upload (for testing)
process_and_upload.sh 27569 --remove-bg --skip-upload

# Use specific provider
process_and_upload.sh 27569 --remove-bg --provider gemini
```

## Features

### Background Removal Providers

#### Gemini Vision API (Recommended)
- **Cost**: ~$0.002 per image
- **Quality**: Excellent edge detection and transparency
- **Speed**: 3-5 seconds per image
- **Rate Limits**: 60 requests/minute (free tier)
- **Setup**: Requires `GEMINI_API_KEY`

#### Banana API (Alternative)
- **Cost**: ~$0.001-0.005 per image
- **Quality**: Good for batch processing
- **Speed**: 2-4 seconds per image
- **Rate Limits**: Based on plan
- **Setup**: Requires `BANANA_API_KEY` and `BANANA_MODEL_KEY`

### Intelligent Caching

The system automatically caches processed images in MongoDB to avoid duplicate processing:
- Same image hash = instant retrieval from cache
- Significant cost savings for repeated processing
- Cache stored in `bg_removal_cache` collection

### Format Conversion

Automatically handles:
- HEIC → PNG with transparency
- JPEG → PNG with transparency  
- Preserves original images
- Optimized file sizes

## Usage Examples

### Single Image Processing

```bash
# Process with background removal
process_and_upload.sh 27569 --remove-bg

# Process, preview, then upload
process_and_upload.sh 27569 --remove-bg --preview

# Process without using cache
process_and_upload.sh 27569 --remove-bg --no-cache
```

### Testing Providers

```bash
# Test Gemini provider
process_and_upload.sh 27569 --remove-bg --provider gemini --skip-upload

# Test Banana provider
process_and_upload.sh 27569 --remove-bg --provider banana --skip-upload
```

### Direct Python Interface

```bash
# Test background removal service directly
python3 cache-system/bg_removal_service.py ~/tmp/square_upload/photo.jpg gemini
```

## Directory Structure

```
square-tools/
├── cache-system/
│   ├── bg_removal_service.py      # Background removal service
│   └── square_cache_manager.py    # Existing cache manager
├── bin/
│   ├── process_and_upload.sh      # Enhanced workflow with BG removal
│   └── photos_to_square.sh        # Original workflow (no processing)
└── tmp/
    ├── square_upload/              # Exported photos
    └── square_processed/           # Processed images with BG removed
```

## API Configuration

### Gemini API Setup

1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set environment variable:
   ```bash
   export GEMINI_API_KEY="your_key_here"
   ```
3. Test connection:
   ```bash
   curl -H "Content-Type: application/json" \
        "https://generativelanguage.googleapis.com/v1beta/models?key=$GEMINI_API_KEY"
   ```

### Banana API Setup

1. Sign up at [Banana.dev](https://banana.dev)
2. Get your API key and model key from dashboard
3. Set environment variables:
   ```bash
   export BANANA_API_KEY="your_api_key_here"
   export BANANA_MODEL_KEY="your_model_key_here"
   ```

## MongoDB Collections

### `bg_removal_cache`

Stores processed image metadata and paths:

```javascript
{
  image_hash: "sha256_hash_of_original",
  processed_path: "/path/to/processed_image.png",
  metadata: {
    provider: "gemini",
    status: "success",
    cost: 0.002,
    timestamp: "2025-12-20T03:22:00Z",
    original_size: 1024000,
    processed_size: 512000
  },
  cached_at: ISODate("2025-12-20T03:22:00Z")
}
```

## Cost Tracking

Track processing costs:

```bash
# View cache statistics
mongosh square_cache --eval "db.bg_removal_cache.aggregate([
  { \$group: { 
    _id: '\$metadata.provider', 
    total_cost: { \$sum: '\$metadata.cost' },
    count: { \$sum: 1 }
  }}
])"

# Total images processed
mongosh square_cache --eval "db.bg_removal_cache.countDocuments()"
```

## Troubleshooting

### "No provider available" Error

**Problem**: No API keys configured

**Solution**:
```bash
# Check if keys are set
echo $GEMINI_API_KEY
echo $BANANA_API_KEY

# Set at least one provider
export GEMINI_API_KEY="your_key_here"
```

### "PIL module not found" Error

**Problem**: Pillow not installed

**Solution**:
```bash
pip3 install Pillow
```

### Background Removal Quality Issues

**Problem**: Poor edge detection or artifacts

**Solutions**:
1. Try different provider: `--provider gemini` or `--provider banana`
2. Use higher quality source images
3. Check image contrast and lighting
4. Preview before upload: `--preview`

### Rate Limit Errors

**Problem**: API rate limits exceeded

**Solution**:
```bash
# Use cache to avoid reprocessing
process_and_upload.sh 27569 --remove-bg  # uses cache by default

# For Gemini free tier: max 60 requests/minute
# Add delays between batch processing
```

### MongoDB Connection Issues

**Problem**: Cannot connect to MongoDB

**Solution**:
```bash
# Start MongoDB
brew services start mongodb-community@8.0

# Check MongoDB status
brew services list | grep mongodb

# Test connection
mongosh --eval "db.runCommand('ping')"
```

## Performance Metrics

Typical performance (single image):
- **Export from Photos**: 1-2 seconds
- **Background removal**: 3-5 seconds
- **Upload to Square**: 2-3 seconds
- **Total workflow**: 6-10 seconds per image

With caching:
- **Cached retrieval**: < 1 second
- **Total workflow**: 3-5 seconds per image

## Environment Variables Reference

```bash
# Required for upload
export SQUARE_TOKEN="your_square_access_token"

# Required for background removal (at least one)
export GEMINI_API_KEY="your_gemini_api_key"
export BANANA_API_KEY="your_banana_api_key"

# Optional configuration
export BANANA_MODEL_KEY="your_model_key"           # For custom Banana models
export BG_REMOVAL_PROVIDER="gemini"                # Default provider (gemini/banana/auto)
export EXPORT_DIR="$HOME/tmp/square_upload"        # Photo export directory
export PROCESSED_DIR="$HOME/tmp/square_processed"  # Processed images directory
```

## Next Steps

### Batch Processing (Coming Soon)

Process multiple images in queue:
```bash
# Add images to processing queue
image_queue.sh add 27569 27570 27571

# Process entire queue
image_queue.sh process --provider auto

# Monitor queue status
image_queue.sh status
```

### Quality Validation (Coming Soon)

Automatic quality scoring:
- Edge detection scores
- Transparency validation
- Manual review queue for low scores

## Support

For issues or questions:
1. Check this documentation
2. Review Linear issue TVM-27
3. Check MongoDB logs: `~/square-tools/logs/`
4. Test providers individually with Python interface

## Related Documentation

- [Main WARP.md](WARP.md) - System architecture overview
- [Linear TVM-27](https://linear.app/tvm-brands/issue/TVM-27) - Implementation tracking
- [Gemini API Docs](https://ai.google.dev/docs)
- [Banana API Docs](https://docs.banana.dev)
