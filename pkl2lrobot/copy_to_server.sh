#!/bin/bash
# Copy dataset to remote server via SCP

set -e  # Exit on error

LOCAL_PATH="./data/lrobot/move_cup_to_shelf"
REMOTE_USER="axgu"
REMOTE_HOST="10.16.118.8"
REMOTE_PATH="/data2/axgu/.cache/move_cup_to_shelf"

echo "📦 Copying dataset to remote server..."
echo "   Local:  $LOCAL_PATH"
echo "   Remote: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"
echo ""

# Check if local path exists
if [ ! -d "$LOCAL_PATH" ]; then
    echo "❌ Error: Local dataset not found at $LOCAL_PATH"
    exit 1
fi

# Use SCP to copy recursively
# -r: recursive copy
# -p: preserve modification times and modes
# -C: enable compression
echo "🚀 Starting transfer (this may take a while)..."

scp -r -p -C "$LOCAL_PATH" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Dataset successfully copied to remote server!"
    echo "   Remote path: ${REMOTE_PATH}"
else
    echo ""
    echo "❌ Transfer failed"
    echo "   Please check:"
    echo "   - SSH connection to ${REMOTE_HOST}"
    echo "   - Remote directory permissions"
    echo "   - Network connectivity"
    exit 1
fi
