import logging
import os

from faster_whisper import WhisperModel


def move_file(source_path, destination_path):
    """
    Moves a file from the source_path to the destination_path.

    Args:
        source_path: The full path to the file to be moved.
        destination_path: The full path to where the file should be moved.
    """
    try:
        os.rename(source_path, destination_path)
        print(f"File '{source_path}' moved to '{destination_path}'")
    except FileNotFoundError:
        print(f"Error: File '{source_path}' not found.")
    except OSError as e:
        print(f"Error moving file: {e}")


def transcribe_file(file):
    # faster_whisper configuration
    ## Other Options: "int8_float16", "int8"
    compute_type = "float16"
    ## Devices: "cuda", "cpu"
    device = "cuda"
    ## Model Size
    model_size = "small"

    # Run
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        segments, info = model.transcribe(file, beam_size=5)

        print(
            "Detected language '%s' with probability %f"
            % (info.language, info.language_probability)
        )

        for segment in segments:
            print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

    except Exception as e:
        logging.error = f"Error Transcribing Audio: {e}"
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Input Dir
    input_dir = "transcribe-bot/input"

    # Setup Audio Project
    ## Setup Root Audio Directory
    audio_dir = "transcribe-bot/audio"
    os.makedirs(audio_dir, exist_ok=True)
    ## Setup Project Directory
    audio_project = "AWS reInvent 2025 - Keynote with CEO Matt Garman.wav"
    os.makedirs(f"{audio_dir}/{audio_project}", exist_ok=True)
    ## Vars for Audio File
    audio_file = f"{audio_project}.mp3"
    audio_path = f"{audio_dir}/{audio_project}/{audio_file}"
    move_file(f"{input_dir}/{audio_project}", audio_path)

    # Transcribe
    transcribe_file(audio_path)
