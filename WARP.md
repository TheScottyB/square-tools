# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## System Architecture

This is a Square catalog management system built with Python/Bash and MongoDB that provides:

- **Comprehensive caching layer**: Local MongoDB cache of all Square catalog items with change detection
- **Audit trail system**: Before/after snapshots of all item modifications with detailed diffs  
- **Photo integration pipeline**: Direct upload from macOS Photos Library to Square catalog
- **CLI management tools**: Shell scripts for cache operations, photo management, and reporting

### Core Components

1. **square_cache_manager.py** - Python class managing MongoDB operations, Square API sync, and change detection
2. **square_cache.sh** - CLI wrapper providing commands for sync, changes, reports, search, and status
3. **photos_to_square.sh** - Photo export from macOS Photos Library and upload to Square catalog
4. **browse_photos.sh** - Photos Library browser with search, export, and info capabilities

### Data Flow Architecture

```
Square API ──→ Change Detection ──→ MongoDB Cache
     ↓               ↓                    ↓
   Sync Log    Change Snapshots    Cached Items
     
macOS Photos ──→ Export ──→ Square Upload ──→ Item Association
```

### MongoDB Collections

- **`catalog_items`**: Full Square item cache with content hashing for change detection
- **`change_snapshots`**: Before/after snapshots with field-level differences tracking  
- **`sync_log`**: Sync operation history with performance metrics and error tracking

## Setup

### Initial Setup

```bash
# Install MongoDB and Python dependencies
brew tap mongodb/brew
brew install mongodb-community@8.0
brew services start mongodb-community@8.0
pip3 install pymongo requests

# Set required environment variable
export SQUARE_TOKEN="your_square_access_token_here"

# Load configuration (creates necessary directories)
source ~/square-tools/config.sh

# Add bin/ to PATH for easier command access
export PATH="$HOME/square-tools/bin:$PATH"

# Verify setup
square_cache.sh status

# Perform initial sync to establish baseline cache
square_cache.sh sync
```

## Development Commands

### Cache Management

```bash
# Check system status and cache statistics
square_cache.sh status

# Perform full sync from Square API to MongoDB
square_cache.sh sync

# View recent changes with detailed diffs
square_cache.sh changes
square_cache.sh changes --since 2025-09-30

# Generate comprehensive change report
square_cache.sh report
square_cache.sh report --output json

# Search cached items by name pattern
square_cache.sh search "Trading Places"

# Get specific cached item details
square_cache.sh item ANE5SXKQR4JZ6AYEZDO26IMX
```

### Photo Management Workflow

```bash
# Browse Photos Library (27,569 total photos)
browse_photos.sh recent 10
browse_photos.sh search "IMG_7232" 
browse_photos.sh random 5
browse_photos.sh info 27569
browse_photos.sh export 27569

# Upload photo from library to Square
photos_to_square.sh 27569 $SQUARE_TOKEN
```

### Testing and Demo

```bash
# Run change tracking demonstration
~/square-tools/cache-system/demo_change_tracking.sh
```

### Direct MongoDB Queries

```bash
# Access MongoDB shell for the square_cache database
mongosh square_cache

# Count total cached items
mongosh square_cache --eval "db.catalog_items.countDocuments()"

# View latest sync operation
mongosh square_cache --eval "db.sync_log.findOne({}, {sort: {timestamp: -1}})"

# View all changes for a specific item
mongosh square_cache --eval "db.change_snapshots.find({item_id: 'ANE5SXKQR4JZ6AYEZDO26IMX'}).pretty()"

# View recent changes in the last 24 hours
mongosh square_cache --eval "db.change_snapshots.find({timestamp: {\$gte: new Date(Date.now() - 24*60*60*1000)}}).pretty()"

# Get items with images
mongosh square_cache --eval "db.catalog_items.find({'item_data.image_ids': {\$exists: true}}).count()"
```

## Technical Implementation Details

### Change Detection Algorithm

The system uses content hashing (SHA256) for efficient change detection:

1. **Content Hash Calculation**: Excludes volatile fields (`updated_at`, `version`) to focus on meaningful changes
2. **Diff Generation**: Field-by-field comparison identifying exactly what changed
3. **Snapshot Creation**: Complete before/after data preservation for audit trail
4. **Performance Optimization**: MongoDB indexes on key fields, cursor-based pagination for large catalogs

### Critical Files and Functions

- **`SquareCacheManager._detect_changes()`** - Core change detection logic comparing Square API data with cached versions
- **`SquareCacheManager._find_differences()`** - Field-level diff generation for tracking specific changes  
- **`SquareCacheManager.sync_from_square()`** - Main synchronization workflow with error handling and logging
- **`SquareCacheManager._calculate_hash()`** - Content hashing for change detection excluding volatile fields

### MongoDB Schema and Indexing Strategy

```python
# Performance indexes created automatically:
items_collection.create_index("id", unique=True)
items_collection.create_index("item_data.name") 
changes_collection.create_index(["item_id", "timestamp"])
sync_log_collection.create_index("timestamp")
```

### Photo Integration Implementation

Photos workflow uses AppleScript automation for macOS Photos Library access:
- **Export**: `osascript` commands to export specific photos by index number
- **Upload**: Square API v2 catalog/images endpoint with multipart form data
- **Association**: Image IDs can be attached to catalog items via `item_data.image_ids`

## Troubleshooting

### MongoDB Connection Issues

```bash
# Check if MongoDB is running
mongosh --eval "db.runCommand('ismaster')" --quiet

# Start MongoDB service
brew services start mongodb-community@8.0

# Check MongoDB service status
brew services list | grep mongodb

# View MongoDB logs
tail -f /opt/homebrew/var/log/mongodb/mongo.log  # Apple Silicon
tail -f /usr/local/var/log/mongodb/mongo.log      # Intel Mac
```

### Square API Issues

```bash
# Verify Square token is set
echo $SQUARE_TOKEN

# Test Square API connectivity (requires curl and jq)
curl -H "Square-Version: 2024-09-18" \
     -H "Authorization: Bearer $SQUARE_TOKEN" \
     "https://connect.squareup.com/v2/catalog/list?types=ITEM&limit=1"
```

### Cache Sync Problems

```bash
# Check recent sync logs for errors
mongosh square_cache --eval "db.sync_log.find({error: {\$exists: true}}).sort({timestamp: -1}).limit(5).pretty()"

# Clear cache and resync (nuclear option)
mongosh square_cache --eval "db.catalog_items.deleteMany({}); db.change_snapshots.deleteMany({}); db.sync_log.deleteMany({})"
square_cache.sh sync
```

### Photo Export Issues

```bash
# Verify Photos Library path
ls -la "$HOME/Pictures/Photos Library.photoslibrary"

# Check export directory
ls -la ~/square-tools/data/photo_exports/

# Test AppleScript access to Photos
osascript -e "tell application \"Photos\" to count media items"
```

## Environment Variables

```bash
# Required
export SQUARE_TOKEN="your_square_access_token_here"

# Optional (defaults provided in config.sh)
export SQUARE_ENVIRONMENT="production"  # or 'sandbox'
export MONGO_URI="mongodb://localhost:27017/"
export MONGO_DATABASE="square_cache"
export PHOTOS_LIBRARY_PATH="$HOME/Pictures/Photos Library.photoslibrary"
export SQUARE_LOG_LEVEL="INFO"
```

## Key Implementation Patterns

### Error Handling and Resilience

- **Connection retry logic** for MongoDB and Square API failures
- **Partial sync recovery** with detailed error logging to `sync_log` collection  
- **Data validation** before cache updates with comprehensive logging
- **Idempotent operations** supporting safe re-runs of sync processes

### Performance Considerations

- **Batch operations** for bulk MongoDB updates during sync
- **Content hashing** eliminates unnecessary API calls and database writes
- **Indexed queries** on frequently accessed fields (item_id, timestamp, name)
- **Cursor-based pagination** handles large Square catalogs efficiently

### Change Tracking Capabilities

The system tracks three change types with complete audit trails:
- **`create`**: New items added to Square catalog with full initial data
- **`update`**: Modifications to existing items with field-level diffs showing exactly what changed
- **`delete`**: Items removed from catalog (framework ready, not yet implemented)

Example change detection output:
```
🔄 Trading Places - Rare Video 8 Format (1983)
   Type: update
   Changes: item_data.image_ids, version, updated_at
   Version: 1759194139169 → 1759194200000
   BEFORE: No images attached  
   AFTER:  2 images attached
```

This comprehensive caching and change tracking system enables robust Square catalog management, detailed audit trails, and seamless photo integration workflows.