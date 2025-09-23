#!/bin/bash

# Setup script to clone essentia repository
# This replaces the problematic git submodule approach

set -e  # Exit on any error

VENDOR_DIR="vendor"
ESSENTIA_DIR="$VENDOR_DIR/essentia"
ESSENTIA_REPO="https://github.com/MTG/essentia.git"
ESSENTIA_BRANCH="master"

echo "Setting up Essentia library..."

# Create vendor directory if it doesn't exist
mkdir -p "$VENDOR_DIR"

# Remove existing essentia directory if it exists
if [ -d "$ESSENTIA_DIR" ]; then
    echo "Removing existing essentia directory..."
    rm -rf "$ESSENTIA_DIR"
fi

# Clone essentia repository (shallow clone for faster download)
echo "Cloning essentia from $ESSENTIA_REPO (branch: $ESSENTIA_BRANCH)..."
git clone --depth 1 --branch "$ESSENTIA_BRANCH" "$ESSENTIA_REPO" "$ESSENTIA_DIR"

# Remove .git directory to make it a regular directory (not a repo)
echo "Cleaning up git metadata..."
rm -rf "$ESSENTIA_DIR/.git"

# Remove problematic submodule configurations
if [ -f "$ESSENTIA_DIR/.gitmodules" ]; then
    echo "Removing .gitmodules from essentia..."
    rm "$ESSENTIA_DIR/.gitmodules"
fi

# Remove test directories that would contain large LFS files
if [ -d "$ESSENTIA_DIR/test/models" ]; then
    echo "Removing test/models directory (contains large LFS files)..."
    rm -rf "$ESSENTIA_DIR/test/models"
fi

if [ -d "$ESSENTIA_DIR/test/audio" ]; then
    echo "Removing test/audio directory..."
    rm -rf "$ESSENTIA_DIR/test/audio"
fi

# Build Eigen headers (required for compilation)
echo "Building Eigen headers..."
cd "$ESSENTIA_DIR/packaging/debian_3rdparty"
./build_eigen3.sh

echo "Essentia setup complete!"
echo "Essentia source code is now available in: $ESSENTIA_DIR"
echo "Eigen headers built in: $ESSENTIA_DIR/packaging/debian_3rdparty/include"