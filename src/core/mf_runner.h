#pragma once
#include <cstddef>
#include <vector>
#include <string>

struct MFOut
{
  double bpm = 0.0;
  double confidence = 0.0; // ~0..5.32 for multifeature
  std::vector<double> ticks_sec;
  std::vector<double> bpm_estimates;
  std::vector<double> bpm_intervals_sec;
};

struct OnsetOut
{
  double onset_rate = 0.0;
  std::vector<double> onsets_sec;
};

/**
 * Run Essentia's multifeature beat tracker on mono 44.1kHz float PCM.
 * Implemented in mf_runner.cpp by wiring vendored Essentia classes.
 */
MFOut run_multifeature(const float *mono_44100, size_t n_samples,
                       int min_tempo_bpm, int max_tempo_bpm);

/**
 * Run Essentia's RhythmExtractor2013-style analysis with enhanced BPM calculation.
 * method: "multifeature" or "degara"
 */
MFOut run_rhythm_extractor_2013(const float *mono_44100, size_t n_samples,
                                 int min_tempo_bpm, int max_tempo_bpm, 
                                 const std::string& method = "multifeature");

/**
 * Run Essentia's OnsetRate algorithm on mono 44.1kHz float PCM.
 * Returns onset times and overall onset rate.
 */
OnsetOut run_onset_detection(const float *mono_44100, size_t n_samples);