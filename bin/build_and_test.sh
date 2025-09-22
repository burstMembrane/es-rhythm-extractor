set -e
export CMAKE_BUILD_PARALLEL_LEVEL=$(sysctl -n hw.ncpu)
uv pip install -e . -v \
  -C cmake.build-type=Release \
  -C cmake.define.CMAKE_OSX_ARCHITECTURES=arm64 \
  -C cmake.define.CMAKE_C_COMPILER_LAUNCHER=ccache \
  -C cmake.define.CMAKE_CXX_COMPILER_LAUNCHER=ccache
# run the cli tool to verify the installation
uv run rhythm-extractor testdata/drums2.wav --algorithm rhythm2013