.PHONY: dev build test run
dev:
	uv pip install -e . -v \
	-C cmake.build-type=Release \
	-C cmake.define.CMAKE_OSX_ARCHITECTURES=arm64 \
	-C cmake.define.CMAKE_C_COMPILER_LAUNCHER=ccache \
	-C cmake.define.CMAKE_CXX_COMPILER_LAUNCHER=ccache
build:
	uv build -v \
	-C cmake.build-type=Release \
	-C cmake.define.CMAKE_OSX_ARCHITECTURES=arm64 \
	-C cmake.define.CMAKE_C_COMPILER_LAUNCHER=ccache \
	-C cmake.define.CMAKE_CXX_COMPILER_LAUNCHER=ccache

test:
	pytest tests -v

run:
	uv run rhythm-extractor testdata/drums2.wav --algorithm rhythm2013
