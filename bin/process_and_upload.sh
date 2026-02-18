#!/bin/bash

# Process and Upload Photos with Background Removal
# Usage: ./process_and_upload.sh [photo_number] [options]

set -e

# Load configuration
if [ -f "$HOME/square-tools/config.sh" ]; then
    source "$HOME/square-tools/config.sh"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_SYSTEM_DIR="$(dirname "$SCRIPT_DIR")/cache-system"
EXPORT_DIR="${EXPORT_DIR:-$HOME/tmp/square_upload}"
PROCESSED_DIR="${PROCESSED_DIR:-$HOME/tmp/square_processed}"
PRE_FLIGHT="${SQUARE_AGENT_PREFLIGHT:-$SCRIPT_DIR/agent_preflight.sh}"

# Create directories
mkdir -p "$EXPORT_DIR" "$PROCESSED_DIR"

# Default options
REMOVE_BG=false
PREVIEW=false
SKIP_UPLOAD=false
PROVIDER="auto"
USE_CACHE=true
PHOTO_NUM=""
SQUARE_TOKEN="${SQUARE_TOKEN:-}"

run_preflight() {
    local args=(--operation "process_and_upload" --runtime "${SQUARE_RUNTIME_ID:-local_cli}" --quiet)
    if [ -n "${SQUARE_RUNTIME_MODE:-}" ]; then
        args+=(--mode "$SQUARE_RUNTIME_MODE")
    fi

    if [ ! -x "$PRE_FLIGHT" ]; then
        echo "❌ Preflight script not found or not executable: $PRE_FLIGHT" >&2
        exit 20
    fi

    "$PRE_FLIGHT" "${args[@]}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --remove-bg)
            REMOVE_BG=true
            shift
            ;;
        --preview)
            PREVIEW=true
            shift
            ;;
        --skip-upload)
            SKIP_UPLOAD=true
            shift
            ;;
        --provider)
            PROVIDER="$2"
            shift 2
            ;;
        --no-cache)
            USE_CACHE=false
            shift
            ;;
        --help|-h)
            echo "Usage: process_and_upload.sh [photo_number] [options]"
            echo ""
            echo "Options:"
            echo "  --remove-bg          Remove background using AI"
            echo "  --preview            Show preview before upload"
            echo "  --skip-upload        Process only, don't upload to Square"
            echo "  --provider NAME      Use specific provider (gemini, banana, auto)"
            echo "  --no-cache           Don't use cached processed images"
            echo "  --help, -h           Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  SQUARE_TOKEN         Square API access token (required for upload)"
            echo "  GEMINI_API_KEY       Google Gemini API key (for background removal)"
            echo "  BANANA_API_KEY       Banana API key (for background removal)"
            echo ""
            echo "Examples:"
            echo "  process_and_upload.sh 27569 --remove-bg --preview"
            echo "  process_and_upload.sh 27569 --remove-bg --provider gemini"
            echo "  process_and_upload.sh 27569 --remove-bg --skip-upload"
            exit 0
            ;;
        *)
            if [[ "$1" =~ ^[0-9]+$ ]]; then
                PHOTO_NUM="$1"
            else
                echo "❌ Unknown option: $1"
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate photo number
if [ -z "$PHOTO_NUM" ]; then
    echo "❌ Photo number required"
    echo "Usage: process_and_upload.sh [photo_number] [options]"
    echo "Use --help for more information"
    exit 1
fi

# Check dependencies
check_dependencies() {
    local missing=()
    
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi
    
    if $REMOVE_BG; then
        if ! python3 -c "import PIL" 2>/dev/null; then
            missing+=("PIL (pip3 install Pillow)")
        fi
        if ! python3 -c "import pymongo" 2>/dev/null; then
            missing+=("pymongo (pip3 install pymongo)")
        fi
        if ! python3 -c "import requests" 2>/dev/null; then
            missing+=("requests (pip3 install requests)")
        fi
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo "❌ Missing dependencies:"
        for dep in "${missing[@]}"; do
            echo "   - $dep"
        done
        exit 1
    fi
}

# Export photo from Photos Library
export_photo() {
    local photo_index="$1"
    
    echo "🖼️  Exporting photo #$photo_index from Photos library..."
    
    # Clear previous exports
    rm -f "$EXPORT_DIR"/*.jpg "$EXPORT_DIR"/*.jpeg "$EXPORT_DIR"/*.png "$EXPORT_DIR"/*.heic 2>/dev/null
    
    # Export using AppleScript
    osascript -e "tell application \"Photos\" to export {item $photo_index of media items} to POSIX file \"$EXPORT_DIR\""
    
    # Find the exported file
    local exported_file=$(ls -t "$EXPORT_DIR"/*.jpg "$EXPORT_DIR"/*.jpeg "$EXPORT_DIR"/*.png "$EXPORT_DIR"/*.heic 2>/dev/null | head -1)
    
    if [ -n "$exported_file" ]; then
        echo "✅ Photo exported: $(basename "$exported_file")"
        echo "$exported_file"
    else
        echo "❌ Export failed"
        return 1
    fi
}

# Process image with background removal
process_image() {
    local input_path="$1"
    local output_path="$2"
    
    echo "🎨 Processing image with background removal..."
    
    # Build Python command
    local python_cmd="
import sys
sys.path.insert(0, '$CACHE_SYSTEM_DIR')
from bg_removal_service import BackgroundRemovalService

service = BackgroundRemovalService()
output_path, metadata = service.remove_background(
    '$input_path',
    output_path='$output_path',
    provider='$PROVIDER' if '$PROVIDER' != 'auto' else None,
    use_cache=$USE_CACHE
)

if output_path:
    print(f'SUCCESS:{output_path}')
    print(f'Provider: {metadata.get(\"provider\")}')
    print(f'Cost: \${metadata.get(\"cost\", 0):.4f}')
    print(f'From cache: {metadata.get(\"from_cache\", False)}')
    sys.exit(0)
else:
    print(f'ERROR:{metadata.get(\"error\", \"Unknown error\")}')
    sys.exit(1)
"
    
    # Run processing
    local result=$(python3 -c "$python_cmd" 2>&1)
    local exit_code=$?
    
    echo "$result"
    
    if [ $exit_code -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Preview image
preview_image() {
    local image_path="$1"
    
    if [ ! -f "$image_path" ]; then
        echo "❌ Image not found: $image_path"
        return 1
    fi
    
    echo "👁️  Opening preview..."
    open "$image_path"
    
    echo ""
    read -p "Continue with upload? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Upload cancelled"
        return 1
    fi
    
    return 0
}

# Upload to Square
upload_to_square() {
    local image_file="$1"
    local access_token="$2"
    
    if [ ! -f "$image_file" ]; then
        echo "❌ Image file not found: $image_file"
        return 1
    fi
    
    if [ -z "$access_token" ]; then
        echo "❌ Square access token required (set SQUARE_TOKEN environment variable)"
        echo "📁 Processed image saved: $image_file"
        return 1
    fi
    
    echo "📤 Uploading to Square catalog..."
    
    # Generate unique identifiers
    local idempotency_key="upload_$(date +%s)_$(uuidgen | cut -d'-' -f1)"
    local image_id="#PHOTO_LIB_PROCESSED_$(date +%s)"
    local image_name=$(basename "$image_file")
    
    # Upload
    local response=$(curl -s -X POST \
        https://connect.squareup.com/v2/catalog/images \
        -H "Square-Version: 2024-09-18" \
        -H "Authorization: Bearer $access_token" \
        -F "request={\"idempotency_key\":\"$idempotency_key\",\"image\":{\"id\":\"$image_id\",\"type\":\"IMAGE\",\"image_data\":{\"caption\":\"$image_name - Processed with background removal via CLI\"}}}" \
        -F "image_file=@$image_file")
    
    # Check for errors
    if echo "$response" | grep -q '"errors"'; then
        echo "❌ Upload failed:"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        return 1
    elif echo "$response" | grep -q '"id"'; then
        echo "✅ Upload successful!"
        
        # Extract and display key information
        local square_id=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['image']['id'])" 2>/dev/null)
        local image_url=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['image']['image_data']['url'])" 2>/dev/null)
        
        echo ""
        echo "📋 Upload Summary:"
        echo "   Square Image ID: $square_id"
        echo "   Image URL: $image_url"
        echo "   Processed Image: $image_file"
        return 0
    else
        echo "❌ Unexpected response:"
        echo "$response"
        return 1
    fi
}

# Main execution
main() {
    run_preflight

    echo "📸 Photos to Square - Enhanced with AI Processing"
    echo "=================================================="
    echo ""
    
    # Check dependencies
    check_dependencies
    
    # Export photo
    exported_file=$(export_photo "$PHOTO_NUM")
    if [ $? -ne 0 ]; then
        exit 1
    fi
    
    # Determine which file to use
    local file_to_upload="$exported_file"
    
    # Process with background removal if requested
    if $REMOVE_BG; then
        local input_name=$(basename "$exported_file")
        local output_path="$PROCESSED_DIR/${input_name%.*}_no_bg.png"
        
        if process_image "$exported_file" "$output_path"; then
            file_to_upload="$output_path"
            echo ""
            echo "✅ Background removal complete"
            echo "   Original: $exported_file"
            echo "   Processed: $file_to_upload"
        else
            echo "⚠️  Background removal failed, using original image"
            file_to_upload="$exported_file"
        fi
    fi
    
    echo ""
    
    # Preview if requested
    if $PREVIEW; then
        if ! preview_image "$file_to_upload"; then
            exit 0
        fi
    fi
    
    # Upload to Square unless skipped
    if ! $SKIP_UPLOAD; then
        echo ""
        upload_to_square "$file_to_upload" "$SQUARE_TOKEN"
    else
        echo "⏭️  Upload skipped (--skip-upload specified)"
        echo "📁 Processed file ready: $file_to_upload"
    fi
}

# Run main function
main
