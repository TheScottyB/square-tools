#!/bin/bash

# Square Items MongoDB Cache CLI Wrapper
# Usage: ./square_cache.sh <command> [options]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_MANAGER="$HOME/Workspace/square-tools/cache-system/square_cache_manager.py"
SQUARE_TOKEN="${SQUARE_TOKEN}"

show_help() {
    echo "🗄️  Square Items MongoDB Cache Manager"
    echo "======================================"
    echo ""
    echo "Commands:"
    echo "  sync             - Sync all Square catalog items to MongoDB cache"
    echo "  changes          - Show recent changes"
    echo "  report           - Generate detailed change report"
    echo "  item <ID>        - Get cached item by ID"
    echo "  search <PATTERN> - Search items by name or SKU pattern"
    echo "  status           - Show cache status"
    echo ""
    echo "Search Options:"
    echo "  --name <pattern>  - Search by item name"
    echo "  --sku <pattern>   - Search by SKU"
    echo ""
    echo "Other Options:"
    echo "  --since YYYY-MM-DD  - Show changes since date"
    echo "  --json              - Output in JSON format"
    echo ""
    echo "Examples:"
    echo "  ./square_cache.sh sync"
    echo "  ./square_cache.sh changes --since 2025-09-30"
    echo "  ./square_cache.sh search 'Trading Places'  # name search"
    echo "  ./square_cache.sh search --sku RG-0005     # SKU search"
    echo "  ./square_cache.sh item ANE5SXKQR4JZ6AYEZDO26IMX"
    echo ""
    echo "Environment Variables:"
    echo "  SQUARE_TOKEN - Square API access token (default: set from upload session)"
}

check_requirements() {
    # Check if MongoDB is running
    if ! mongosh --eval "db.runCommand('ismaster')" --quiet >/dev/null 2>&1; then
        echo "❌ MongoDB is not running. Please start it:"
        echo "   brew services start mongodb-community@8.0"
        exit 1
    fi
    
    # Check if Python script exists
    if [ ! -f "$CACHE_MANAGER" ]; then
        echo "❌ Cache manager script not found: $CACHE_MANAGER"
        exit 1
    fi
    
    # Check if Square token is set
    if [ -z "$SQUARE_TOKEN" ]; then
        echo "❌ SQUARE_TOKEN not set. Please set it:"
        echo "   export SQUARE_TOKEN='your_token_here'"
        exit 1
    fi
}

get_cache_status() {
    echo "📊 Square Items Cache Status"
    echo "============================"
    
    # MongoDB status
    echo "🗄️  MongoDB Status:"
    if mongosh --eval "db.runCommand('ismaster')" --quiet >/dev/null 2>&1; then
        echo "   ✅ Running"
    else
        echo "   ❌ Not running"
    fi
    
    # Database stats
    echo ""
    echo "📈 Cache Statistics:"
    mongosh square_cache --eval "
        print('   Items cached: ' + db.catalog_items.countDocuments());
        print('   Change records: ' + db.change_snapshots.countDocuments());
        print('   Sync operations: ' + db.sync_log.countDocuments());
        
        var lastSync = db.sync_log.findOne({}, {sort: {timestamp: -1}});
        if (lastSync) {
            print('   Last sync: ' + lastSync.timestamp);
            print('   Last sync status: ' + (lastSync.error ? 'Failed - ' + lastSync.error : 'Success'));
        } else {
            print('   Last sync: Never');
        }
    " --quiet
}

main() {
    local command="$1"
    shift
    
    case "$command" in
        "sync")
            check_requirements
            echo "🔄 Starting Square catalog sync..."
            python3 "$CACHE_MANAGER" sync --token "$SQUARE_TOKEN" "$@"
            ;;
        "changes")
            check_requirements
            python3 "$CACHE_MANAGER" changes --token "$SQUARE_TOKEN" "$@"
            ;;
        "report")
            check_requirements
            python3 "$CACHE_MANAGER" report --token "$SQUARE_TOKEN" "$@"
            ;;
        "item")
            check_requirements
            if [ -z "$1" ]; then
                echo "❌ Item ID required"
                echo "Usage: $0 item <ITEM_ID>"
                exit 1
            fi
            python3 "$CACHE_MANAGER" item --token "$SQUARE_TOKEN" --item-id "$1"
            ;;
        "search")
            check_requirements
            # Handle search with optional --name or --sku flags
            if [ "$1" = "--sku" ]; then
                if [ -z "$2" ]; then
                    echo "❌ SKU pattern required"
                    echo "Usage: $0 search --sku <SKU>"
                    exit 1
                fi
                python3 "$CACHE_MANAGER" search --token "$SQUARE_TOKEN" --sku "$2"
            elif [ "$1" = "--name" ]; then
                if [ -z "$2" ]; then
                    echo "❌ Name pattern required"
                    echo "Usage: $0 search --name <PATTERN>"
                    exit 1
                fi
                python3 "$CACHE_MANAGER" search --token "$SQUARE_TOKEN" --name "$2"
            else
                # Default to name search for backward compatibility
                if [ -z "$1" ]; then
                    echo "❌ Search pattern required"
                    echo "Usage: $0 search <PATTERN> or search --sku <SKU>"
                    exit 1
                fi
                python3 "$CACHE_MANAGER" search --token "$SQUARE_TOKEN" --name "$1"
            fi
            ;;
        "status")
            get_cache_status
            ;;
        "help"|"-h"|"--help"|"")
            show_help
            ;;
        *)
            echo "❌ Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"