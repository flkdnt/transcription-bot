import logging
import os

from faster_whisper import BatchedInferencePipeline, WhisperModel


def transcribe_file(
    project,
    audio="video.wav",
    transcript="transcript.txt",
    batch_size=4,
    beam_size=5,
    compute_type="int8",
    device="cpu",
    model_size="medium",
    vad_filter=False,
):
    """Transcribes an audio file using faster_whisper.

    This function takes an audio file, creates a transcript,
    and uses the faster_whisper library to transcribe the audio.

    Args:
        project (str): The path to the project working directory, where the video
            files exist and the transcript file will get created
        audio (str): the name of the audio file. Defaults to "video.wav".
        transcript (str): the name of the transcript file. Defaults to "transcript.txt".
        batch_size (int): the maximum number of parallel requests to model for decoding. Defaults to 4
        beam_size (int): Beam size to use for decoding. Defaults to 5
        compute_type (str): The compute type for faster_whisper. See
            https://opennmt.net/CTranslate2/quantization.html. Defaults to "int8".
        device (str): Device to use for computation ("cpu", "cuda", "auto"). Defaults to "cpu".
        model_size (str): Size of the model to use (tiny, tiny.en, base, base.en, small,
            small.en, distil-small.en, medium, medium.en, distil-medium.en, large-v1, large-v2,
            large-v3, large, distil-large-v2, distil-large-v3, large-v3-turbo, or turbo), a
            path to a converted model directory, or a CTranslate2-converted Whisper model ID
            from the HF Hub. When a size or a model ID is configured, the converted model is
            downloaded from the Hugging Face Hub. Defaults to "medium".
        vad_filter (bool): Enable the voice activity detection (VAD) to filter out parts of the audio
            without speech. This step is using the Silero VAD model
            https://github.com/snakers4/silero-vad. Default is False

    Returns:
        None

    Raises:
        ValueError: If the input folder path is None.
        RuntimeError: If an error occurs during the transcription process.
    """
    if project is None:
        raise ValueError("Error! Project directory not specified!")

    # Run
    logger.info(f"Starting Transcription on {audio}...")
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        batched_model = BatchedInferencePipeline(model=model)
        segment_list = []

        segments, info = batched_model.transcribe(
            f"{project}/{audio}",
            batch_size=batch_size,
            beam_size=beam_size,
            vad_filter=vad_filter,
        )

        logger.info("Starting Transcription...")
        for segment in segments:
            cleaned_segment = segment.text.strip(" \t\n\r")
            segment_list.append(cleaned_segment)
            logger.debug(cleaned_segment)

        with open(f"{project}/{transcript}", "w") as f:
            for item in segment_list:
                f.write(f"{item}")
        logger.info(f"Transcript created at {project}/{transcript}")

    except Exception as e:
        logger.error(f"Error Transcribing Audio: {e}")
        raise RuntimeError("Error transcribing.")
        return None

    return segments


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Setup Audio Project
    repo_root = os.getcwd()
    audio_dir = "downloads"
    audio_project = "test"
    project_path = f"{repo_root}/{audio_dir}/{audio_project}"

    # Transcribe
    transcribe_file(project_path, batch_size=4, model_size="large-v1", vad_filter=True)
