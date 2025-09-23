#include "mf_runner.h"
#include "vendor/essentia/src/essentia/essentia.h"
#include "vendor/essentia/src/essentia/algorithmfactory.h"
#include "vendor/essentia/src/essentia/streaming/algorithms/poolstorage.h"
#include "vendor/essentia/src/essentia/streaming/algorithms/vectorinput.h"
#include "vendor/essentia/src/essentia/scheduler/network.h"
#include "vendor/essentia/src/essentia/essentiamath.h"

using namespace std;
using namespace essentia;
using namespace essentia::streaming;
using namespace essentia::scheduler;

// Global initialization - only happens once per process
static bool essentia_initialized = false;
static void ensure_essentia_initialized() {
    if (!essentia_initialized) {
        essentia::init();
        essentia_initialized = true;
    }
}

MFOut run_multifeature(const float *mono_44100, size_t n_samples,
                       int min_tempo_bpm, int max_tempo_bpm)
{
    ensure_essentia_initialized();
    MFOut out;

    try {
        // Use streaming factory approach like in the example
        streaming::AlgorithmFactory& factory = streaming::AlgorithmFactory::instance();
        
        Pool pool;
        
        // Create a VectorInput to feed our audio data
        VectorInput<Real>* vectorInput = new VectorInput<Real>();
        Algorithm* beattracker = factory.create("BeatTrackerMultiFeature");
        
        // Connect algorithms like in the example
        *vectorInput >> beattracker->input("signal");
        beattracker->output("ticks") >> PC(pool, "rhythm.ticks");
        beattracker->output("confidence") >> PC(pool, "rhythm.confidence");
        
        // Convert input to vector<Real> and set it
        vector<Real> signal(mono_44100, mono_44100 + n_samples);
        vectorInput->setVector(&signal);
        
        // Create and run network
        Network network(vectorInput);
        network.run();
        
        // Extract results from pool
        vector<Real> ticks;
        Real confidence = 0.0;
        
        if (pool.contains<vector<Real>>("rhythm.ticks")) {
            ticks = pool.value<vector<Real>>("rhythm.ticks");
        }
        if (pool.contains<Real>("rhythm.confidence")) {
            confidence = pool.value<Real>("rhythm.confidence");
        }

        // Calculate BPM from ticks (like RhythmExtractor2013 does)
        Real bpm = 0.0;
        vector<Real> bpmIntervals;
        vector<Real> estimates;

        if (ticks.size() > 1) {
            // Calculate intervals between beats
            bpmIntervals.reserve(ticks.size() - 1);
            for (size_t i = 1; i < ticks.size(); i++) {
                bpmIntervals.push_back(ticks[i] - ticks[i - 1]);
                estimates.push_back(60.0 / bpmIntervals.back()); // period to bpm
            }

            // Calculate mean BPM
            if (!estimates.empty()) {
                Real sum = 0;
                for (size_t i = 0; i < estimates.size(); i++) {
                    sum += estimates[i];
                }
                bpm = sum / estimates.size();
            }
        }

        // Copy results to output structure
        out.bpm = bpm;
        out.confidence = confidence;
        out.ticks_sec = vector<double>(ticks.begin(), ticks.end());
        out.bpm_estimates = vector<double>(estimates.begin(), estimates.end());
        out.bpm_intervals_sec = vector<double>(bpmIntervals.begin(), bpmIntervals.end());

    }
    catch (const exception &e) {
        // Return empty results on error - could optionally log to stderr or throw
    }

    return out;
}

// Helper function for sophisticated BPM calculation (from RhythmExtractor2013)
static void calculateBpmRhythmExtractor2013Style(const vector<Real>& ticks, 
                                                  Real& bpm, 
                                                  vector<Real>& estimates,
                                                  vector<Real>& bpmIntervals) {
    bpm = 0.0;
    estimates.clear();
    bpmIntervals.clear();
    
    if (ticks.size() <= 1) return;
    
    // Calculate intervals between beats
    vector<Real> bpmEstimateList;
    bpmIntervals.reserve(ticks.size() - 1);
    bpmEstimateList.reserve(bpmIntervals.size());
    
    for (size_t i = 1; i < ticks.size(); i++) {
        bpmIntervals.push_back(ticks[i] - ticks[i-1]);
        bpmEstimateList.push_back(60.0 / bpmIntervals.back()); // period to bpm
    }
    
    if (bpmEstimateList.empty()) return;
    
    // Apply RhythmExtractor2013's sophisticated BPM estimation
    const Real periodTolerance = 5.0; // Same as RhythmExtractor2013
    
    Real closestBpm = 0;
    vector<Real> countedBins;
    
    // Divide by 2 for tempo multiple handling
    for (size_t i = 0; i < bpmEstimateList.size(); ++i) {
        bpmEstimateList[i] /= 2.0;
    }
    
    // Use bincount to find histogram 
    bincount(bpmEstimateList, countedBins);
    
    // Find the bin with maximum count
    closestBpm = argmax(countedBins) * 2.0;
    
    // Restore original values and filter by period tolerance
    for (size_t i = 0; i < bpmEstimateList.size(); ++i) {
        bpmEstimateList[i] *= 2.0;
        if (abs(closestBpm - bpmEstimateList[i]) < periodTolerance) {
            estimates.push_back(bpmEstimateList[i]);
        }
    }
    
    if (estimates.empty()) {
        // Something odd happened, use closest BPM
        bpm = closestBpm;
    } else {
        // Calculate mean of filtered estimates
        bpm = mean(estimates);
    }
}

MFOut run_rhythm_extractor_2013(const float *mono_44100, size_t n_samples,
                                 int min_tempo_bpm, int max_tempo_bpm, 
                                 const std::string& method) {
    ensure_essentia_initialized();
    MFOut out;

    try {
        // Use streaming factory approach like in the example
        streaming::AlgorithmFactory& factory = streaming::AlgorithmFactory::instance();
        
        Pool pool;
        
        // Create a VectorInput to feed our audio data
        VectorInput<Real>* vectorInput = new VectorInput<Real>();
        Algorithm* beattracker;
        
        // Choose algorithm based on method
        if (method == "degara") {
            beattracker = factory.create("BeatTrackerDegara");
        } else {
            // Default to multifeature
            beattracker = factory.create("BeatTrackerMultiFeature");
        }
        
        // Configure the beat tracker with tempo parameters
        beattracker->configure("minTempo", min_tempo_bpm, "maxTempo", max_tempo_bpm);
        
        // Connect algorithms like in the example
        *vectorInput >> beattracker->input("signal");
        beattracker->output("ticks") >> PC(pool, "rhythm.ticks");
        
        // Only BeatTrackerMultiFeature has confidence output
        if (method != "degara") {
            beattracker->output("confidence") >> PC(pool, "rhythm.confidence");
        }
        
        // Convert input to vector<Real> and set it
        vector<Real> signal(mono_44100, mono_44100 + n_samples);
        vectorInput->setVector(&signal);
        
        // Create and run network
        Network network(vectorInput);
        network.run();
        
        // Extract results from pool
        vector<Real> ticks;
        Real confidence = 0.0;
        
        if (pool.contains<vector<Real>>("rhythm.ticks")) {
            ticks = pool.value<vector<Real>>("rhythm.ticks");
        }
        if (pool.contains<Real>("rhythm.confidence")) {
            confidence = pool.value<Real>("rhythm.confidence");
        }

        // Use sophisticated BPM calculation (RhythmExtractor2013 style)
        Real bpm;
        vector<Real> estimates;
        vector<Real> bpmIntervals;
        calculateBpmRhythmExtractor2013Style(ticks, bpm, estimates, bpmIntervals);

        // Copy results to output structure
        out.bpm = bpm;
        out.confidence = confidence;
        out.ticks_sec = vector<double>(ticks.begin(), ticks.end());
        out.bpm_estimates = vector<double>(estimates.begin(), estimates.end());
        out.bpm_intervals_sec = vector<double>(bpmIntervals.begin(), bpmIntervals.end());

    }
    catch (const exception &e) {
        // Return empty results on error - could optionally log to stderr or throw
    }

    return out;
}

OnsetOut run_onset_detection(const float *mono_44100, size_t n_samples)
{
    ensure_essentia_initialized();
    OnsetOut out;

    try {
        // Use standard factory approach like in the original onset_detector.cpp
        standard::AlgorithmFactory& factory = standard::AlgorithmFactory::instance();
        
        // Convert input to vector<Real>
        vector<Real> signal(mono_44100, mono_44100 + n_samples);
        
        // Create OnsetRate algorithm
        standard::Algorithm* onsetRate = factory.create("OnsetRate");
        
        // Configure the algorithm (important!)
        onsetRate->configure();
        
        // Set up inputs and outputs
        vector<Real> onsets;
        Real onsetRateValue = 0.0;
        
        onsetRate->input("signal").set(signal);
        onsetRate->output("onsets").set(onsets);
        onsetRate->output("onsetRate").set(onsetRateValue);
        
        // Compute
        onsetRate->compute();
        
        // Copy results to output structure
        out.onset_rate = onsetRateValue;
        out.onsets_sec = vector<double>(onsets.begin(), onsets.end());
        
        // Debug output
        std::cerr << "Debug: signal size=" << signal.size() 
                  << ", onsetRate=" << onsetRateValue 
                  << ", onsets count=" << onsets.size() << std::endl;
        
        // Clean up
        delete onsetRate;
        
    }
    catch (const exception &e) {
        // Return empty results on error - could log the error for debugging
        std::cerr << "OnsetRate error: " << e.what() << std::endl;
    }

    return out;
}