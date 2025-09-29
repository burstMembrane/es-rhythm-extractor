"""Metronome generation from audio files using rhythm extraction."""

import json
from pathlib import Path
from typing import Dict, List, Optional


def _quantize_onsets_to_beat_grid(onsets, beats) -> List[float]:
    """Quantize onset times to the nearest beat grid positions."""
    import numpy as np

    # Handle case where onsets/beats might be numpy arrays
    if hasattr(onsets, "any"):
        if not onsets.any() or len(beats) < 2:
            return []
    else:
        if not len(onsets) or len(beats) < 2:
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
    # Handle numpy array check for onsets
    if hasattr(onsets, "any"):
        audio_duration = (
            max(onsets[-1] if onsets.any() else 0, last_beat) + avg_beat_interval
        )
    else:
        audio_duration = (
            max(onsets[-1] if len(onsets) > 0 else 0, last_beat) + avg_beat_interval
        )
    while t < audio_duration:
        t += avg_beat_interval
        grid_times.append(t)

    grid_times = np.array(sorted(grid_times))

    # Quantize each onset to nearest grid point
    for onset_time in onsets:
        distances = np.abs(grid_times - onset_time)
        nearest_idx = np.argmin(distances)
        nearest_beat_time = grid_times[nearest_idx]

        # Only quantize if onset is within reasonable distance (quarter beat)
        if distances[nearest_idx] < avg_beat_interval * 0.25:
            quantized_onsets.append(nearest_beat_time)

    # Remove duplicates and sort
    quantized_onsets = sorted(set(quantized_onsets))

    return quantized_onsets


def _generate_click_sound(
    sample_rate: int = 44100, duration: float = 0.05, frequency: int = 1000
) -> "np.ndarray":
    """Generate a click/beep sound."""
    import numpy as np

    t = np.linspace(0, duration, int(sample_rate * duration))
    # Create a sine wave with an exponential decay envelope
    envelope = np.exp(-35 * t)
    click = np.sin(2 * np.pi * frequency * t) * envelope
    return click.astype(np.float32)


def generate_metronome_from_file(
    input_file: str,
    output_dir: str,
    output_file: Optional[str] = None,
    create_mixed: bool = True,
    save_json: bool = True,
) -> Dict:
    """Generate a metronome track from audio file using rhythm extraction.

    Args:
        input_file: Path to input audio file
        output_dir: Directory to save output files (required)
        output_file: Filename for metronome WAV file (defaults to input_file stem + '_metronome.wav')
        create_mixed: Whether to create a mixed version with original audio (default: True)
        save_json: Whether to save beat grid data to JSON (default: True)

    Returns:
        Dict containing:
        - bpm: Detected BPM
        - beats: List of beat times in seconds
        - confidence: Beat detection confidence
        - onsets: Dict with onset detection results
        - quantized_onsets: List of quantized onset times
        - metronome_file: Path to generated metronome file
        - mixed_file: Path to mixed file (if create_mixed=True)
        - json_file: Path to JSON file (if save_json=True)
    """
    import numpy as np
    import soundfile as sf

    # Import the C++ functions
    from . import run_onset_detection_from_file, run_rhythm_extractor_2013_from_file

    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file '{input_file}' not found")

    # Create output directory if it doesn't exist
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Set output file path
    if output_file is None:
        output_file = f"{input_path.stem}_metronome.wav"

    output_file_path = output_dir_path / output_file

    # Run rhythm analysis using from_file methods
    print("Detecting onsets...")
    onsets = run_onset_detection_from_file(str(input_file))
    onset_times = onsets.get("onsets", [])
    print(f"Found {len(onset_times)} onsets")

    print("Extracting rhythm...")
    rhythm_result = run_rhythm_extractor_2013_from_file(
        str(input_file), method="multifeature"
    )

    bpm = rhythm_result["bpm"]
    beats = rhythm_result["ticks"]
    beats_confidence = rhythm_result["confidence"]
    beats_intervals = rhythm_result["bpm_estimates"]
    bpm_intervals = rhythm_result["bpm_intervals"]

    print(f"Detected BPM: {bpm:.2f}")
    print(f"Confidence: {beats_confidence:.2f}")
    print(f"Found {len(beats)} beats")

    # Load audio for metronome generation (we still need this for creating the output)
    audio, sample_rate = sf.read(input_file, always_2d=False)

    # Convert to mono if stereo
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    # Resample to 44100 Hz if necessary
    target_sr = 44100
    if sample_rate != target_sr:
        import soxr

        audio = soxr.resample(audio, sample_rate, target_sr)
        sample_rate = target_sr

    # Ensure float32
    audio = audio.astype(np.float32)

    # Quantize onsets to beat grid
    print("Quantizing onsets to beat grid...")
    quantized_onsets = _quantize_onsets_to_beat_grid(onset_times, beats)
    print(f"Quantized to {len(quantized_onsets)} grid positions")

    # Generate metronome track
    print("Generating metronome track...")

    # Create silent track of same length
    metronome = np.zeros_like(audio)

    # Generate click sounds
    strong_click = _generate_click_sound(
        sample_rate, duration=0.05, frequency=1000
    )  # Main beats
    weak_click = (
        _generate_click_sound(sample_rate, duration=0.03, frequency=800) * 0.6
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
        # Handle numpy array check for beats
        if hasattr(beats, "any"):
            min_distance = (
                min(abs(onset_time - beat) for beat in beats)
                if beats.any()
                else float("inf")
            )
        else:
            min_distance = (
                min(abs(onset_time - beat) for beat in beats)
                if len(beats) > 0
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

    # Write metronome output
    sf.write(str(output_file_path), metronome, sample_rate)
    print(f"Metronome track written to: {output_file_path}")

    result = {
        "bpm": bpm,
        "beats": beats,
        "confidence": beats_confidence,
        "onsets": onsets,
        "quantized_onsets": quantized_onsets,
        "beats_intervals": beats_intervals,
        "bpm_intervals": bpm_intervals,
        "metronome_file": str(output_file_path),
    }

    # Create mixed version if requested
    if create_mixed:
        mixed_filename = output_file.replace(".wav", "_mixed.wav")
        mixed_file_path = output_dir_path / mixed_filename
        mixed = audio * 0.3 + metronome * 0.7  # Mix original (quieter) with metronome
        max_val = np.abs(mixed).max()
        if max_val > 0:
            mixed = mixed / max_val * 0.8
        sf.write(str(mixed_file_path), mixed, sample_rate)
        print(f"Mixed track written to: {mixed_file_path}")
        result["mixed_file"] = str(mixed_file_path)

    # Save JSON data if requested
    if save_json:
        json_filename = output_file.replace(".wav", "_beat_grid.json")
        json_file_path = output_dir_path / json_filename
        beat_grid_data = {
            "bpm": float(bpm),
            "beats": [float(t) for t in beats],
            "confidence": float(beats_confidence),
            "onsets": [float(t) for t in onset_times],
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

        with open(json_file_path, "w") as f:
            json.dump(beat_grid_data, f, indent=2)
        print(f"Beat grid data written to: {json_file_path}")
        result["json_file"] = str(json_file_path)

    return result
