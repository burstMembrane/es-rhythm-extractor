# essentia-rhythm-multifeature

Skinny wheel exposing Essentia's RhythmExtractor2013 (multifeature) without importing the whole Essentia library.
NumPy audio in → BPM, ticks, confidence out.

## Install (local)

```bash
uv venv
uv pip install -U build scikit-build-core pybind11 numpy
uv pip install -e .
```

**Note**: The Essentia library source code and required Eigen headers are automatically downloaded and built during the build process. No git submodules, LFS downloads, or manual dependency setup required!
