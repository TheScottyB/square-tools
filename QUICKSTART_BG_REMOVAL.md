# Quick Start: Background Removal

Get started with automated background removal in 5 minutes.

## ✅ System Status

Your system is ready! Dependencies installed:
- ✅ Python 3 with Pillow, pymongo, requests
- ✅ MongoDB running
- ✅ Square token configured

**Next step**: Configure background removal API keys

## 1. Get API Keys

### Option A: Gemini API (Recommended)

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key

### Option B: Banana API

1. Visit [Banana.dev](https://banana.dev)
2. Sign up and get your API key
3. Deploy a background removal model
4. Get your model key

## 2. Configure Environment

Add to your shell config (`~/.zshrc`):

```bash
# Background removal APIs
export GEMINI_API_KEY="your_gemini_key_here"
# OR
export BANANA_API_KEY="your_banana_key_here"
export BANANA_MODEL_KEY="your_model_key_here"

# Already configured
export SQUARE_TOKEN="your_square_token"
```

Then reload:
```bash
source ~/.zshrc
```

## 3. Test the System

```bash
# Run system check
cd ~/square-tools
python3 cache-system/test_bg_removal.py
```

Expected output when ready:
```
🎉 All tests passed! System ready for background removal.
```

## 4. Process Your First Image

### Test without uploading:
```bash
process_and_upload.sh 27569 --remove-bg --skip-upload
```

### With preview before upload:
```bash
process_and_upload.sh 27569 --remove-bg --preview
```

### Full workflow:
```bash
process_and_upload.sh 27569 --remove-bg
```

## Common Commands

```bash
# Test Gemini provider
process_and_upload.sh 27569 --remove-bg --provider gemini --skip-upload

# Process and preview
process_and_upload.sh 27569 --remove-bg --preview

# See all options
process_and_upload.sh --help
```

## Files Created

Your new files:
- `cache-system/bg_removal_service.py` - Core service
- `bin/process_and_upload.sh` - Enhanced CLI
- `cache-system/test_bg_removal.py` - System test
- `IMAGE_PROCESSING.md` - Full documentation
- `QUICKSTART_BG_REMOVAL.md` - This guide

## Cost Estimates

- **Gemini**: ~$0.002 per image (~500 images per $1)
- **Banana**: ~$0.005 per image (~200 images per $1)
- **Caching**: Free for repeated images

## Troubleshooting

### "No provider available"
```bash
# Check if keys are set
echo $GEMINI_API_KEY

# Set the key
export GEMINI_API_KEY="your_key_here"
```

### MongoDB not running
```bash
brew services start mongodb-community@8.0
```

### Dependencies missing
```bash
pip3 install Pillow pymongo requests
```

## Next Steps

1. ✅ Set API key (see step 2)
2. ✅ Run test (step 3)
3. ✅ Process first image (step 4)
4. 📖 Read [IMAGE_PROCESSING.md](IMAGE_PROCESSING.md) for advanced features
5. 🔍 Track progress at [Linear TVM-27](https://linear.app/tvm-brands/issue/TVM-27)

## Getting Help

- Full docs: `IMAGE_PROCESSING.md`
- System architecture: `WARP.md`
- Linear issue: TVM-27
- Test system: `python3 cache-system/test_bg_removal.py`
