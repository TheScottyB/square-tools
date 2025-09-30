#!/bin/bash

# Square Tools Configuration Template
# ===================================
# Copy this file to config.local.sh and customize your settings

# Square API Configuration
# Get your token from: https://developer.squareup.com/apps
export SQUARE_TOKEN="YOUR_SQUARE_TOKEN_HERE"
export SQUARE_ENVIRONMENT="production"  # or 'sandbox'

# MongoDB Configuration  
export MONGO_URI="mongodb://localhost:27017/"
export MONGO_DATABASE="square_cache"

# Tool Paths (usually don't need to change these)
export SQUARE_TOOLS_HOME="$HOME/square-tools"
export SQUARE_CACHE_SYSTEM="$SQUARE_TOOLS_HOME/cache-system"
export SQUARE_DATA_DIR="$SQUARE_TOOLS_HOME/data"

# Photos Library Configuration
export PHOTOS_LIBRARY_PATH="$HOME/Pictures/Photos Library.photoslibrary"
export PHOTOS_EXPORT_DIR="$SQUARE_DATA_DIR/photo_exports"

# Logging
export SQUARE_LOG_LEVEL="INFO"
export SQUARE_LOG_DIR="$SQUARE_DATA_DIR/logs"

# Create necessary directories
mkdir -p "$SQUARE_DATA_DIR"
mkdir -p "$PHOTOS_EXPORT_DIR" 
mkdir -p "$SQUARE_LOG_DIR"

echo "✅ Square Tools configuration loaded"
echo "📂 Tools home: $SQUARE_TOOLS_HOME"
echo "🗄️  MongoDB: $MONGO_URI"
echo "📸 Photos exports: $PHOTOS_EXPORT_DIR"