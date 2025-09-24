#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
// ignore unused variable warning from numpy headers
#include <numpy/ndarrayobject.h>
#include "core/mf_runner.h"

namespace py = pybind11;

static inline void check_input(const py::array &x, double sr)
{
    if (x.ndim() != 1)
    {
        throw std::runtime_error("Expected mono 1D array, got " + std::to_string(x.ndim()) + "D array");
    }

    PyArrayObject *array = (PyArrayObject *)x.ptr();
    if (array->descr->type_num != NPY_FLOAT)
    {
        throw std::runtime_error("Expected float32 numpy array, got type_num=" + std::to_string(array->descr->type_num) + " (expected " + std::to_string(NPY_FLOAT) + ")");
    }

    if (sr != 44100.0)
    {
        throw std::runtime_error("Expected sample_rate=44100.0, got " + std::to_string(sr));
    }
}

py::dict rhythm_multifeature(py::array_t<float> x, double sample_rate,
                             int min_tempo = 40, int max_tempo = 208)
{
    check_input(x, sample_rate);
    auto buf = x.request();
    auto *data = static_cast<float *>(buf.ptr);
    auto out = run_multifeature(data, static_cast<size_t>(buf.size),
                                min_tempo, max_tempo);

    py::dict d;
    d["bpm"] = out.bpm;
    d["confidence"] = out.confidence;
    d["ticks"] = py::array(out.ticks_sec.size(), out.ticks_sec.data());
    d["bpm_estimates"] = py::array(out.bpm_estimates.size(), out.bpm_estimates.data());
    d["bpm_intervals"] = py::array(out.bpm_intervals_sec.size(), out.bpm_intervals_sec.data());
    return d;
}

py::dict rhythm_extractor_2013(py::array_t<float> x, double sample_rate,
                               int min_tempo = 40, int max_tempo = 208,
                               const std::string &method = "multifeature")
{
    check_input(x, sample_rate);
    auto buf = x.request();
    auto *data = static_cast<float *>(buf.ptr);
    auto out = run_rhythm_extractor_2013(data, static_cast<size_t>(buf.size),
                                         min_tempo, max_tempo, method);

    py::dict d;
    d["bpm"] = out.bpm;
    d["confidence"] = out.confidence;
    d["ticks"] = py::array(out.ticks_sec.size(), out.ticks_sec.data());
    d["bpm_estimates"] = py::array(out.bpm_estimates.size(), out.bpm_estimates.data());
    d["bpm_intervals"] = py::array(out.bpm_intervals_sec.size(), out.bpm_intervals_sec.data());
    return d;
}

py::dict onset_detection(py::array_t<float> x, double sample_rate)
{
    check_input(x, sample_rate);
    auto buf = x.request();
    auto *data = static_cast<float *>(buf.ptr);
    auto out = run_onset_detection(data, static_cast<size_t>(buf.size));

    py::dict d;
    d["onset_rate"] = out.onset_rate;
    d["onsets"] = py::array(out.onsets_sec.size(), out.onsets_sec.data());
    return d;
}

// File-based Python bindings
py::dict rhythm_multifeature_from_file(const std::string& filename,
                                       int min_tempo = 40, int max_tempo = 208)
{
    auto out = run_multifeature_from_file(filename, min_tempo, max_tempo);

    py::dict d;
    d["bpm"] = out.bpm;
    d["confidence"] = out.confidence;
    d["ticks"] = py::array(out.ticks_sec.size(), out.ticks_sec.data());
    d["bpm_estimates"] = py::array(out.bpm_estimates.size(), out.bpm_estimates.data());
    d["bpm_intervals"] = py::array(out.bpm_intervals_sec.size(), out.bpm_intervals_sec.data());
    return d;
}

py::dict rhythm_extractor_2013_from_file(const std::string& filename,
                                         int min_tempo = 40, int max_tempo = 208,
                                         const std::string& method = "multifeature")
{
    auto out = run_rhythm_extractor_2013_from_file(filename, min_tempo, max_tempo, method);

    py::dict d;
    d["bpm"] = out.bpm;
    d["confidence"] = out.confidence;
    d["ticks"] = py::array(out.ticks_sec.size(), out.ticks_sec.data());
    d["bpm_estimates"] = py::array(out.bpm_estimates.size(), out.bpm_estimates.data());
    d["bpm_intervals"] = py::array(out.bpm_intervals_sec.size(), out.bpm_intervals_sec.data());
    return d;
}

py::dict onset_detection_from_file(const std::string& filename)
{
    auto out = run_onset_detection_from_file(filename);

    py::dict d;
    d["onset_rate"] = out.onset_rate;
    d["onsets"] = py::array(out.onsets_sec.size(), out.onsets_sec.data());
    return d;
}

PYBIND11_MODULE(_rhythmext, m)
{
    m.doc() = "Essentia RhythmExtractor2013 multifeature (skinny wheel)";
    m.def("rhythm_multifeature", &rhythm_multifeature,
          py::arg("x"), py::arg("sample_rate"),
          py::arg("min_tempo") = 40, py::arg("max_tempo") = 208);
    m.def("rhythm_extractor_2013", &rhythm_extractor_2013,
          py::arg("x"), py::arg("sample_rate"),
          py::arg("min_tempo") = 40, py::arg("max_tempo") = 208,
          py::arg("method") = "multifeature");
    m.def("onset_detection", &onset_detection,
          py::arg("x"), py::arg("sample_rate"));

    // File-based functions
    m.def("rhythm_multifeature_from_file", &rhythm_multifeature_from_file,
          py::arg("filename"),
          py::arg("min_tempo") = 40, py::arg("max_tempo") = 208);
    m.def("rhythm_extractor_2013_from_file", &rhythm_extractor_2013_from_file,
          py::arg("filename"),
          py::arg("min_tempo") = 40, py::arg("max_tempo") = 208,
          py::arg("method") = "multifeature");
    m.def("onset_detection_from_file", &onset_detection_from_file,
          py::arg("filename"));
}