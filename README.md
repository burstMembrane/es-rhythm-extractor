# essentia-rhythm-multifeature

Skinny wheel exposing Essentia's RhythmExtractor2013 (multifeature) without importing the whole Essentia library.
NumPy audio in → BPM, ticks, confidence out.

## Install (local)

```bash
uv venv
uv pip install -U build scikit-build-core pybind11 numpy
uv pip install -e .
