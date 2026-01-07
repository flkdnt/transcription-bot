import logging
import os
from datetime import datetime

from stages import stage_1, stage_2
from utility_os import find_files, format_path

logger = logging.getLogger(__name__)


def main(
    repo_root: str,
    url_list: list,
    audio_dir="downloads",
    input_dir="input",
    url_batch_size=10,
    noplaylist="True",
    llm_model="llama3.1:8b",
    llm_host="http://localhost:11434",
    chunk_size=2000,
    num_ctx=3000,
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

    for url_file in url_list:
        url_file = f"{repo_root}/{input_dir}/{url_file}"

        # Script Start
        stage_1(
            directory=download_directory,
            llm_host=llm_host,
            llm_model=llm_model,
            url_file=url_file,
            chunk_size=chunk_size,
            noplaylist=noplaylist,
            num_ctx=num_ctx,
            url_batch_size=url_batch_size,
        )

    # Step 5: Summarize Transcript
    transcripts = find_files(download_directory, "transcript.txt")
    logger.info(f"{datetime.now()}: Starting Summary Process")

    for transcript in transcripts:
        transcript_directory = format_path(transcript)

        stage_2(
            directory=transcript_directory,
            llm_host=llm_host,
            llm_model="llama3.2:3b",
            chunk_size=5000,
            num_ctx=6000,
        )

    logger.info(f"{datetime.now()}: Main Function Finished")


if __name__ == "__main__":
    # Configuration
    # logging.basicConfig(filename="logs/main.log", level=logging.INFO)
    logging.basicConfig(level=logging.INFO)
    repo_root = os.getcwd()
    # Batch size (number of URLs to process at a time)
    url_batch_size = 10
    # URL file
    noplaylist = "True"
    url_list = ["keynotes.txt"]

    main(
        llm_model="gemma3:4b",
        llm_host="http://ollama.hf.io:11434",
        repo_root=repo_root,
        url_list=url_list,
        url_batch_size=url_batch_size,
        noplaylist=noplaylist,
        chunk_size=5000,
        num_ctx=6000,
    )
