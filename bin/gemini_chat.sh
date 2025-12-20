#!/bin/bash

# Interactive Gemini Chat Interface
# Usage: gemini_chat.sh [model] [image_path]
#
# Models: flash (default), pro, flash-image
# Examples:
#   gemini_chat.sh                          # Text chat with Flash
#   gemini_chat.sh pro                      # Text chat with Pro
#   gemini_chat.sh flash image.jpg          # Chat about an image

set -e

MODEL="${1:-flash}"
IMAGE_PATH="$2"
GEMINI_API_KEY="${GEMINI_API_KEY:-}"

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ GEMINI_API_KEY not set"
    echo "Set it with: export GEMINI_API_KEY='your_key'"
    exit 1
fi

# Map model names to API endpoints
case "$MODEL" in
    flash)
        API_MODEL="gemini-2.5-flash"
        ;;
    pro)
        API_MODEL="gemini-2.5-pro"
        ;;
    2.0)
        API_MODEL="gemini-2.0-flash"
        ;;
    exp)
        API_MODEL="gemini-2.0-flash-exp"
        ;;
    *)
        echo "❌ Unknown model: $MODEL"
        echo "Available: flash (2.5), pro (2.5), 2.0, exp"
        exit 1
        ;;
esac

ENDPOINT="https://generativelanguage.googleapis.com/v1beta/models/${API_MODEL}:generateContent"

echo "🤖 Gemini Chat - Model: $API_MODEL"
echo "========================================="
echo "Type 'exit' or 'quit' to end chat"
echo ""

# Function to send text-only request
send_text_prompt() {
    local prompt="$1"
    
    local json_payload=$(cat <<EOF
{
  "contents": [{
    "parts": [{
      "text": "$prompt"
    }]
  }]
}
EOF
)
    
    local response=$(curl -s -X POST "$ENDPOINT?key=$GEMINI_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$json_payload")
    
    # Extract text response
    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'candidates' in data and len(data['candidates']) > 0:
        parts = data['candidates'][0].get('content', {}).get('parts', [])
        for part in parts:
            if 'text' in part:
                print(part['text'])
                break
    elif 'error' in data:
        print(f\"Error: {data['error'].get('message', 'Unknown error')}\")
    else:
        print('No response generated')
except Exception as e:
    print(f'Error parsing response: {e}')
    print(sys.stdin.read())
"
}

# Function to send image + text request
send_image_prompt() {
    local prompt="$1"
    local image_path="$2"
    
    # Read and encode image
    local image_base64=$(base64 -i "$image_path")
    
    # Detect mime type
    local mime_type="image/jpeg"
    case "${image_path##*.}" in
        png) mime_type="image/png" ;;
        jpg|jpeg) mime_type="image/jpeg" ;;
        gif) mime_type="image/gif" ;;
        webp) mime_type="image/webp" ;;
    esac
    
    local json_payload=$(cat <<EOF
{
  "contents": [{
    "parts": [
      {"text": "$prompt"},
      {
        "inline_data": {
          "mime_type": "$mime_type",
          "data": "$image_base64"
        }
      }
    ]
  }]
}
EOF
)
    
    local response=$(curl -s -X POST "$ENDPOINT?key=$GEMINI_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$json_payload")
    
    # Extract text response
    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'candidates' in data and len(data['candidates']) > 0:
        parts = data['candidates'][0].get('content', {}).get('parts', [])
        for part in parts:
            if 'text' in part:
                print(part['text'])
                break
    elif 'error' in data:
        print(f\"Error: {data['error'].get('message', 'Unknown error')}\")
    else:
        print('No response generated')
except Exception as e:
    print(f'Error parsing response: {e}')
"
}

# If image provided, start with image analysis
if [ -n "$IMAGE_PATH" ]; then
    if [ ! -f "$IMAGE_PATH" ]; then
        echo "❌ Image not found: $IMAGE_PATH"
        exit 1
    fi
    echo "📷 Analyzing image: $(basename "$IMAGE_PATH")"
    echo ""
    echo "You> describe this image"
    echo ""
    echo "Gemini> "
    send_image_prompt "Describe this image in detail" "$IMAGE_PATH"
    echo ""
    echo "---"
    echo ""
fi

# Interactive chat loop
while true; do
    echo -n "You> "
    read -r user_input
    
    # Check for exit
    if [ "$user_input" = "exit" ] || [ "$user_input" = "quit" ]; then
        echo "👋 Goodbye!"
        break
    fi
    
    # Skip empty input
    if [ -z "$user_input" ]; then
        continue
    fi
    
    echo ""
    echo "Gemini> "
    
    # Send to Gemini
    if [ -n "$IMAGE_PATH" ]; then
        send_image_prompt "$user_input" "$IMAGE_PATH"
    else
        send_text_prompt "$user_input"
    fi
    
    echo ""
    echo "---"
    echo ""
done
