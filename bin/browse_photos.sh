#!/bin/bash

# Photos Library Browser
# Usage: ./browse_photos.sh [command] [options]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRE_FLIGHT="${SQUARE_AGENT_PREFLIGHT:-$SCRIPT_DIR/agent_preflight.sh}"

run_preflight() {
    local args=(--operation "browse_photos" --runtime "${SQUARE_RUNTIME_ID:-local_cli}" --quiet)
    if [ -n "${SQUARE_RUNTIME_MODE:-}" ]; then
        args+=(--mode "$SQUARE_RUNTIME_MODE")
    fi

    if [ ! -x "$PRE_FLIGHT" ]; then
        echo "❌ Preflight script not found or not executable: $PRE_FLIGHT" >&2
        exit 20
    fi

    "$PRE_FLIGHT" "${args[@]}"
}

show_help() {
    echo "📸 Photos Library Browser"
    echo "=========================="
    echo ""
    echo "Commands:"
    echo "  recent [N]     - Show N most recent photos (default: 10)"
    echo "  search TEXT    - Search photo names/titles containing TEXT"
    echo "  date YYYY-MM   - Show photos from specific month"
    echo "  random [N]     - Show N random photos (default: 5)"
    echo "  info NUMBER    - Show detailed info for photo number"
    echo "  export NUMBER  - Export photo number to current directory"
    echo ""
    echo "Examples:"
    echo "  ./browse_photos.sh recent 20        # Show 20 most recent photos"
    echo "  ./browse_photos.sh search \"beach\"    # Find photos with 'beach' in name"
    echo "  ./browse_photos.sh date 2024-12     # Photos from December 2024"
    echo "  ./browse_photos.sh info 1500        # Details for photo #1500"
    echo "  ./browse_photos.sh export 1500      # Export photo #1500"
}

get_photo_info() {
    local photo_num=$1
    
    # Get basic info about the photo
    osascript << EOF
tell application "Photos"
    try
        set photoItem to item $photo_num of media items
        set photoName to name of photoItem
        set photoDate to date of photoItem
        set photoFilename to filename of photoItem
        
        return "Photo #$photo_num: " & photoName & " | " & photoDate & " | " & photoFilename
    on error
        return "Photo #$photo_num: [Error accessing photo]"
    end try
end tell
EOF
}

show_recent_photos() {
    local count=${1:-10}
    local total_photos=27569
    
    echo "🕐 Most Recent $count Photos:"
    echo "=============================="
    
    # Start from the end (most recent) and work backwards
    for ((i=0; i<count; i++)); do
        local photo_num=$((total_photos - i))
        echo "$(get_photo_info $photo_num)"
    done
}

search_photos() {
    local search_term="$1"
    local max_results=20
    local found=0
    
    echo "🔍 Searching for photos containing '$search_term':"
    echo "=================================================="
    
    # Search through recent photos first (more likely to be relevant)
    for ((i=27569; i>=1 && found<max_results; i--)); do
        local info=$(get_photo_info $i)
        if echo "$info" | grep -i "$search_term" > /dev/null; then
            echo "$info"
            ((found++))
        fi
        
        # Show progress every 1000 photos
        if ((i % 1000 == 0)); then
            echo "  ... searching photo #$i ..." >&2
        fi
    done
    
    if [ $found -eq 0 ]; then
        echo "No photos found containing '$search_term'"
    else
        echo ""
        echo "Found $found photos. Use 'info NUMBER' for details or 'export NUMBER' to export."
    fi
}

show_random_photos() {
    local count=${1:-5}
    
    echo "🎲 $count Random Photos:"
    echo "======================="
    
    for ((i=1; i<=count; i++)); do
        local random_num=$((RANDOM % 27569 + 1))
        echo "$(get_photo_info $random_num)"
    done
}

export_photo() {
    local photo_num=$1
    local export_dir="$PWD"
    
    echo "📤 Exporting photo #$photo_num..."
    
    # Clear any existing exports
    rm -f *.jpg *.jpeg *.png *.heic 2>/dev/null
    
    # Export the photo
    osascript -e "tell application \"Photos\" to export {item $photo_num of media items} to POSIX file \"$export_dir\""
    
    # Find the exported file
    exported_file=$(ls -t *.jpg *.jpeg *.png *.heic 2>/dev/null | head -1)
    
    if [ -n "$exported_file" ]; then
        echo "✅ Exported: $exported_file"
        echo "📊 File size: $(ls -lh "$exported_file" | awk '{print $5}')"
        echo ""
        echo "💡 To upload to Square:"
        echo "   ../photos_to_square.sh $photo_num YOUR_SQUARE_TOKEN"
        echo ""
        echo "📁 File ready at: $PWD/$exported_file"
    else
        echo "❌ Export failed"
        return 1
    fi
}

# Main execution
case "$1" in
    "recent")
        run_preflight || exit $?
        show_recent_photos "$2"
        ;;
    "search")
        run_preflight || exit $?
        if [ -z "$2" ]; then
            echo "❌ Search term required"
            echo "Usage: $0 search \"search term\""
            exit 1
        fi
        search_photos "$2"
        ;;
    "random")
        run_preflight || exit $?
        show_random_photos "$2"
        ;;
    "info")
        run_preflight || exit $?
        if [ -z "$2" ]; then
            echo "❌ Photo number required"
            echo "Usage: $0 info NUMBER"
            exit 1
        fi
        echo "📋 Photo Details:"
        echo "=================="
        get_photo_info "$2"
        ;;
    "export")
        run_preflight || exit $?
        if [ -z "$2" ]; then
            echo "❌ Photo number required"
            echo "Usage: $0 export NUMBER"
            exit 1
        fi
        export_photo "$2"
        ;;
    "help"|"-h"|"--help"|"")
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
