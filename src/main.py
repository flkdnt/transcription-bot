import logging
import os
from datetime import datetime

from download import download_file
from transcribe import transcribe_file


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


def main(
    repo_root: str,
    url_file: str,
    audio_dir="downloads",
    input_dir="input",
    url_batch_size=10,
    noplaylist="True",
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
            # Step 2-1: For each URL...
            for url in batch_urls:
                url = url.strip()

                logger.info(f"{datetime.now()}: Download Starting")
                # ...Download audio
                download_file(
                    url, download_directory, noplaylist=noplaylist, logger=logger
                )
                logger.info(f"{datetime.now()}: Download Finished")

            ## Step 2-2: Find directories containing "video.wav"
            valid_dirs = [
                d
                for d in os.listdir(download_directory)
                if os.path.isdir(os.path.join(download_directory, d))
                and any(
                    os.path.join(download_directory, d, f)
                    for f in os.listdir(os.path.join(download_directory, d))
                    if "video.wav" in f
                )
                and not any(
                    os.path.join(download_directory, d, f)
                    for f in os.listdir(os.path.join(download_directory, d))
                    if ".vtt" in f
                )
            ]
            logger.info(f"{datetime.now()}: Videos Without Subtitles: {valid_dirs}")

            # Step 2-3: Transcribe Audio in Batches
            if not valid_dirs:
                logger.info(f"{datetime.now()}: Batch Transcription is starting")
                for dir in valid_dirs:
                    # Transcribe audio
                    transcribe_file(
                        f"{download_directory}/{dir}",
                        batch_size=8,
                        model_size="medium",
                        vad_filter=True,
                        logger=logger,
                    )
                logger.info(f"{datetime.now()}: Batch Transcription finished")

            # Step 2-4: Delete media files
            logger.info(f"{datetime.now()}: Deleting Media Files")
            delete_media_files(download_directory)

        logger.info(f"{datetime.now()}: Main Function Finished")

    except Exception as e:
        logger.error(f"An error occurred during processing: {e}")


if __name__ == "__main__":
    logging.basicConfig(filename="logs/main.log", level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Configuration
    repo_root = os.getcwd()
    # Batch size (number of URLs to process at a time)
    url_batch_size = 10
    # URL file
    url_file = "keynotes.txt"
    noplaylist = "True"

    main(
        repo_root=repo_root,
        url_file=url_file,
        url_batch_size=url_batch_size,
        noplaylist=noplaylist,
    )
