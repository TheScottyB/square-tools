#!/bin/bash

# Photos to Square Uploader
# Usage: ./photos_to_square.sh [photo_number] [square_token]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRE_FLIGHT="${SQUARE_AGENT_PREFLIGHT:-$SCRIPT_DIR/agent_preflight.sh}"

run_preflight() {
    local args=(--operation "photos_to_square_upload" --runtime "${SQUARE_RUNTIME_ID:-local_cli}" --quiet)
    if [ -n "${SQUARE_RUNTIME_MODE:-}" ]; then
        args+=(--mode "$SQUARE_RUNTIME_MODE")
    fi

    if [ ! -x "$PRE_FLIGHT" ]; then
        echo "❌ Preflight script not found or not executable: $PRE_FLIGHT" >&2
        exit 20
    fi

    "$PRE_FLIGHT" "${args[@]}"
}

export_photo_from_library() {
    local photo_index=${1:-1}
    local export_dir="$HOME/tmp/square_upload"
    
    echo "🖼️  Exporting photo #$photo_index from Photos library (27,569 total photos)..."
    
    # Clear previous exports
    rm -f "$export_dir"/*.jpg "$export_dir"/*.jpeg "$export_dir"/*.png "$export_dir"/*.heic 2>/dev/null
    
    # Export using AppleScript
    osascript -e "tell application \"Photos\" to export {item $photo_index of media items} to POSIX file \"$export_dir\""
    
    # Find the exported file
    exported_file=$(ls -t "$export_dir"/*.jpg "$export_dir"/*.jpeg "$export_dir"/*.png "$export_dir"/*.heic 2>/dev/null | head -1)
    
    if [ -n "$exported_file" ]; then
        echo "✅ Photo exported: $(basename "$exported_file")"
        echo "$exported_file"
    else
        echo "❌ Export failed"
        return 1
    fi
}

upload_to_square() {
    local image_file="$1"
    local access_token="$2"
    
    if [ ! -f "$image_file" ]; then
        echo "❌ Image file not found: $image_file"
        return 1
    fi
    
    if [ -z "$access_token" ]; then
        echo "❌ Square access token required"
        echo "📁 Photo ready for manual upload: $image_file"
        return 1
    fi
    
    echo "📤 Uploading to Square catalog..."
    
    # Generate unique identifiers
    local idempotency_key="upload_$(date +%s)_$(uuidgen | cut -d'-' -f1)"
    local image_id="#PHOTO_LIB_$(date +%s)"
    local image_name=$(basename "$image_file")
    
    # Upload using the proven working format
    response=$(curl -s -X POST \
        https://connect.squareup.com/v2/catalog/images \
        -H "Square-Version: 2024-09-18" \
        -H "Authorization: Bearer $access_token" \
        -F "request={\"idempotency_key\":\"$idempotency_key\",\"image\":{\"id\":\"$image_id\",\"type\":\"IMAGE\",\"image_data\":{\"caption\":\"$image_name - Uploaded from Photos Library via CLI\"}}}" \
        -F "image_file=@$image_file")
    
    # Check for errors
    if echo "$response" | grep -q '"errors"'; then
        echo "❌ Upload failed:"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        return 1
    elif echo "$response" | grep -q '"id"'; then
        echo "✅ Upload successful!"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        
        # Extract and display key information
        echo ""
        echo "📋 Upload Summary:"
        square_id=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['image']['id'])" 2>/dev/null)
        image_url=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['image']['image_data']['url'])" 2>/dev/null)
        echo "   Square Image ID: $square_id"
        echo "   Image URL: $image_url"
        return 0
    else
        echo "❌ Unexpected response:"
        echo "$response"
        return 1
    fi
}

# Main execution
main() {
    run_preflight || exit $?

    local photo_num=${1:-1}
    local square_token="$2"
    
    echo "📸 Photos to Square CLI Tool"
    echo "=============================="
    
    # Export photo
    export_photo_from_library "$photo_num"
    if [ $? -eq 0 ]; then
        # Find the exported file
        exported_file=$(ls -t "$HOME/tmp/square_upload"/*.jpg "$HOME/tmp/square_upload"/*.jpeg "$HOME/tmp/square_upload"/*.png "$HOME/tmp/square_upload"/*.heic 2>/dev/null | head -1)
        if [ -n "$exported_file" ]; then
            echo "📁 Using exported file: $(basename "$exported_file")"
            # Upload to Square
            upload_to_square "$exported_file" "$square_token"
        else
            echo "❌ Could not find exported file"
        fi
    fi
}

# Run if script is executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
