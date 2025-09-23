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