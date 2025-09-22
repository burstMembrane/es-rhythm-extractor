cmake_minimum_required(VERSION 3.20)
project(essentia_rhythm_multifeature LANGUAGES C CXX)

# Set modern CMake policies
cmake_policy(SET CMP0148 OLD)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# --- Build type & standard ---
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

# -------- Feature-targeted optimization profiles --------
option(ESSENTIA_OPT_PRESET "Optimization preset: native|x86v3|x86v2|armv82|portable" "native")

# Handle case where option is not set or OFF
if(NOT ESSENTIA_OPT_PRESET OR ESSENTIA_OPT_PRESET STREQUAL "OFF")
  set(ESSENTIA_OPT_PRESET "native")
endif()

# Common release toggles (math + section GC + visibility)
set(_ESSENTIA_BASE_CXX
  -O3 -DNDEBUG
  -ffast-math -fno-math-errno -fno-trapping-math -ffp-contract=fast
  -fmerge-all-constants
  -fvisibility=hidden -fvisibility-inlines-hidden
)
set(_ESSENTIA_BASE_C "${_ESSENTIA_BASE_CXX}")  # KissFFT is C

# Section GC works only with these on TUs:
set(_ESSENTIA_SECTIONS -ffunction-sections -fdata-sections)

# Linker dead-stripping (ELF vs Mach-O)
if(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
  set(_ESSENTIA_LD -Wl,-dead_strip -Wl,-x)
else()
  set(_ESSENTIA_LD -Wl,--gc-sections -Wl,--as-needed -Wl,-O3)
endif()

# Architecture baselines
if(ESSENTIA_OPT_PRESET STREQUAL "native")
  set(_ESSENTIA_ARCH -march=native -mtune=native)
  if(CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64|arm64")
    list(APPEND _ESSENTIA_ARCH -mcpu=native)
  endif()
elseif(ESSENTIA_OPT_PRESET STREQUAL "x86v3")
  # AVX2/FMA baseline - modern Intel/AMD (2013+)
  set(_ESSENTIA_ARCH -march=x86-64-v3 -mtune=generic)
elseif(ESSENTIA_OPT_PRESET STREQUAL "x86v2")
  # SSE4.2/POPCNT baseline - compatible Intel/AMD (2009+)
  set(_ESSENTIA_ARCH -march=x86-64-v2 -mtune=generic)
elseif(ESSENTIA_OPT_PRESET STREQUAL "armv82")
  # ARM64 with NEON baseline - compatible AArch64 (2016+)
  set(_ESSENTIA_ARCH -march=armv8.2-a+fp16+dotprod -mtune=generic)
elseif(ESSENTIA_OPT_PRESET STREQUAL "portable")
  # Maximum compatibility - basic optimizations only
  set(_ESSENTIA_ARCH "")
  # Remove fast-math for portable builds
  list(REMOVE_ITEM _ESSENTIA_BASE_CXX -ffast-math -fno-math-errno -fno-trapping-math)
  list(REMOVE_ITEM _ESSENTIA_BASE_C -ffast-math -fno-math-errno -fno-trapping-math)
else()
  message(FATAL_ERROR "Unknown ESSENTIA_OPT_PRESET: ${ESSENTIA_OPT_PRESET}")
endif()

# GCC/Clang specific optimizations
set(_ESSENTIA_GCC_CLANG_CXX
  -funroll-loops
  "$<$<CXX_COMPILER_ID:GNU>:-fno-plt>"
  "$<$<CXX_COMPILER_ID:GNU>:-fno-semantic-interposition>"
  -falign-functions=32
)

# Apply optimization flags
add_compile_options(
  "$<$<CONFIG:Release>:${_ESSENTIA_BASE_CXX}>"
  "$<$<CONFIG:Release>:${_ESSENTIA_ARCH}>"
  "$<$<CONFIG:Release>:${_ESSENTIA_SECTIONS}>"
  "$<$<AND:$<CONFIG:Release>,$<CXX_COMPILER_ID:GNU,Clang>>:${_ESSENTIA_GCC_CLANG_CXX}>"
)

add_link_options("$<$<CONFIG:Release>:${_ESSENTIA_LD}>")

# --- Interprocedural optimization (LTO / ThinLTO) ---
# Works on GCC/Clang/MSVC; Clang will pick ThinLTO automatically if available.
include(CheckIPOSupported)
check_ipo_supported(RESULT ipo_ok OUTPUT ipo_err)
if(ipo_ok)
  set(CMAKE_INTERPROCEDURAL_OPTIMIZATION_RELEASE ON)
endif()

# Print optimization preset being used
message(STATUS "Essentia optimization preset: ${ESSENTIA_OPT_PRESET}")
if(_ESSENTIA_ARCH)
  message(STATUS "Architecture flags: ${_ESSENTIA_ARCH}")
endif()

# pybind11 via scikit-build-core
find_package(pybind11 CONFIG REQUIRED)

# Find Eigen3 - use system package on Linux, bundled otherwise
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
  find_package(Eigen3 REQUIRED)
endif()

# Find numpy
execute_process(
  COMMAND ${Python_EXECUTABLE} -c "import numpy; print(numpy.get_include())"
  OUTPUT_VARIABLE NUMPY_INCLUDE_DIR
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Read Essentia version and generate version.h
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/VERSION" ESSENTIA_VERSION_RAW)
string(STRIP "${ESSENTIA_VERSION_RAW}" ESSENTIA_VERSION)
set(ESSENTIA_VERSION_MAJOR 2)
set(ESSENTIA_VERSION_MINOR 1)
set(ESSENTIA_VERSION_PATCH 0)

# Configure version.h and place it in vendor/essentia/src/essentia/
configure_file(
  "${CMAKE_CURRENT_SOURCE_DIR}/version.h.in"
  "${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/essentia/version.h"
  @ONLY
)

# You'll incrementally add sources from vendor/essentia as you wire it up
add_library(essentia_rhythm_core STATIC
  src/core/mf_runner.cpp
  src/essentia_init.cpp
  # --- Begin Essentia vendor files (add as you copy them) ---
  # Essential Essentia core
  vendor/essentia/src/essentia/parameter.cpp
  vendor/essentia/src/essentia/configurable.cpp
  vendor/essentia/src/essentia/debugging.cpp
  vendor/essentia/src/essentia/algorithm.cpp
  vendor/essentia/src/essentia/essentiautil.cpp
  vendor/essentia/src/essentia/essentia.cpp
  vendor/essentia/src/algorithms/filters/iir.cpp
  vendor/essentia/src/essentia/pool.cpp
  vendor/essentia/src/essentia/range.cpp
  vendor/essentia/src/essentia/stringutil.cpp
  vendor/essentia/src/essentia/connector.cpp
  # Essential streaming infrastructure  
  vendor/essentia/src/essentia/streaming/sourcebase.cpp
  vendor/essentia/src/essentia/streaming/sinkbase.cpp
  vendor/essentia/src/essentia/streaming/streamingalgorithm.cpp
  vendor/essentia/src/essentia/streaming/streamingalgorithmcomposite.cpp
  # Scheduler infrastructure
  vendor/essentia/src/essentia/scheduler/network.cpp
  # Streaming algorithms needed by RhythmExtractor2013
  vendor/essentia/src/essentia/streaming/algorithms/poolstorage.cpp
  vendor/essentia/src/essentia/streaming/algorithms/devnull.cpp
  vendor/essentia/src/essentia/streaming/algorithms/ringbufferinput.cpp
  vendor/essentia/src/essentia/streaming/algorithms/ringbufferoutput.cpp
  vendor/essentia/src/essentia/streaming/algorithms/ringbuffervectoroutput.cpp
  # Streaming wrapper infrastructure
  vendor/essentia/src/essentia/streaming/streamingalgorithmwrapper.cpp
  # Rhythm stack
  vendor/essentia/src/algorithms/rhythm/rhythmextractor2013.cpp
  vendor/essentia/src/algorithms/rhythm/beattrackermultifeature.cpp
vendor/essentia/src/algorithms/rhythm/beattrackerdegara.cpp
vendor/essentia/src/algorithms/rhythm/onsetdetection.cpp
vendor/essentia/src/algorithms/rhythm/onsetdetectionglobal.cpp
vendor/essentia/src/algorithms/rhythm/tempotapdegara.cpp
vendor/essentia/src/algorithms/rhythm/tempotapmaxagreement.cpp
vendor/essentia/src/algorithms/standard/framecutter.cpp
vendor/essentia/src/algorithms/complex/cartesiantopolar.cpp
vendor/essentia/src/algorithms/standard/scale.cpp
vendor/essentia/src/essentia/streaming/streamingalgorithmcomposite.cpp
vendor/essentia/src/algorithms/complex/magnitude.cpp
vendor/essentia/src/algorithms/spectral/erbbands.cpp

  # Spectral/temporal deps
vendor/essentia/src/algorithms/standard/windowing.cpp
vendor/essentia/src/algorithms/standard/spectrum.cpp
vendor/essentia/src/algorithms/standard/dct.cpp
vendor/essentia/src/algorithms/standard/idct.cpp
vendor/essentia/src/algorithms/standard/noiseadder.cpp
vendor/essentia/src/algorithms/standard/overlapadd.cpp
vendor/essentia/src/algorithms/standard/fftk.cpp
vendor/essentia/src/algorithms/standard/ifftk.cpp
vendor/essentia/src/algorithms/standard/spectrum.cpp
vendor/essentia/src/algorithms/filters/movingaverage.cpp
vendor/essentia/src/algorithms/standard/autocorrelation.cpp
vendor/essentia/src/algorithms/spectral/hfc.cpp
vendor/essentia/src/algorithms/spectral/flux.cpp
vendor/essentia/src/algorithms/spectral/triangularbands.cpp
vendor/essentia/src/algorithms/standard/powerspectrum.cpp
vendor/essentia/src/algorithms/standard/autocorrelation.cpp
vendor/essentia/src/algorithms/spectral/mfcc.cpp
vendor/essentia/src/algorithms/spectral/melbands.cpp
vendor/essentia/src/algorithms/spectral/triangularbarkbands.cpp
vendor/essentia/src/algorithms/spectral/hfc.cpp
vendor/essentia/src/algorithms/filters/movingaverage.cpp
vendor/essentia/src/algorithms/complex/magnitude.cpp
vendor/essentia/src/algorithms/temporal/loudness.cpp
vendor/essentia/src/algorithms/temporal/zerocrossingrate.cpp
vendor/essentia/src/algorithms/stats/rms.cpp
  #
  # KissFFT (to avoid FFTW)
vendor/essentia/src/3rdparty/kiss_fft130/kiss_fft.c
vendor/essentia/src/3rdparty/kiss_fft130/tools/kiss_fftr.c
  # --- End Essentia vendor files ---
)

target_include_directories(essentia_rhythm_core PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/src
  ${CMAKE_CURRENT_SOURCE_DIR}
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/essentia
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/essentia/streaming
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/essentia/streaming/algorithms
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/essentia/scheduler
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/essentia/utils
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/algorithms
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/algorithms/standard
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/algorithms/spectral
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/algorithms/filters
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/algorithms/complex
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/algorithms/temporal
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/algorithms/stats
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/streaming
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/3rdparty/kiss_fft130
  $<$<STREQUAL:${CMAKE_SYSTEM_NAME},Linux>:/usr/include/eigen3>
  $<$<STREQUAL:${CMAKE_SYSTEM_NAME},Linux>:/usr/include/eigen3/unsupported>
  $<$<NOT:$<STREQUAL:${CMAKE_SYSTEM_NAME},Linux>>:${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/packaging/debian_3rdparty/include>
  $<$<NOT:$<STREQUAL:${CMAKE_SYSTEM_NAME},Linux>>:${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/packaging/debian_3rdparty/include/eigen3>
)

# Performance and optimization macros
target_compile_definitions(essentia_rhythm_core PRIVATE
  NDEBUG                    # Ensure debug assertions are disabled
  EIGEN_NO_DEBUG           # Disable Eigen runtime checks
  EIGEN_DONT_PARALLELIZE   # Disable Eigen threading (we're single-threaded)
  EIGEN_FAST_MATH          # Enable fast math in Eigen
)
# If Essentia files expect certain macros, define them here as needed.
# target_compile_definitions(essentia_rhythm_core PRIVATE ESSENTIA_NO_AVCODEC)

# Section flags must be target-scoped to maximize --gc-sections effect
target_compile_options(essentia_rhythm_core PRIVATE
  -Wno-undefined-var-template
  "$<$<CONFIG:Release>:-ffunction-sections>"
  "$<$<CONFIG:Release>:-fdata-sections>"
)

# Link Eigen3 to the core library (only on Linux where we use system package)
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
  target_link_libraries(essentia_rhythm_core PUBLIC Eigen3::Eigen)
endif()

# Python extension
pybind11_add_module(_rhythmext src/bridge.cpp)
target_link_libraries(_rhythmext PRIVATE essentia_rhythm_core)

# Apply same optimizations to the Python module
target_compile_definitions(_rhythmext PRIVATE
  NDEBUG EIGEN_NO_DEBUG EIGEN_DONT_PARALLELIZE EIGEN_FAST_MATH
)
target_compile_options(_rhythmext PRIVATE
  -Wno-undefined-var-template
  "$<$<CONFIG:Release>:-ffunction-sections>"
  "$<$<CONFIG:Release>:-fdata-sections>"
)

# Ensure proper include directories for the Python module
target_include_directories(_rhythmext PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/src
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor/essentia/src/essentia
  ${NUMPY_INCLUDE_DIR}
)

# Install the Python module
install(TARGETS _rhythmext DESTINATION .)    