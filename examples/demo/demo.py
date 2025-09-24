#!/usr/bin/env python3
"""Demo script for rhythm extraction and metronome generation using es-rhythm-extractor."""

import argparse
import json
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


def quantize_onsets_to_beat_grid(onsets, beats):
    """Quantize onset times to the nearest beat grid positions."""
    if not onsets or len(beats) < 2:
        return []

    onset_times = onsets.get("onsets", [])
    if not onset_times.any():
        return []

    quantized_onsets = []

    # Calculate beat interval from first few beats for regular grid
    beat_intervals = np.diff(beats[: min(4, len(beats))])
    avg_beat_interval = np.mean(beat_intervals)

    # Create extended beat grid (before first beat and after last beat)
    first_beat = beats[0]
    last_beat = beats[-1]

    # Extend grid backwards
    grid_times = []
    t = first_beat
    while t > 0:
        t -= avg_beat_interval
        grid_times.append(t)
    grid_times.reverse()

    # Add actual beats
    grid_times.extend(beats)

    # Extend grid forwards
    t = last_beat
    audio_duration = (
        max(onset_times[-1] if onset_times.any() else 0, last_beat) + avg_beat_interval
    )
    while t < audio_duration:
        t += avg_beat_interval
        grid_times.append(t)

    grid_times = np.array(sorted(grid_times))

    # Quantize each onset to nearest grid point
    for onset_time in onset_times:
        distances = np.abs(grid_times - onset_time)
        nearest_idx = np.argmin(distances)
        nearest_beat_time = grid_times[nearest_idx]

        # Only quantize if onset is within reasonable distance (quarter beat)
        if distances[nearest_idx] < avg_beat_interval * 0.25:
            quantized_onsets.append(nearest_beat_time)

    # Remove duplicates and sort
    quantized_onsets = sorted(set(quantized_onsets))

    return quantized_onsets


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
    print(f"Found {len(onsets.get('onsets', []))} onsets")

    # Run RhythmExtractor2013
    print("Extracting rhythm...")
    rhythm_result = esrx.rhythm_extractor_2013(
        audio, sample_rate, method="multifeature"
    )

    bpm = rhythm_result["bpm"]
    beats = rhythm_result["ticks"]
    beats_confidence = rhythm_result["confidence"]
    beats_intervals = rhythm_result["bpm_estimates"]
    bpm_intervals = rhythm_result["bpm_intervals"]

    print(f"Detected BPM: {bpm:.2f}")
    print(f"Confidence: {beats_confidence:.2f}")
    print(f"Found {len(beats)} beats")

    # Quantize onsets to beat grid
    print("Quantizing onsets to beat grid...")
    quantized_onsets = quantize_onsets_to_beat_grid(onsets, beats)
    print(f"Quantized to {len(quantized_onsets)} grid positions")

    # Generate metronome track
    print("Generating metronome track...")

    # Create silent track of same length
    metronome = np.zeros_like(audio)

    # Generate click sounds
    strong_click = generate_click(
        sample_rate, duration=0.05, frequency=1000
    )  # Main beats
    weak_click = (
        generate_click(sample_rate, duration=0.03, frequency=800) * 0.6
    )  # Quantized onsets

    # Place strong clicks at main beat positions
    for beat_time in beats:
        sample_idx = int(beat_time * sample_rate)
        end_idx = min(sample_idx + len(strong_click), len(metronome))
        click_len = end_idx - sample_idx
        if click_len > 0:
            metronome[sample_idx:end_idx] += strong_click[:click_len]

    # Place weaker clicks at quantized onset positions (avoid overlapping with main beats)
    for onset_time in quantized_onsets:
        # Check if this onset is too close to a main beat
        min_distance = (
            min(abs(onset_time - beat) for beat in beats)
            if beats.any()
            else float("inf")
        )
        if min_distance > 0.05:  # More than 50ms away from nearest beat
            sample_idx = int(onset_time * sample_rate)
            end_idx = min(sample_idx + len(weak_click), len(metronome))
            click_len = end_idx - sample_idx
            if click_len > 0:
                metronome[sample_idx:end_idx] += weak_click[:click_len]

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

    # Save beat grid data to JSON
    json_file = output_file.replace(".wav", "_beat_grid.json")
    beat_grid_data = {
        "bpm": float(bpm),
        "beats": [float(t) for t in beats],
        "confidence": float(beats_confidence),
        "onsets": [float(t) for t in onsets.get("onsets", [])],
        "quantized_onsets": [float(t) for t in quantized_onsets],
        "beats_intervals": [float(x) for x in beats_intervals]
        if beats_intervals is not None
        else None,
        "bpm_intervals": [float(x) for x in bpm_intervals]
        if bpm_intervals is not None
        else None,
        "sample_rate": int(sample_rate),
        "audio_duration": float(len(audio) / sample_rate),
    }

    with open(json_file, "w") as f:
        json.dump(beat_grid_data, f, indent=2)
    print(f"Beat grid data written to: {json_file}")

    return {
        "bpm": bpm,
        "beats": beats,
        "confidence": beats_confidence,
        "onsets": onsets,
        "quantized_onsets": quantized_onsets,
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
            print(f"Number of onsets: {len(result['onsets'].get('onsets', []))}")
            print(f"Number of quantized onsets: {len(result['quantized_onsets'])}")
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
