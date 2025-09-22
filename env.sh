#!/bin/bash

# Get the absolute path of the project root
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS=$(ls "$ROOT_DIR/bin")
echo -e "Adding scripts to PATH:\n$SCRIPTS"
# Add bin directory to PATH if not already included
export PATH="$ROOT_DIR/bin:$PATH"

