# Import the compiled extension
from _rhythmext import rhythm_extractor_2013, rhythm_multifeature  # type: ignore

"""This module provides Python bindings for rhythm feature extraction
using the Essentia library's BeatTrackerMultiFeature and RhythmExtractor2013 algorithms.
The core functionality is implemented in C++ and exposed to Python via pybind11.
"""


def run_multifeature(x, sr, *, min_tempo=40, max_tempo=208):
    """
    RhythmMultiFeature analysis based on Essentia's BeatTrackerMultiFeature algorithm.
    extracted from Essentia C++ library.
    Args:
        x: mono float32 numpy array
        sr: sample rate (must be 44100.0)
    Returns:
        dict with keys: bpm, confidence, ticks, bpm_estimates, bpm_intervals
    """
    return rhythm_multifeature(x, float(sr), int(min_tempo), int(max_tempo))


def run_rhythm_extractor_2013(
    x, sr, *, min_tempo=40, max_tempo=208, method="multifeature"
):
    """
    RhythmExtractor2013 analysis with enhanced BPM calculation.
    based on Essentia's RhythmExtractor2013 algorithm.

    Args:
        x: mono float32 numpy array
        sr: sample rate (must be 44100.0)
        min_tempo: minimum tempo in BPM (default: 40)
        max_tempo: maximum tempo in BPM (default: 208)
        method: "multifeature" or "degara" (default: "multifeature")
    Returns:
        dict: bpm, confidence, ticks, bpm_estimates, bpm_intervals
    """
    return rhythm_extractor_2013(x, float(sr), int(min_tempo), int(max_tempo), method)
