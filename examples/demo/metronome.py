import argparse
from pathlib import Path

import essentia_rhythm_extractor as esrx


def main():
    parser = argparse.ArgumentParser(
        description="Generate a metronome track from an audio file using Essentia Rhythm Extractor."
    )
    parser.add_argument("input_file", type=str, help="Path to the input audio file")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="metronome.wav",
        help="Path to save the generated metronome WAV file (default: metronome.wav)",
    )
    parser.add_argument(
        "--create-mixed",
        action="store_true",
        help="Create a mixed version of the original audio with the metronome",
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Save beat grid data to a JSON file alongside the WAV",
    )
    args = parser.parse_args()
    if not Path(args.input_file).exists():
        print(f"Error: Input file '{args.input_file}' does not exist.")
        return
    result = esrx.generate_metronome_from_file(
        args.input_file,
        output_file=args.output,
        create_mixed=args.create_mixed,
        save_json=args.save_json,
    )
    print(result)

    # Returns dict with file paths and extracted data
    print(f"Metronome file: {result['metronome_file']}")  # Path to metronome WAV
    if "mixed_file" in result:
        print(f"Mixed file: {result['mixed_file']}")  # Path to mixed version
    if "json_file" in result:
        print(f"JSON file: {result['json_file']}")  # Path to JSON data
    print(f"BPM: {result['bpm']}")  # Extracted BPM and other data


if __name__ == "__main__":
    main()
