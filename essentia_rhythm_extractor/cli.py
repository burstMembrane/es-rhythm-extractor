#!/usr/bin/env python3
"""
Thin CLI wrapper for Essentia Rhythm Extractor
"""

import argparse
import json
import sys
from pathlib import Path

import essentia_rhythm_extractor


def main():
    parser = argparse.ArgumentParser(description="Extract rhythm features from audio")
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument(
        "--algorithm",
        choices=["multifeature", "rhythm2013", "onset"],
        default="multifeature",
        help="Algorithm to use",
    )
    parser.add_argument("--min-tempo", type=int, default=40, help="Minimum tempo (BPM)")
    parser.add_argument(
        "--max-tempo", type=int, default=208, help="Maximum tempo (BPM)"
    )
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")

    args = parser.parse_args()

    print(f"Using algorithm: {args.algorithm}", file=sys.stderr)

    if not Path(args.audio_file).exists():
        print(f"Error: File {args.audio_file} not found", file=sys.stderr)
        return 1

    # Use file-based functions to avoid Python audio loading overhead
    if args.algorithm == "multifeature":
        result = essentia_rhythm_extractor.run_multifeature_from_file(
            args.audio_file, min_tempo=args.min_tempo, max_tempo=args.max_tempo
        )
    elif args.algorithm == "onset":
        result = essentia_rhythm_extractor.run_onset_detection_from_file(
            args.audio_file
        )
    else:
        result = essentia_rhythm_extractor.run_rhythm_extractor_2013_from_file(
            args.audio_file, min_tempo=args.min_tempo, max_tempo=args.max_tempo
        )

    # Convert arrays to lists for JSON serialization
    for key, value in result.items():
        if hasattr(value, "tolist"):
            result[key] = value.tolist()

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
    else:
        print(json.dumps(result, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
