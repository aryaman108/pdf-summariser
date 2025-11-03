#!/bin/bash

# Disk Space Cleanup Script for macOS
# This script helps free up space to install the full application

echo "============================================================"
echo "Disk Space Cleanup Script"
echo "============================================================"
echo ""

# Show current disk usage
echo "Current disk usage:"
df -h . | tail -1
echo ""

# Calculate space needed
AVAILABLE=$(df -k . | tail -1 | awk '{print $4}')
NEEDED=$((3 * 1024 * 1024))  # 3GB in KB

echo "Available space: $(($AVAILABLE / 1024))MB"
echo "Required space: 3GB (3072MB)"
echo ""

if [ $AVAILABLE -lt $NEEDED ]; then
    echo "⚠️  Insufficient space! Need to free up $(( ($NEEDED - $AVAILABLE) / 1024 ))MB"
    echo ""
else
    echo "✅ Sufficient space available!"
    exit 0
fi

# Function to show size and ask for confirmation
cleanup_item() {
    local path=$1
    local description=$2
    
    if [ -d "$path" ] || [ -f "$path" ]; then
        local size=$(du -sh "$path" 2>/dev/null | cut -f1)
        echo "Found: $description ($size)"
        read -p "Delete this? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$path"
            echo "✅ Deleted $description"
        else
            echo "⏭️  Skipped $description"
        fi
        echo ""
    fi
}

echo "Checking for items to clean up..."
echo ""

# Clean pip cache
cleanup_item "$HOME/.cache/pip" "Pip cache"

# Clean Homebrew cache
if command -v brew &> /dev/null; then
    echo "Found Homebrew. Cleaning up..."
    brew cleanup
    echo ""
fi

# Clean conda cache
if command -v conda &> /dev/null; then
    echo "Found Conda. Cleaning up..."
    conda clean --all -y
    echo ""
fi

# Clean npm cache
if command -v npm &> /dev/null; then
    cleanup_item "$HOME/.npm" "NPM cache"
fi

# Clean yarn cache
if command -v yarn &> /dev/null; then
    echo "Found Yarn. Cleaning cache..."
    yarn cache clean
    echo ""
fi

# Clean trash
cleanup_item "$HOME/.Trash" "Trash"

# Clean Xcode derived data
cleanup_item "$HOME/Library/Developer/Xcode/DerivedData" "Xcode derived data"

# Clean iOS device support
cleanup_item "$HOME/Library/Developer/Xcode/iOS DeviceSupport" "iOS device support files"

# Clean old iOS simulators
if command -v xcrun &> /dev/null; then
    echo "Cleaning old iOS simulators..."
    xcrun simctl delete unavailable 2>/dev/null
    echo ""
fi

# Clean Docker (if installed)
if command -v docker &> /dev/null; then
    echo "Found Docker. Cleaning up..."
    read -p "Clean Docker images and containers? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker system prune -a -f
        echo "✅ Docker cleaned"
    fi
    echo ""
fi

# Show final disk usage
echo "============================================================"
echo "Final disk usage:"
df -h . | tail -1
echo ""

AVAILABLE=$(df -k . | tail -1 | awk '{print $4}')
echo "Available space: $(($AVAILABLE / 1024))MB"

if [ $AVAILABLE -lt $NEEDED ]; then
    echo ""
    echo "⚠️  Still need $(( ($NEEDED - $AVAILABLE) / 1024 ))MB more space"
    echo ""
    echo "Additional suggestions:"
    echo "  1. Check for large files: du -sh ~/* 2>/dev/null | sort -hr | head -20"
    echo "  2. Empty Downloads folder: rm -rf ~/Downloads/*"
    echo "  3. Clean up old projects and files"
    echo "  4. Use external storage for this project"
else
    echo ""
    echo "✅ Sufficient space available! You can now install dependencies:"
    echo ""
    echo "  source .venv/bin/activate"
    echo "  pip install --no-cache-dir -r requirements.txt"
    echo "  python app.py"
fi

echo "============================================================"
