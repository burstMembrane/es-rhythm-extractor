#!/bin/bash

# Setup script to clone essentia repository
# This replaces the problematic git submodule approach

set -e  # Exit on any error

VENDOR_DIR="vendor"
ESSENTIA_DIR="$VENDOR_DIR/essentia"
ESSENTIA_REPO="https://github.com/MTG/essentia.git"
# Pinned commit: last commit before FFmpeg 5.x API changes (has swresample + old channel_layout API)
ESSENTIA_COMMIT="36ec3d92"

echo "Setting up Essentia library..."

# Create vendor directory if it doesn't exist
mkdir -p "$VENDOR_DIR"

# Skip cloning if essentia source already exists (e.g., from sdist)
if [ -d "$ESSENTIA_DIR/src" ]; then
    echo "Essentia source already present, skipping clone..."
else
    # Remove existing essentia directory if it exists but is incomplete
    if [ -d "$ESSENTIA_DIR" ]; then
        echo "Removing incomplete essentia directory..."
        rm -rf "$ESSENTIA_DIR"
    fi

    # Clone essentia repository and checkout pinned commit
    echo "Cloning essentia from $ESSENTIA_REPO (commit: $ESSENTIA_COMMIT)..."
    git clone --filter=blob:none "$ESSENTIA_REPO" "$ESSENTIA_DIR"
    cd "$ESSENTIA_DIR"
    git checkout "$ESSENTIA_COMMIT"
    cd - > /dev/null

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
fi

# Check for system Eigen first, build only if needed
echo "Checking for Eigen headers..."

# Common system locations for Eigen
EIGEN_FOUND=""
for EIGEN_PATH in \
    "/usr/include/eigen3" \
    "/usr/local/include/eigen3" \
    "/opt/homebrew/include/eigen3" \
    "/usr/include/eigen3" \
    "$ESSENTIA_DIR/packaging/debian_3rdparty/include/eigen3"; do
    
    if [ -f "$EIGEN_PATH/unsupported/Eigen/CXX11/Tensor" ]; then
        echo "Found system Eigen at: $EIGEN_PATH"
        EIGEN_FOUND="$EIGEN_PATH"
        break
    fi
done

# Only build Eigen if not found on system
if [ -z "$EIGEN_FOUND" ]; then
    echo "System Eigen not found, building Eigen 3.3.7..."
    cd "$ESSENTIA_DIR/packaging/debian_3rdparty"
    
    EIGEN_VERSION="3.3.7"
    PREFIX="$PWD"
    
    rm -rf tmp
    mkdir tmp
    cd tmp
    
    curl -SLO https://gitlab.com/libeigen/eigen/-/archive/$EIGEN_VERSION/eigen-$EIGEN_VERSION.tar.gz
    tar -xf eigen-$EIGEN_VERSION.tar.gz
    cd eigen-$EIGEN_VERSION
    
    mkdir build
    cd build
    
    # Configure and install Eigen
    cmake ../ -DCMAKE_INSTALL_PREFIX="$PREFIX"
    make install
    
    # Create pkgconfig file
    mkdir -p "$PREFIX"/lib/pkgconfig/
    cp "$PREFIX"/share/pkgconfig/eigen3.pc "$PREFIX"/lib/pkgconfig/ 2>/dev/null || echo "Pkgconfig copy failed, continuing..."
    
    cd ../../..
    rm -rf tmp
    
    echo "Eigen headers built in: $PREFIX/include/eigen3"
else
    echo "Using system Eigen at: $EIGEN_FOUND"
fi

echo "Essentia setup complete!"
echo "Essentia source code is now available in: $ESSENTIA_DIR"
if [ -n "$EIGEN_FOUND" ]; then
    echo "Using system Eigen at: $EIGEN_FOUND"
else
    echo "Eigen headers built in: $ESSENTIA_DIR/packaging/debian_3rdparty/include"
fi