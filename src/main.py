import logging
import os
from datetime import datetime

from download import download_audio, download_subtitles
from edit import extract_metadata, format_vtt_file
from transcribe import transcribe_file
from utility_llm import paginate_prompt, send_prompt
from utility_os import (
    delete_media_files,
    find_files,
    format_path,
    read_file,
    validate_file,
    write_file,
)

logger = logging.getLogger(__name__)


def main(
    repo_root: str,
    url_file: str,
    audio_dir="downloads",
    input_dir="input",
    url_batch_size=10,
    noplaylist="True",
    ollama_model="llama3.1:8b",
    ollama_host="http://localhost:11434",
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
                    # Transcript Variables
                    project_directory = f"{audio}"
                    project_json = f"{project_directory}/video.info.json"
                    project_transcript = f"{project_directory}/transcript.txt"
                    project_subtitles = f"{project_directory}/subtitles.txt"

                    # Transcribe
                    if os.path.exists(project_subtitles):
                        logger.info(
                            f"{datetime.now()}: Subtitles {project_subtitles} already exist, skipping whisper transcription"
                        )
                    else:
                        logger.info(
                            f"{datetime.now()}: Batch Transcription is starting"
                        )
                        transcribe_file(
                            f"{audio}",
                            batch_size=8,
                            model_size="medium",
                            vad_filter=True,
                        )
                        logger.info(f"{datetime.now()}: Batch Transcription finished")

                    # Step 3: Format Transcripts
                    if os.path.exists(project_transcript):
                        logger.info(
                            f"{datetime.now()}: Transcript {project_transcript} already exists, skipping transcript edit"
                        )
                    else:
                        logger.info(f"{datetime.now()}: Starting transcript edit")

                        # Pre-Processing
                        sub_text = read_file(project_subtitles)
                        transcript_instructions = read_file(transcript_prompt)
                        transcript_details = "\n\n**TRANSCRIPT DETAILS**\n\n"
                        transcript_details += (
                            "*Please do not include this section in the transcript*!\n"
                        )
                        transcript_details += extract_metadata(project_json)
                        transcript_details += "\n\n**TRANSCRIPT**\n"
                        transcript_instructions = (
                            f"{transcript_instructions}{transcript_details}"
                        )
                        transcript_pages = paginate_prompt(
                            sub_text, chunk_size=chunk_size
                        )
                        for page in transcript_pages:
                            page = f"{transcript_details}{page}"

                        # Send to llm for processing
                        edited_text = send_prompt(
                            transcript_pages,
                            transcript_instructions,
                            ollama_model,
                            host=ollama_host,
                            num_ctx=num_ctx,
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
                    project_json = f"{project_directory}/video.info.json"
                    project_transcript = f"{project_directory}/transcript.txt"
                    project_subtitles = f"{project_directory}/subtitles.txt"

                    # Creating details file
                    extract_metadata(project_json)

                    if os.path.exists(project_transcript):
                        logger.info(
                            f"{datetime.now()}: Transcript {project_transcript} already exists, skipping transcript edit"
                        )
                    else:
                        # Format Transcript
                        logger.info(f"{datetime.now()}: Starting transcript edit")
                        format_vtt_file(project_subtitles, project_transcript)
                        logger.info(f"{datetime.now()}: Finished transcript edit")

            # Step 4: Cleanup Files
            # Delete media files now that we have a transcript to process
            logger.info(f"{datetime.now()}: Deleting Media Files")
            delete_media_files(download_directory)

        # Step 5: Summarize Transcript
        pre_summary = find_files(download_directory, "transcript.txt")
        logger.info(f"{datetime.now()}: Starting Summary Process")

        for item in pre_summary:
            summary_directory = format_path(item)
            summary_file = f"{summary_directory}/summary.txt"
            summary_input = f"{summary_directory}/transcript.txt"
            summary_prompt = f"{repo_root}/prompts/summary.prompt.md"
            if os.path.exists(summary_file):
                logger.info(
                    f"{datetime.now()}: Summary {summary_file} already exists, skipping summary process"
                )
            else:
                transcript = read_file(summary_input)
                pages = paginate_prompt(transcript, chunk_size=chunk_size)

                # Send to llm for processing
                summarized_text = send_prompt(
                    pages,
                    instructions=summary_prompt,
                    model=ollama_model,
                    host=ollama_host,
                    num_ctx=num_ctx,
                )

                if summarized_text:
                    write_file(summary_file, summarized_text)
                else:
                    logger.warning(f"{datetime.now()}: No response to write to file!")

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
    url_file = "keynotes.txt"
    noplaylist = "True"

    main(
        ollama_model="gemma3:4b",
        ollama_host="http://ollama.hf.io:11434",
        repo_root=repo_root,
        url_file=url_file,
        url_batch_size=url_batch_size,
        noplaylist=noplaylist,
        chunk_size=4000,
        num_ctx=5000,
    )
