#include "essentia/algorithmfactory.h"

// --- Standard Algorithms ---
#include "algorithms/standard/framecutter.h"
#include "algorithms/standard/windowing.h"
#include "algorithms/standard/fftk.h"
#include "algorithms/standard/ifftk.h"
#include "algorithms/standard/scale.h"
#include "algorithms/standard/noiseadder.h"
#include "algorithms/standard/autocorrelation.h"
#include "algorithms/standard/spectrum.h"

// --- Rhythm Algorithms ---
#include "algorithms/rhythm/beattrackermultifeature.h"
#include "algorithms/rhythm/beattrackerdegara.h"
#include "algorithms/rhythm/onsetdetection.h"
#include "algorithms/rhythm/onsetrate.h"
#include "algorithms/rhythm/onsets.h"
#include "algorithms/rhythm/onsetdetectionglobal.h"
#include "algorithms/rhythm/tempotapdegara.h"
#include "algorithms/rhythm/tempotapmaxagreement.h"

// --- Spectral Algorithms ---
#include "algorithms/spectral/hfc.h"
#include "algorithms/spectral/flux.h"
#include "algorithms/spectral/melbands.h"
#include "algorithms/spectral/triangularbands.h"
#include "algorithms/spectral/erbbands.h"

// --- Filters ---
#include "algorithms/filters/movingaverage.h"
#include "algorithms/filters/iir.h"

// --- Complex Domain Algorithms ---
#include "algorithms/complex/cartesiantopolar.h"
#include "algorithms/complex/magnitude.h"

// Algorithm registration functions following Essentia's pattern
namespace essentia
{
  namespace standard
  {
    void registerAlgorithm()
    {
      AlgorithmFactory::Registrar<BeatTrackerMultiFeature> regBeatTrackerMultiFeature;
      AlgorithmFactory::Registrar<BeatTrackerDegara> regBeatTrackerDegara;
      AlgorithmFactory::Registrar<TempoTapMaxAgreement> regTempoTapMaxAgreement;
      AlgorithmFactory::Registrar<FrameCutter> regFrameCutter;
      AlgorithmFactory::Registrar<Windowing> regWindowing;
      AlgorithmFactory::Registrar<FFTK> regFFTK;
      AlgorithmFactory::Registrar<IFFTK> regIFFT;
      AlgorithmFactory::Registrar<CartesianToPolar> regCartesianToPolar;
      AlgorithmFactory::Registrar<OnsetDetection> regOnsetDetection;
      AlgorithmFactory::Registrar<OnsetDetectionGlobal> regOnsetDetectionGlobal;
      AlgorithmFactory::Registrar<OnsetRate> regOnsetRate;
      AlgorithmFactory::Registrar<Onsets> regOnsets;
      AlgorithmFactory::Registrar<TempoTapDegara> regTempoTapDegara;
      AlgorithmFactory::Registrar<Scale> regScale;
      AlgorithmFactory::Registrar<NoiseAdder> regNoiseAdder;
      AlgorithmFactory::Registrar<HFC> regHFC;
      AlgorithmFactory::Registrar<Flux> regFlux;
      AlgorithmFactory::Registrar<MelBands> regMelBands;
      AlgorithmFactory::Registrar<TriangularBands> regTriangularBands;
      AlgorithmFactory::Registrar<MovingAverage> regMovingAverage;
      AlgorithmFactory::Registrar<IIR> regIIR;
      AlgorithmFactory::Registrar<AutoCorrelation> regAutocorrelation;
      AlgorithmFactory::Registrar<Spectrum> regSpectrum;
      AlgorithmFactory::Registrar<Magnitude> regMagnitude;
      AlgorithmFactory::Registrar<ERBBands> regERBBands;
    }
  }
  namespace streaming
  {
    void registerAlgorithm()
    {
      AlgorithmFactory::Registrar<BeatTrackerMultiFeature, essentia::standard::BeatTrackerMultiFeature> regBeatTrackerMultiFeature;
      AlgorithmFactory::Registrar<BeatTrackerDegara, essentia::standard::BeatTrackerDegara> regBeatTrackerDegara;
      AlgorithmFactory::Registrar<FrameCutter, essentia::standard::FrameCutter> regFrameCutter;
      AlgorithmFactory::Registrar<Windowing, essentia::standard::Windowing> regWindowing;
      AlgorithmFactory::Registrar<FFTK, essentia::standard::FFTK> regFFTK;
      AlgorithmFactory::Registrar<CartesianToPolar, essentia::standard::CartesianToPolar> regCartesianToPolar;
      AlgorithmFactory::Registrar<OnsetDetection, essentia::standard::OnsetDetection> regOnsetDetection;
      AlgorithmFactory::Registrar<OnsetDetectionGlobal, essentia::standard::OnsetDetectionGlobal> regOnsetDetectionGlobal;
      AlgorithmFactory::Registrar<TempoTapDegara, essentia::standard::TempoTapDegara> regTempoTapDegara;
      AlgorithmFactory::Registrar<Scale, essentia::standard::Scale> regScale;
    }
  }
}