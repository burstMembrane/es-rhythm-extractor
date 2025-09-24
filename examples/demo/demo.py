#!/usr/bin/env python3
"""Demo script for rhythm extraction and metronome generation using es-rhythm-extractor."""

import argparse
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import soxr

# Add parent directory to path to import the library
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import essentia_rhythm_extractor as esrx


def generate_click(sample_rate=44100, duration=0.05, frequency=1000):
    """Generate a click/beep sound."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    # Create a sine wave with an exponential decay envelope
    envelope = np.exp(-35 * t)
    click = np.sin(2 * np.pi * frequency * t) * envelope
    return click.astype(np.float32)


def generate_metronome(input_file, output_file="metronome.wav"):
    """Generate a metronome track from audio file beat detection."""
    # Load audio file
    audio, sample_rate = sf.read(input_file, always_2d=False)

    # Convert to mono if stereo
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    # Resample to 44100 Hz if necessary (common for rhythm analysis)
    target_sr = 44100
    if sample_rate != target_sr:
        audio = soxr.resample(audio, sample_rate, target_sr)
        sample_rate = target_sr

    # Ensure float32
    audio = audio.astype(np.float32)

    # Detect onsets
    print("Detecting onsets...")
    onsets = esrx.onset_detection(audio, sample_rate)
    # onset_rate, onsets
    print(onsets)

    # Run RhythmExtractor2013
    print("Extracting rhythm...")
    rhythm_result = esrx.rhythm_extractor_2013(
        audio, sample_rate, method="multifeature"
    )
    print(rhythm_result.keys())
    # ['bpm', 'confidence', 'ticks', 'bpm_estimates', 'bpm_intervals']

    bpm = rhythm_result["bpm"]
    beats = rhythm_result["ticks"]
    beats_confidence = rhythm_result["confidence"]
    beats_intervals = rhythm_result["bpm_estimates"]
    bpm_intervals = rhythm_result["bpm_intervals"]

    print(f"Detected BPM: {bpm:.2f}")
    print(f"Confidence: {beats_confidence:.2f}")
    print(f"Found {len(beats)} beats")

    # Generate metronome track
    print("Generating metronome track...")

    # Create silent track of same length
    metronome = np.zeros_like(audio)

    # Generate click sound
    click = generate_click(sample_rate)

    # Place clicks at beat positions
    for beat_time in beats:
        # Convert time to sample index
        sample_idx = int(beat_time * sample_rate)
        # Add click to metronome track (with bounds checking)
        end_idx = min(sample_idx + len(click), len(metronome))
        click_len = end_idx - sample_idx
        if click_len > 0:
            metronome[sample_idx:end_idx] += click[:click_len]

    # Also add softer clicks at onsets (optional)
    if len(onsets) > 0:
        soft_click = generate_click(sample_rate, duration=0.02, frequency=800) * 0.3
        for onset_time in onsets.get("onsets", []):
            sample_idx = int(onset_time * sample_rate)
            end_idx = min(sample_idx + len(soft_click), len(metronome))
            click_len = end_idx - sample_idx
            if click_len > 0:
                # Only add if not too close to a beat
                min_distance = (
                    min(abs(onset_time - beat) for beat in beats)
                    if len(beats) > 0
                    else float("inf")
                )
                if min_distance > 0.05:  # More than 50ms away from nearest beat
                    metronome[sample_idx:end_idx] += soft_click[:click_len]

    # Normalize to prevent clipping
    max_val = np.abs(metronome).max()
    if max_val > 0:
        metronome = metronome / max_val * 0.8

    # Write output
    sf.write(output_file, metronome, sample_rate)
    print(f"Metronome track written to: {output_file}")

    # Also create a version with original audio mixed in
    mixed_file = output_file.replace(".wav", "_mixed.wav")
    mixed = audio * 0.3 + metronome * 0.7  # Mix original (quieter) with metronome
    max_val = np.abs(mixed).max()
    if max_val > 0:
        mixed = mixed / max_val * 0.8
    sf.write(mixed_file, mixed, sample_rate)
    print(f"Mixed track written to: {mixed_file}")

    return {
        "bpm": bpm,
        "beats": beats,
        "confidence": beats_confidence,
        "onsets": onsets,
        "beats_intervals": beats_intervals,
        "bpm_intervals": bpm_intervals,
    }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate metronome from audio file using onset and beat detection"
    )
    parser.add_argument("input_file", help="Input audio file path")
    parser.add_argument(
        "-o",
        "--output",
        default="metronome.wav",
        help="Output audio file path (default: metronome.wav)",
    )
    parser.add_argument(
        "--show-stats",
        action="store_true",
        help="Show detailed statistics about detected beats and onsets",
    )

    args = parser.parse_args()

    # Check if input file exists
    if not Path(args.input_file).exists():
        print(f"Error: Input file '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)

    try:
        result = generate_metronome(args.input_file, args.output)

        if args.show_stats:
            print("\n=== Detailed Statistics ===")
            print(f"BPM: {result['bpm']:.2f}")
            print(f"Confidence: {result['confidence']:.3f}")
            print(f"Number of beats: {len(result['beats'])}")
            print(f"Number of onsets: {len(result['onsets'])}")
            if len(result["beats"]) > 1:
                beat_intervals = np.diff(result["beats"])
                print(f"Mean beat interval: {np.mean(beat_intervals):.3f}s")
                print(f"Std beat interval: {np.std(beat_intervals):.3f}s")
            print(f"BPM estimates: {result['bpm_intervals']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
