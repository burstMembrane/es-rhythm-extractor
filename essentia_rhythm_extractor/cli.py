#!/usr/bin/env python3
"""
Thin CLI wrapper for Essentia Rhythm Extractor
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import soxr

import essentia_rhythm_extractor


def load_audio(file_path):
    """Load and preprocess audio to mono 44100Hz float32."""
    audio, sr = sf.read(file_path, always_2d=False)
    # Convert to mono if stereo
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    # Resample to 44100Hz if needed
    if sr != 44100:
        audio = soxr.resample(audio, sr, 44100)
    return np.ascontiguousarray(audio, dtype=np.float32)


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

    if not Path(args.audio_file).exists():
        print(f"Error: File {args.audio_file} not found", file=sys.stderr)
        return 1

    try:
        audio = load_audio(args.audio_file)
        if args.algorithm == "multifeature":
            result = essentia_rhythm_extractor.run_multifeature(
                audio, 44100, min_tempo=args.min_tempo, max_tempo=args.max_tempo
            )
        elif args.algorithm == "onset":
            result = essentia_rhythm_extractor.run_onset_detection(audio, 44100)
        else:
            result = essentia_rhythm_extractor.run_rhythm_extractor_2013(
                audio, 44100, min_tempo=args.min_tempo, max_tempo=args.max_tempo
            )

        # Convert numpy arrays to lists for JSON serialization
        for key, value in result.items():
            if isinstance(value, np.ndarray):
                result[key] = value.tolist()

        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
        else:
            print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
