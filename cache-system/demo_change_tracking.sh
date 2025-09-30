#!/bin/bash

# Demo: Square Item Change Tracking with MongoDB Cache
# This demonstrates how the system tracks before/after snapshots when items change

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🎬 Square Item Change Tracking Demo"
echo "=================================="
echo ""

echo "📊 Current Cache Status:"
$HOME/square-tools/bin/square_cache.sh status

echo ""
echo "🔍 Current Trading Places Item (BEFORE state):"
echo "----------------------------------------------"
$HOME/square-tools/bin/square_cache.sh item ANE5SXKQR4JZ6AYEZDO26IMX
import sys, json
data = json.load(sys.stdin)
item_data = data.get('item_data', {})
print(f'Item Name: {item_data.get(\"name\", \"Unknown\")}')
print(f'Version: {data.get(\"version\", \"Unknown\")}')
print(f'Has Images: {\"Yes\" if \"image_ids\" in item_data and item_data[\"image_ids\"] else \"No\"}')
if 'image_ids' in item_data:
    print(f'Image Count: {len(item_data[\"image_ids\"])}')
    print(f'Image IDs: {item_data[\"image_ids\"]}')
else:
    print('Image Count: 0')
    print('Image IDs: None')
print(f'Content Hash: {data.get(\"content_hash\", \"Unknown\")[:16]}...')
print(f'Last Cached: {data.get(\"cached_at\", \"Unknown\")}')
"

echo ""
echo "💡 What happens next:"
echo "====================="
echo "1. When we attach images to the Trading Places item in Square"
echo "2. The next sync will detect the change"
echo "3. A 'before/after' snapshot will be saved to MongoDB"
echo "4. We can see exactly what changed (image_ids field added)"
echo "5. Version numbers will be tracked"
echo ""

echo "🔬 To demonstrate this, you could:"
echo "  • Manually attach images via Square Dashboard"
echo "  • Or use the Square API to update the item"
echo "  • Then run: ~/square-tools/bin/square_cache.sh sync"
echo "  • Then run: ~/square-tools/bin/square_cache.sh changes --since $(date +%Y-%m-%d)"
echo ""

echo "📋 Example of what the change detection will show:"
echo "================================================"
cat << 'EOF'
🔄 Trading Places - Rare Video 8 Format (1983) (ANE5SXKQR4JZ6AYEZDO26IMX)
   Type: update
   Time: 2025-09-30 02:35:00.000000+00:00
   Changes: item_data.image_ids, version, updated_at
   
   BEFORE: No images
   AFTER:  2 images attached
   - Image 1: ZDHVCXFYL7MNUQV6TAQTXH4G (1A2E186B-A015-4A86-84B6-C1F76EC9810D.jpeg)  
   - Image 2: JUOA5BTTKGJOXWHJ62RR4I62 (5748D4B2-F1DC-4BB6-84E4-90B56DCA4059.jpeg)
   
   Version change: 1759194139169 → [NEW_VERSION]
EOF

echo ""
echo "🗄️ MongoDB Collections Created:"
echo "==============================="
mongosh square_cache --eval "
console.log('📦 catalog_items collection:');
console.log('   Documents:', db.catalog_items.countDocuments());
console.log('   Indexes:', db.catalog_items.getIndexes().length);

console.log('\\n📸 change_snapshots collection:');
console.log('   Documents:', db.change_snapshots.countDocuments());
console.log('   Indexes:', db.change_snapshots.getIndexes().length);

console.log('\\n📊 sync_log collection:');
console.log('   Documents:', db.sync_log.countDocuments());
console.log('   Indexes:', db.sync_log.getIndexes().length);

console.log('\\n🔍 Sample change snapshot for Trading Places:');
var tradingPlacesChange = db.change_snapshots.findOne({item_id: 'ANE5SXKQR4JZ6AYEZDO26IMX'});
if (tradingPlacesChange) {
    console.log('   Item:', tradingPlacesChange.item_name);
    console.log('   Change Type:', tradingPlacesChange.change_type);
    console.log('   Timestamp:', tradingPlacesChange.timestamp);
    console.log('   Has Before Data:', tradingPlacesChange.before_data ? 'Yes' : 'No');
    console.log('   Has After Data:', tradingPlacesChange.after_data ? 'Yes' : 'No');
}
" --quiet

echo ""
echo "✅ Demo Complete!"
echo "=================="
echo ""
echo "The MongoDB cache system is now ready to track changes to your Square catalog items."
echo "It has captured the current state (before snapshot) of all 31 items, including"  
echo "Trading Places with NO images attached."
echo ""
echo "🔄 To see change tracking in action:"
echo "   1. Make changes to items in Square (via Dashboard or API)" 
echo "   2. Run: ~/square-tools/bin/square_cache.sh sync"
echo "   3. Run: ~/square-tools/bin/square_cache.sh changes"
echo ""
echo "🎯 The system will automatically detect and log:"
echo "   • New items created"
echo "   • Existing items updated (with field-level changes)"
echo "   • Items deleted"
echo "   • Complete before/after snapshots"
echo "   • Version number tracking"
echo "   • Audit trail with timestamps"