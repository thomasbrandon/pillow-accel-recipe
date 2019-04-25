#!/usr/bin/env bash
accel=$1
[[ $# = 1 ]] || { echo "No acceleration specified. Usage: $0 <accel>."; exit 1; }

if [[ $accel = 'avx512' ]]; then
  # Only AVX512 arch in gcc 7.3.0 used by conda
  march='skylake-avx512'
  mtune='skylake-avx512'
elif [[ $accel = 'avx2' ]]; then
  march='core-avx2'
  mtune='skylake'
elif [[ $accel = 'sse4' ]]; then
  march='nehalem'
  mtune='ivybridge'
else
    echo "Unknown acceleration: ${accel}"
    exit 1
fi
echo "Building with acceleration for ${accel}: march=${march}; mtune=${mtune}."
export CFLAGS="${CFLAGS/-march=* / }"
export CFLAGS="${CFLAGS/-mtune=* / }"
export CFLAGS="${CFLAGS} -march=${march} -mtune=${mtune}"
# --disable platform-guessing is a pillow-simd option that stops it guessing system
# include directories on linux.
# --old-and-unmanageable stops setuptools creating an egg which causes a conda build warning
python setup.py build_ext --disable-platform-guessing install --old-and-unmanageable
