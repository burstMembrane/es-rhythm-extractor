# Import the compiled extension
from _rhythmext import rhythm_extractor_2013, rhythm_multifeature, onset_detection  # type: ignore

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


def run_onset_detection(x, sr):
    """
    Onset detection analysis using Essentia's OnsetRate algorithm.
    
    Args:
        x: mono float32 numpy array
        sr: sample rate (must be 44100.0)
    Returns:
        dict with keys: onset_rate, onsets
            - onset_rate: number of onsets per second
            - onsets: array of onset times in seconds
    """
    return onset_detection(x, float(sr))


# File-based functions for better performance (no Python audio loading)
def run_multifeature_from_file(filename, *, min_tempo=40, max_tempo=208):
    """
    RhythmMultiFeature analysis from file using Essentia's MonoLoader.
    Args:
        filename: path to audio file
        min_tempo: minimum tempo in BPM (default: 40)
        max_tempo: maximum tempo in BPM (default: 208)
    Returns:
        dict with keys: bpm, confidence, ticks, bpm_estimates, bpm_intervals
    """
    from _rhythmext import rhythm_multifeature_from_file  # type: ignore
    return rhythm_multifeature_from_file(filename, int(min_tempo), int(max_tempo))


def run_rhythm_extractor_2013_from_file(filename, *, min_tempo=40, max_tempo=208, method="multifeature"):
    """
    RhythmExtractor2013 analysis from file using Essentia's MonoLoader.
    Args:
        filename: path to audio file
        min_tempo: minimum tempo in BPM (default: 40)
        max_tempo: maximum tempo in BPM (default: 208)
        method: "multifeature" or "degara" (default: "multifeature")
    Returns:
        dict: bpm, confidence, ticks, bpm_estimates, bpm_intervals
    """
    from _rhythmext import rhythm_extractor_2013_from_file  # type: ignore
    return rhythm_extractor_2013_from_file(filename, int(min_tempo), int(max_tempo), method)


def run_onset_detection_from_file(filename):
    """
    Onset detection analysis from file using Essentia's MonoLoader.
    Args:
        filename: path to audio file
    Returns:
        dict with keys: onset_rate, onsets
            - onset_rate: number of onsets per second
            - onsets: array of onset times in seconds
    """
    from _rhythmext import onset_detection_from_file  # type: ignore
    return onset_detection_from_file(filename)


# High-level metronome generation function
from .metronome import generate_metronome_from_file
