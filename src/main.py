import logging
import os
from datetime import datetime

from download import download_audio, download_subtitles
from edit import (
    extract_metadata,
    format_vtt_file,
    read_file,
    write_file,
)
from llm import paginate_transcript, send_transcript
from transcribe import transcribe_file

logger = logging.getLogger(__name__)


def delete_media_files(directory):
    """
    Deletes any file starting with "video", excluding video.info.json, video*.vtt
    from the given directory.
    """
    try:
        for root, directories, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                if os.path.isfile(filepath) and filename.startswith("video"):
                    logger.debug(f"{datetime.now()}:Found file: {filepath}")
                    if filename != "video.info.json" and not filename.endswith(".vtt"):
                        os.remove(filepath)
                        logger.info(f"{datetime.now()}: Deleted {filepath}")
    except Exception as e:
        logger.error(f"{datetime.now()}: Error deleting files: {e}")


def find_file(path, start_filter, end_filter):
    """
    Searches for a file within a given path that starts with 'start_filter' and ends with 'end_filter'

    Args:
        path: The directory to search within.

    Returns:
        Full filepath
    """
    try:
        files = os.listdir(path)
        logger.debug(f"{datetime.now()}:find_file: var path = {path}")
        for filename in files:
            if filename.startswith(start_filter) and filename.endswith(end_filter):
                found = f"{path}/{filename}"
                return found

    except FileNotFoundError:
        logger.error(f"Directory not found: {path}")
        raise  # Raise the FileNotFoundError


def main(
    repo_root: str,
    url_file: str,
    audio_dir="downloads",
    input_dir="input",
    url_batch_size=10,
    noplaylist="True",
    ollama_model="llama3.1:8b",
):
    """
    Orchestrates the transcription process from a list of URLs.

    This function downloads audio files from a list of URLs, transcribes
    them using Whisper, and saves the transcriptions.

    Args:
        repo_root (str): The root directory of the project.
        url_file (str): The path to the file containing the list of URLs.
        audio_dir (str, optional): The directory to store downloaded audio files.
            Defaults to "downloads".
        input_dir (str, optional): The directory for input files. Defaults to "input".
        url_batch_size (int, optional): The number of URLs to process in a batch.
            Defaults to 10.
        noplaylist (str, optional):  Option to control whether to use the playlist. Defaults to "True".

    Returns:
        None

    Raises:
        Exception: If any error occurs during the process.
    """
    logger.info(f"{datetime.now()}: Main Function Starting")
    # Build full directories
    download_directory = f"{repo_root}/{audio_dir}"
    transcript_prompt = f"{repo_root}/prompts/transcript.prompt.md"
    url_file = f"{repo_root}/{input_dir}/{url_file}"

    # Script Start
    try:
        # Step 1: Open url file
        with open(url_file, "r") as f:
            urls = f.readlines()

        # Step 2: Process URLs in batches
        for i in range(0, len(urls), url_batch_size):
            batch_urls = urls[i : i + url_batch_size]
            batch_number = i // url_batch_size

            logger.info(f"{datetime.now()}: Starting Batch {batch_number}")
            # For each URL...
            for url in batch_urls:
                url = url.strip()

                logger.info(f"{datetime.now()}: Subtitle Download Starting")

                # Step 2-1: Download Subtitles
                subtitle = download_subtitles(
                    url, download_directory, noplaylist=noplaylist
                )
                logger.debug(f"{datetime.now()}: Subtitle var 'subtitle': {subtitle}")
                if subtitle is None:
                    # We have to transcript the audio ourselves if no subtitles exist
                    logger.info(
                        f"{datetime.now()}: Subtitles Dont Exist! Downloading Audio"
                    )
                    # Step 2-2: Download video as audio file
                    audio = download_audio(
                        url, download_directory, noplaylist=noplaylist
                    )
                    logger.info(f"{datetime.now()}: Download Finished")
                    # Step 2-3: Transcribe Audio in Batches
                    logger.info(f"{datetime.now()}: Batch Transcription is starting")
                    transcribe_file(
                        f"{audio}/video.wav",
                        batch_size=8,
                        model_size="medium",
                        vad_filter=True,
                    )
                    logger.info(f"{datetime.now()}: Batch Transcription finished")
                    # Step 2-4: Delete media files
                    logger.info(f"{datetime.now()}: Deleting Media Files")
                    delete_media_files(audio)

                    # Step 3: Format Transcripts
                    # Transcript Variables
                    project_directory = f"{repo_root}/{audio}"
                    project_json = f"{project_directory}/video.info.json"
                    project_transcript = f"{project_directory}/transcript.txt"
                    project_subtitles = f"{project_directory}/subtitles.txt"

                    logger.info(f"{datetime.now()}: Starting transcript edit")

                    # Pre-Processing
                    sub_text = read_file(project_subtitles)
                    transcript_instructions = read_file(transcript_prompt)
                    transcript_details = extract_metadata(project_json)
                    transcript_instructions = (
                        f"{transcript_instructions}{transcript_details}"
                    )
                    transcript_pages = paginate_transcript(sub_text, chunk_size=4000)
                    for page in transcript_pages:
                        page = f"{transcript_details}{page}"

                    # Send to llm for processing
                    edited_text = send_transcript(
                        transcript_pages,
                        transcript_instructions,
                        ollama_model,
                        num_ctx=5000,
                        logger=logger,
                    )

                    if edited_text:
                        write_file(project_transcript, edited_text)
                    else:
                        logger.warning(
                            f"{datetime.now()}: No response to write to file!"
                        )
                    logger.info(f"{datetime.now()}: Finished transcript edit")

                else:
                    # Step 3: Format Transcript
                    # Variables
                    logger.info(f"{datetime.now()}: Subtitle Download Finished")
                    project_directory = f"{subtitle}"
                    project_transcript = f"{project_directory}/transcript.txt"
                    project_subtitles = find_file(project_directory, "video", ".vtt")

                    logger.debug(
                        f"project_directory: {project_directory}\nproject_transcript: {project_transcript}\nproject_subtitles: {project_subtitles}"
                    )

                    # Format Transcript
                    logger.info(f"{datetime.now()}: Starting transcript edit")
                    format_vtt_file(project_subtitles, project_transcript)
                    logger.info(f"{datetime.now()}: Finished transcript edit")

        logger.info(f"{datetime.now()}: Main Function Finished")

    except Exception as e:
        logger.error(f"An error occurred during processing: {e}")


if __name__ == "__main__":
    # Configuration
    # logging.basicConfig(filename="logs/main.log", level=logging.INFO)
    logging.basicConfig(level=logging.DEBUG)
    repo_root = os.getcwd()
    # Batch size (number of URLs to process at a time)
    url_batch_size = 10
    # URL file
    url_file = ""
    noplaylist = "True"

    main(
        ollama_model="gemma3:4b",
        repo_root=repo_root,
        url_file=url_file,
        url_batch_size=url_batch_size,
        noplaylist=noplaylist,
    )
