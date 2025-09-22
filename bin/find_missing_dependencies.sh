#!/bin/bash

echo "=== Finding Missing Dependencies ==="

# Try to build and capture missing header files
echo "Running build to find missing files..."
build_output=$(uv sync 2>&1)
missing_headers=$(echo "$build_output" | grep "fatal error.*file not found" | sed -n "s/.*'\([^']*\)' file not found/\1/p" | head -10)

if [ -z "$missing_headers" ]; then
    echo "No missing header files found!"
    
    # Check if build actually succeeded
    if echo "$build_output" | grep -q "Successfully built essentia-rhythm-extractor"; then
        echo "🎉 BUILD SUCCEEDED! 🎉"
        exit 0
    else
        echo "Build failed for other reasons. Checking for warnings/errors..."
        echo "$build_output" | tail -20
        
        # Check for template warnings
        template_warnings=$(echo "$build_output" | grep "undefined-var-template" | wc -l)
        if [ "$template_warnings" -gt 0 ]; then
            echo ""
            echo "ℹ️  Found $template_warnings template instantiation warnings."
            echo "These are non-fatal but may be stopping the build."
            echo "Try adding -Wno-undefined-var-template to compiler flags in CMakeLists.txt"
        fi
        exit 1
    fi
fi

echo "Missing headers found:"
echo "$missing_headers"
echo ""

# For each missing header, find the corresponding .cpp file
echo "=== Searching for corresponding source files ==="
for header in $missing_headers; do
    echo "Looking for: $header"
    
    # Extract just the filename without path
    filename=$(basename "$header" .h)
    
    # Search for both .cpp and .h files
    echo "  Searching for ${filename}.*"
    find vendor/essentia/src -name "${filename}.*" -type f | head -3
    echo ""
done

echo "=== Algorithm directories available ==="
ls vendor/essentia/src/algorithms/

echo ""
echo "=== To add missing algorithms to CMakeLists.txt ==="
echo "1. Add source files (*.cpp) to the CMakeLists.txt file"
echo "2. Add include directories if needed"
echo "3. Run this script again to find next missing dependency"