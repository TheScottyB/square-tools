# Square Items MongoDB Cache System

A comprehensive caching and change tracking system for Square catalog items using MongoDB.

## 🏗️ System Overview

This system provides:
- **Local MongoDB cache** of all Square catalog items
- **Change detection** with before/after snapshots
- **Audit trail** of all modifications
- **AI-powered image processing** with automated background removal
- **CLI tools** for easy management
- **Photo integration** from Photos Library to Square
- **Gemini AI chat** for image analysis and assistance

## 📁 Project Structure

```
~/Workspace/square-tools/
├── bin/
│   ├── square_cache.sh           # CLI wrapper for cache operations
│   ├── photos_to_square.sh       # Photos Library → Square uploader
│   ├── process_and_upload.sh     # AI-powered photo processing + upload
│   ├── gemini_chat.sh           # Interactive Gemini chat interface
│   └── browse_photos.sh          # Photos Library browser
├── cache-system/
│   ├── square_cache_manager.py   # Core MongoDB cache manager
│   ├── bg_removal_service.py     # Background removal service (Remove.bg, Gemini, Banana)
│   ├── test_bg_removal.py        # System health checker
│   └── demo_change_tracking.sh   # Demonstration script
├── data/
│   ├── photo_exports/            # Exported photos directory
│   └── logs/                     # Application logs
├── config.sh                     # Configuration file
├── IMAGE_PROCESSING.md           # Image processing documentation
├── QUICKSTART_BG_REMOVAL.md      # Quick start guide
├── DEMO.md                       # Quick demos and examples
└── README.md                     # This documentation
```

## 🗄️ MongoDB Database Schema

### Database: `square_cache`

#### Collections:

1. **`catalog_items`** - Cached Square catalog items
   ```json
   {
     "_id": "ObjectId",
     "id": "ANE5SXKQR4JZ6AYEZDO26IMX",
     "type": "ITEM", 
     "version": 1759194139169,
     "item_data": {
       "name": "Trading Places - Rare Video 8 Format (1983)",
       "image_ids": ["ZDHVCXFYL7MNUQV6TAQTXH4G", "..."],
       ...
     },
     "content_hash": "620e6650a2732e5a...",
     "cached_at": "2025-09-30T02:31:13.439Z"
   }
   ```

2. **`change_snapshots`** - Before/after change tracking
   ```json
   {
     "_id": "ObjectId",
     "item_id": "ANE5SXKQR4JZ6AYEZDO26IMX",
     "item_name": "Trading Places - Rare Video 8 Format (1983)",
     "change_type": "update",
     "timestamp": "2025-09-30T02:35:00.000Z",
     "before_data": { /* complete item before change */ },
     "after_data": { /* complete item after change */ },
     "differences": {
       "item_data.image_ids": {
         "before": null,
         "after": ["ZDHVCXFYL7MNUQV6TAQTXH4G", "JUOA5BTTKGJOXWHJ62RR4I62"]
       }
     },
     "square_version_before": 1759194139169,
     "square_version_after": 1759194200000
   }
   ```

3. **`sync_log`** - Sync operation history
   ```json
   {
     "_id": "ObjectId", 
     "timestamp": "2025-09-30T02:31:12.920Z",
     "total_items": 31,
     "created_count": 31,
     "updated_count": 0,
     "changes_detected": 31,
     "duration_seconds": 0.532
   }
   ```

4. **`bg_removal_cache`** - Processed image cache (AI background removal)
   ```json
   {
     "_id": "ObjectId",
     "image_hash": "sha256_hash_of_original",
     "processed_path": "/path/to/processed_image.png",
     "metadata": {
       "provider": "remove_bg",
       "status": "success",
       "cost": 0.002,
       "timestamp": "2025-12-20T03:22:00Z",
       "original_size": 1024000,
       "processed_size": 512000
     },
     "cached_at": "2025-12-20T03:22:00Z"
   }
   ```

## 🚀 Quick Start

### Runtime Policy Note

Privileged operations are gated by runtime policy:

- `runtime/capability_matrix.json`
- `runtime/operation_policy.json`
- `bin/agent_preflight.sh`

Example:

```bash
bin/agent_preflight.sh --operation square_cache_sync --runtime "${SQUARE_RUNTIME_ID:-local_cli}"
```

### 1. Prerequisites

```bash
# Install MongoDB
brew tap mongodb/brew
brew install mongodb-community@8.0
brew services start mongodb-community@8.0

# Install Python dependencies
pip3 install pymongo requests Pillow
```

### 2. Set Environment Variables

```bash
# Required for Square API
export SQUARE_TOKEN="YOUR_SQUARE_TOKEN_HERE"

# Optional: For AI background removal (at least one recommended)
export REMOVEBG_API_KEY="your_remove_bg_api_key"  # Recommended
export GEMINI_API_KEY="your_gemini_api_key"        # For chat & image analysis
```

### 2.5 Security Gate

Run secret scanning before commit/release:

```bash
./bin/secret_scan.sh
```

### 3. Initial Setup

```bash
# Load configuration (creates directories)
source ~/Workspace/square-tools/config.sh

# Check system status
square_cache.sh status

# Perform initial sync (creates baseline cache)
square_cache.sh sync

# View all changes
square_cache.sh changes
```

## 📝 CLI Commands

### Cache Management

```bash
# Sync all items from Square to MongoDB cache
square_cache.sh sync

# Show recent changes
square_cache.sh changes
square_cache.sh changes --since 2025-09-30

# Generate detailed change report
square_cache.sh report
square_cache.sh report --output json

# Search cached items
square_cache.sh search "Trading Places"

# Get specific item details
square_cache.sh item ANE5SXKQR4JZ6AYEZDO26IMX

# Check system status
square_cache.sh status
```

### Photo Management

```bash
# Browse Photos Library
browse_photos.sh recent 10
browse_photos.sh search "IMG_7232"
browse_photos.sh random 5
browse_photos.sh export 27569

# Upload photos to Square (basic)
photos_to_square.sh 27569 "YOUR_SQUARE_TOKEN"

# Process with AI background removal and upload
process_and_upload.sh 27569 --remove-bg --preview
process_and_upload.sh 27569 --remove-bg --skip-upload
process_and_upload.sh 27569 --remove-bg --provider remove_bg
```

### AI Image Processing

```bash
# Remove background from image (Python interface)
python3 cache-system/bg_removal_service.py image.jpg remove_bg

# Chat with Gemini about text
gemini_chat.sh flash

# Chat with Gemini about an image
gemini_chat.sh flash image.jpg

# Test system health
python3 cache-system/test_bg_removal.py
```

### Demo & Testing

```bash
# Run change tracking demonstration
~/Workspace/square-tools/cache-system/demo_change_tracking.sh
```

## 🔄 Change Detection Process

### 1. Content Hashing
- Each item gets a SHA256 hash of its content (excluding volatile fields like `updated_at`, `version`)
- Changes detected by comparing hashes between Square API and cached versions

### 2. Before/After Snapshots
- **BEFORE**: Complete item data from MongoDB cache
- **AFTER**: Complete item data from Square API
- **DIFFERENCES**: Field-by-field comparison showing exactly what changed

### 3. Change Types
- **`create`**: New item added to Square catalog
- **`update`**: Existing item modified (with detailed diff)
- **`delete`**: Item removed from Square catalog (planned feature)

## 📊 Real-World Example

### Before State (Trading Places Item):
```json
{
  "name": "Trading Places - Rare Video 8 Format (1983)",
  "version": 1759194139169,
  "item_data": {
    // NO image_ids field - item has no images
  }
}
```

### After State (Images Attached):
```json
{
  "name": "Trading Places - Rare Video 8 Format (1983)", 
  "version": 1759194200000,
  "item_data": {
    "image_ids": [
      "ZDHVCXFYL7MNUQV6TAQTXH4G",  // 1A2E186B-A015-4A86-84B6-C1F76EC9810D.jpeg
      "JUOA5BTTKGJOXWHJ62RR4I62"   // 5748D4B2-F1DC-4BB6-84E4-90B56DCA4059.jpeg
    ]
  }
}
```

### Change Detection Output:
```
🔄 Trading Places - Rare Video 8 Format (1983)
   Type: update
   Changes: item_data.image_ids, version, updated_at
   Version: 1759194139169 → 1759194200000
   
   BEFORE: No images attached
   AFTER:  2 images attached
```

## 🎯 Use Cases

### 1. Audit Trail
- Track all changes to your Square catalog
- See who changed what and when
- Compliance and business intelligence

### 2. Content Management
- Backup/restore item configurations  
- Bulk operations planning
- A/B testing tracking

### 3. Integration Monitoring
- Detect unauthorized changes
- Monitor third-party integrations
- Quality assurance workflows

### 4. Analytics
- Track catalog growth over time
- Monitor pricing changes
- Image attachment patterns

## 🧪 Testing & Validation

### Current System State
- ✅ **31 items cached** from Square catalog
- ✅ **All items have baseline snapshots** (before state)
- ✅ **Trading Places item cached** with NO images (perfect test case)
- ✅ **2 images uploaded** to Square catalog ready for attachment
- ✅ **Change detection ready** to track image attachment

### Test Workflow
1. **Baseline established**: All items cached with current state
2. **Make changes**: Attach images via Square Dashboard or API
3. **Sync & detect**: `./square_cache.sh sync` will detect changes
4. **View changes**: `./square_cache.sh changes` shows before/after

## 🔧 Technical Details

### Change Detection Algorithm
```python
def _detect_changes(self, square_item: Dict) -> Optional[ChangeSnapshot]:
    item_id = square_item['id']
    cached_item = self.items_collection.find_one({"id": item_id})
    
    if not cached_item:
        return ChangeSnapshot(change_type='create', ...)
    
    square_hash = self._calculate_hash(square_item)
    cached_hash = cached_item.get('content_hash', '')
    
    if square_hash != cached_hash:
        differences = self._find_differences(cached_item, square_item)
        return ChangeSnapshot(change_type='update', differences=differences, ...)
    
    return None
```

### Performance Optimizations
- **MongoDB indexes** on key fields (id, timestamp, item_name)
- **Content hashing** for efficient change detection
- **Cursor-based pagination** for large catalogs
- **Batch operations** for bulk changes

### Error Handling
- **Connection retry logic** for MongoDB and Square API
- **Partial sync recovery** if operations fail
- **Comprehensive logging** of all operations
- **Data validation** before cache updates

## 🎉 Success Metrics

The system successfully provides:

1. **Complete catalog cache**: All 31 Square items cached locally in MongoDB
2. **Change tracking**: Before/after snapshots for all modifications  
3. **Audit trail**: Complete history of when and what changed
4. **CLI tools**: Easy-to-use command-line interface
5. **Photo integration**: Direct upload from macOS Photos Library
6. **Real-time sync**: Detect changes on-demand or scheduled
7. **Detailed reporting**: JSON and human-readable change reports

This creates a robust foundation for Square catalog management, change tracking, and business intelligence.

---

## 🚀 Next Steps

To see the change tracking in action:

1. **Attach the uploaded images** to Trading Places item in Square Dashboard
2. **Run sync**: `./square_cache.sh sync` 
3. **View changes**: `./square_cache.sh changes --since 2025-09-30`
4. **Generate report**: `./square_cache.sh report`

The system will detect and document the exact changes made, creating a complete before/after snapshot for audit and analysis purposes.
