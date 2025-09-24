#!/bin/bash
CMD="rhythm-extractor testdata/drums_60s_mono.wav --algorithm rhythm2013"

hyperfine --warmup 3 \
          --runs 10 \
          --export-markdown benchmark.md \
          "$CMD"
