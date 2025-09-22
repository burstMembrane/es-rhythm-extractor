"""
Test suite comparing our implementation against official Essentia.
"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path

# Test if essentia is available for comparison
try:
    import essentia.standard as es
    ESSENTIA_AVAILABLE = True
except ImportError:
    ESSENTIA_AVAILABLE = False

import essentia_rhythm_extractor as ere


def generate_white_noise_burst(duration_seconds: float, sample_rate: int = 44100, 
                              burst_duration: float = 0.1, burst_interval: float = 0.5,
                              amplitude: float = 0.5) -> np.ndarray:
    """
    Generate audio with short bursts of white noise at regular intervals.
    This creates a rhythmic pattern that should be detectable by beat tracking.
    
    Args:
        duration_seconds: Total duration of audio
        sample_rate: Sample rate (default 44100)
        burst_duration: Duration of each noise burst in seconds
        burst_interval: Interval between burst starts in seconds
        amplitude: Amplitude of noise bursts (0-1)
    
    Returns:
        numpy array of generated audio
    """
    total_samples = int(duration_seconds * sample_rate)
    audio = np.zeros(total_samples, dtype=np.float32)
    
    burst_samples = int(burst_duration * sample_rate)
    interval_samples = int(burst_interval * sample_rate)
    
    # Generate bursts at regular intervals
    current_pos = 0
    while current_pos + burst_samples < total_samples:
        # Generate white noise burst
        noise = np.random.uniform(-amplitude, amplitude, burst_samples).astype(np.float32)
        audio[current_pos:current_pos + burst_samples] = noise
        current_pos += interval_samples
    
    return audio


def generate_sine_wave_beats(duration_seconds: float, bpm: float, sample_rate: int = 44100,
                           beat_duration: float = 0.05, amplitude: float = 0.5) -> np.ndarray:
    """
    Generate audio with sine wave beats at a specific BPM.
    
    Args:
        duration_seconds: Total duration of audio
        bpm: Beats per minute
        sample_rate: Sample rate (default 44100)
        beat_duration: Duration of each beat in seconds
        amplitude: Amplitude of beats (0-1)
    
    Returns:
        numpy array of generated audio
    """
    total_samples = int(duration_seconds * sample_rate)
    audio = np.zeros(total_samples, dtype=np.float32)
    
    beat_interval = 60.0 / bpm  # seconds between beats
    beat_samples = int(beat_duration * sample_rate)
    interval_samples = int(beat_interval * sample_rate)
    
    # Generate beats at BPM intervals
    current_pos = 0
    while current_pos + beat_samples < total_samples:
        # Generate sine wave beat (440 Hz)
        t = np.linspace(0, beat_duration, beat_samples)
        beat = amplitude * np.sin(2 * np.pi * 440 * t).astype(np.float32)
        audio[current_pos:current_pos + beat_samples] = beat
        current_pos += interval_samples
    
    return audio


# Helper functions

def run_our_implementation(audio: np.ndarray) -> dict:
    """Run our rhythm extraction implementation."""
    result = ere.run_rhythm_extractor_2013(audio, 44100.0, method="multifeature")
    return {
        'bpm': result['bpm'],
        'beats': result['ticks'],
        'confidence': result.get('confidence', 0.0)
    }


def run_official_implementation(audio: np.ndarray) -> dict:
    """Run official Essentia implementation."""
    rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
    bpm, beats, beats_confidence, _, beats_intervals = rhythm_extractor(audio)
    
    return {
        'bpm': bpm,
        'beats': beats,
        'confidence': beats_confidence
    }


def assert_similar_results(our_result: dict, official_result: dict, 
                          bpm_tolerance: float = 2.0, beat_tolerance: float = 0.1):
    """Assert that our results are similar to official results."""
    # BPM comparison
    bpm_diff = abs(our_result['bpm'] - official_result['bpm'])
    assert bpm_diff <= bpm_tolerance, f"BPM difference {bpm_diff:.2f} > tolerance {bpm_tolerance}"
    
    # Beat count comparison (allow some variation)
    beat_count_diff = abs(len(our_result['beats']) - len(official_result['beats']))
    max_beat_diff = max(2, int(0.1 * len(official_result['beats'])))  # 10% or at least 2
    assert beat_count_diff <= max_beat_diff, f"Beat count difference {beat_count_diff} > tolerance {max_beat_diff}"
    
    # Beat timing comparison (for overlapping beats)
    min_beats = min(len(our_result['beats']), len(official_result['beats']), 10)
    if min_beats > 0:
        for i in range(min_beats):
            timing_diff = abs(our_result['beats'][i] - official_result['beats'][i])
            assert timing_diff <= beat_tolerance, f"Beat {i} timing difference {timing_diff:.3f} > tolerance {beat_tolerance}"


# Tests

def test_our_implementation_basic():
    """Test that our implementation runs without errors on generated audio."""
    # Generate simple test audio
    audio = generate_white_noise_burst(duration_seconds=5.0, burst_interval=0.5)
    
    # Run our implementation
    result = run_our_implementation(audio)
    
    # Basic sanity checks
    assert isinstance(result['bpm'], (int, float))
    assert result['bpm'] > 0
    assert isinstance(result['beats'], np.ndarray)
    assert len(result['beats']) >= 0
    assert isinstance(result['confidence'], (int, float))
    
    print(f"Our implementation - BPM: {result['bpm']:.2f}, Beats: {len(result['beats'])}")


@pytest.mark.skipif(not ESSENTIA_AVAILABLE, reason="Official Essentia not available")
def test_white_noise_bursts_comparison():
    """Compare implementations on white noise bursts."""
    # Generate rhythmic white noise (120 BPM = 0.5s intervals)
    audio = generate_white_noise_burst(
        duration_seconds=10.0, 
        burst_interval=0.5,  # 120 BPM
        burst_duration=0.1,
        amplitude=0.7
    )
    
    # Run both implementations
    our_result = run_our_implementation(audio)
    official_result = run_official_implementation(audio)
    
    print(f"White noise bursts - Our: {our_result['bpm']:.2f} BPM, {len(our_result['beats'])} beats")
    print(f"White noise bursts - Official: {official_result['bpm']:.2f} BPM, {len(official_result['beats'])} beats")
    
    # Assert similarity (more lenient for generated audio)
    assert_similar_results(our_result, official_result, bpm_tolerance=5.0, beat_tolerance=0.2)


@pytest.mark.skipif(not ESSENTIA_AVAILABLE, reason="Official Essentia not available")
def test_sine_wave_beats_comparison():
    """Compare implementations on sine wave beats."""
    # Generate sine wave beats at 140 BPM
    target_bpm = 140
    audio = generate_sine_wave_beats(
        duration_seconds=8.0,
        bpm=target_bpm,
        beat_duration=0.05,
        amplitude=0.8
    )
    
    # Run both implementations
    our_result = run_our_implementation(audio)
    official_result = run_official_implementation(audio)
    
    print(f"Sine beats ({target_bpm} BPM) - Our: {our_result['bpm']:.2f} BPM, {len(our_result['beats'])} beats")
    print(f"Sine beats ({target_bpm} BPM) - Official: {official_result['bpm']:.2f} BPM, {len(official_result['beats'])} beats")
    
    # Assert similarity
    assert_similar_results(our_result, official_result, bpm_tolerance=3.0, beat_tolerance=0.15)


@pytest.mark.skipif(not ESSENTIA_AVAILABLE, reason="Official Essentia not available")  
def test_multiple_bpm_values():
    """Test comparison across multiple BPM values."""
    test_bpms = [80, 120, 140, 160]
    
    for target_bpm in test_bpms:
        # Generate audio for this BPM
        audio = generate_sine_wave_beats(
            duration_seconds=6.0,
            bpm=target_bpm,
            beat_duration=0.04,
            amplitude=0.6
        )
        
        # Run both implementations
        our_result = run_our_implementation(audio)
        official_result = run_official_implementation(audio)
        
        print(f"BPM {target_bpm} - Our: {our_result['bpm']:.1f}, Official: {official_result['bpm']:.1f}")
        
        # Assert similarity (allowing more tolerance for generated audio)
        assert_similar_results(our_result, official_result, bpm_tolerance=8.0, beat_tolerance=0.2)


def test_edge_cases():
    """Test edge cases with our implementation."""
    # Test very short audio
    short_audio = generate_white_noise_burst(duration_seconds=1.0, burst_interval=0.25)
    result = run_our_implementation(short_audio)
    assert result['bpm'] >= 0
    
    # Test silence
    silence = np.zeros(44100 * 3, dtype=np.float32)  # 3 seconds of silence
    result = run_our_implementation(silence)
    assert result['bpm'] >= 0
    
    # Test very loud audio
    loud_audio = generate_white_noise_burst(duration_seconds=3.0, amplitude=0.9, burst_interval=0.4)
    result = run_our_implementation(loud_audio)
    assert result['bpm'] >= 0
    
    print("Edge cases passed")


@pytest.mark.skipif(not ESSENTIA_AVAILABLE, reason="Official Essentia not available")
def test_real_audio_file_if_exists():
    """Test comparison on real audio file if it exists."""
    test_file = Path("testdata/drums2.wav")
    if not test_file.exists():
        pytest.skip("Real test audio file not found")
    
    # Load audio using Essentia
    loader = es.MonoLoader(filename=str(test_file))
    audio = loader()
    
    # Run both implementations
    our_result = run_our_implementation(audio)
    official_result = run_official_implementation(audio)
    
    print(f"Real audio - Our: {our_result['bpm']:.2f} BPM, {len(our_result['beats'])} beats")
    print(f"Real audio - Official: {official_result['bpm']:.2f} BPM, {len(official_result['beats'])} beats")
    
    # Should be very close for real audio
    assert_similar_results(our_result, official_result, bpm_tolerance=0.1, beat_tolerance=0.01)


if __name__ == "__main__":
    # Run a quick test if called directly
    test_our_implementation_basic()
    
    if ESSENTIA_AVAILABLE:
        test_white_noise_bursts_comparison()
        print("Comparison tests completed successfully!")
    else:
        print("Official Essentia not available - only basic tests completed")