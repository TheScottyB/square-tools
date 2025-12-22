# Demo: Automated Background Removal System

## 🎉 System Status: READY

All components are installed and configured:
- ✅ Remove.bg API configured (primary provider)
- ✅ Gemini API configured (secondary + chat)
- ✅ MongoDB running
- ✅ Python dependencies installed

## Quick Tests

### 1. Test Background Removal Service Directly

```bash
# Set API keys
export REMOVEBG_API_KEY=""
export GEMINI_API_KEY=""

# Test with Remove.bg
cd ~/square-tools
python3 cache-system/bg_removal_service.py ~/tmp/square_upload/image000000.jpeg remove_bg

# Result: Creates image000000_no_bg.png with transparent background
```

### 2. Chat with Gemini (Text)

```bash
# Interactive text chat with Gemini Flash
export GEMINI_API_KEY=""
gemini_chat.sh flash

# Try prompts like:
# - "explain how background removal works"
# - "what's the best way to prepare product photos for ecommerce?"
# - "help me write a script to process 100 images"
```

### 3. Chat with Gemini About Images

```bash
# Analyze an 
export GEMINI_API_KEY=""
gemini_chat.sh flash ~/tmp/square_upload/image000000.jpeg

# It will describe the image, then you can ask:
# - "what would this look like with no background?"
# - "describe the lighting and composition"
# - "suggest improvements for this product photo"
```

### 4. System Health Check

```bash
cd ~/square-tools
python3 cache-system/test_bg_removal.py
```

Expected output:
```
🎉 All tests passed! System ready for background removal.

Available providers: ['remove_bg', 'gemini']
  - remove_bg: $0.0020 per image [DEFAULT]
  - gemini: $0.0020 per image
```

## Pricing Comparison

| Provider | Cost per Image | Best For | Speed |
|----------|---------------|----------|-------|
| **Remove.bg** | $0.002 | Production, bulk | 2-3s |
| **Gemini** | $0.002-0.039 | Testing, chat | 3-5s |
| **Banana** | $0.005 | Serverless GPU | 2-4s |

**Note**: Remove.bg free tier includes 50 images/month

## Available Commands

```bash
# Background removal service (Python)
python3 cache-system/bg_removal_service.py <image> [provider]

# Gemini chat (interactive)
gemini_chat.sh [model] [image]
  Models: flash, pro, 2.0, exp

# System test
python3 cache-system/test_bg_removal.py

# Process and upload (full workflow)
process_and_upload.sh <photo_num> --remove-bg [--preview] [--skip-upload]
```

## Example Workflow

### Remove Background and Upload to Square

```bash
# 1. Set environment
export REMOVEBG_API_KEY="aDuPi7tnoSM6RaHUnDHkHSNe"
export SQUARE_TOKEN="your_square_token"

# 2. Process image with background removal and preview
process_and_upload.sh 27569 --remove-bg --preview

# 3. Review the preview, confirm upload
# Image is uploaded to Square catalog
```

### Batch Process Multiple Images

```bash
# Process images 27500-27510 with background removal
for i in {27500..27510}; do
  echo "Processing photo $i..."
  process_and_upload.sh $i --remove-bg --skip-upload
  sleep 1  # Respect rate limits
done

# Results saved in ~/tmp/square_processed/
```

### Test Gemini Image Understanding

```bash
# Export a photo
photos_to_square.sh 27569 --export-only

# Chat with Gemini about it
gemini_chat.sh flash ~/tmp/square_upload/latest.jpeg
```

## MongoDB Queries

### Check Processing Cache

```bash
# View processed images
mongosh square_cache --eval "db.bg_removal_cache.find().pretty()"

# Count processed images
mongosh square_cache --eval "db.bg_removal_cache.countDocuments()"

# Calculate total cost
mongosh square_cache --eval "
  db.bg_removal_cache.aggregate([
    { \$group: { 
      _id: '\$metadata.provider', 
      total_cost: { \$sum: '\$metadata.cost' },
      count: { \$sum: 1 }
    }}
  ])
"
```

## Troubleshooting

### "No provider available"
```bash
echo $REMOVEBG_API_KEY  # Check if set
export REMOVEBG_API_KEY="aDuPi7tnoSM6RaHUnDHkHSNe"
```

### Python string errors
Use the Python interface directly instead of the shell wrapper:
```bash
python3 cache-system/bg_removal_service.py image.jpg remove_bg
```

### Rate limits
Add delays between batch operations:
```bash
for i in {1..10}; do
  python3 cache-system/bg_removal_service.py image$i.jpg
  sleep 2
done
```

## Next Steps

1. ✅ Test background removal: `python3 cache-system/bg_removal_service.py ~/tmp/square_upload/image000000.jpeg`
2. ✅ Chat with Gemini: `gemini_chat.sh flash`
3. ✅ Process a photo: `process_and_upload.sh 27569 --remove-bg --skip-upload`
4. 📖 Read full docs: `IMAGE_PROCESSING.md`
5. 🔍 Track progress: [Linear TVM-27](https://linear.app/tvm-brands/issue/TVM-27)

## Files Reference

- **bg_removal_service.py** - Core background removal service
- **gemini_chat.sh** - Interactive Gemini chat interface  
- **process_and_upload.sh** - Complete photo → Square workflow
- **test_bg_removal.py** - System health check
- **IMAGE_PROCESSING.md** - Complete documentation
- **QUICKSTART_BG_REMOVAL.md** - Quick start guide
