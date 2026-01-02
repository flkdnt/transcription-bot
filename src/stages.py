import logging
import os
from datetime import datetime

from download import download_audio, download_subtitles
from edit import extract_metadata, format_vtt_file
from transcribe import transcribe_file
from utility_llm import paginate_prompt, send_prompt
from utility_os import (
    delete_files,
    read_file,
    write_file,
)

logger = logging.getLogger(__name__)


def stage_1(
    directory: str,
    llm_host: str,
    llm_model: str,
    transcript_prompt: str,
    url_file: str,
    chunk_size=2000,
    noplaylist="True",
    num_ctx=3000,
    url_batch_size=10,
) -> None:
    """
    Stage 1 of the transcription process.

    This stage creates a transcript.txt, by either:
    1. downloading subtitles and formatting them, or
    2. downloading the video, converting into an audio file, transcribing the
        audio using faster_whisper, and formatting the transcriptcusing a large
        language model (LLM).

    Args:
        directory: The directory where files will be stored and processed.
        llm_host: The hostname or IP address of the LLM service.
        llm_model: The name of the LLM model to use for transcript formatting.
        transcript_prompt: The prompt to use when formatting the transcript with the LLM.
        url_file: The path to a file containing a list of URLs.
        chunk_size: The size of chunks to use when processing the transcript with the LLM.
        noplaylist: Flag indicating if a playlist should be ignored. Defaults to "True".
        num_ctx: The maximum number of tokens to use in the LLM context.
        url_batch_size: The number of URLs to process in each batch.

    Raises:
        Exception: If any error occurs during the stage execution.
    """
    # Stage 1 Start
    try:
        # Stage 1-1:
        # Open url file
        logger.debug(f"{datetime.now()}:Stage 1-1: Opening File {url_file}")
        with open(url_file, "r") as f:
            urls = f.readlines()

        # Stage 1-1::
        # Process URLs in batches
        for i in range(0, len(urls), url_batch_size):
            batch_urls = urls[i : i + url_batch_size]
            batch_number = i // url_batch_size

            logger.info(f"{datetime.now()}:Stage 1-1: Starting Batch {batch_number}")
            # For each URL...
            for url in batch_urls:
                url = url.strip()

                # Stage 1-2: Download Subtitles
                subtitle = stage_1_2(
                    url=url, directory=directory, noplaylist=noplaylist
                )

                if subtitle is None:
                    # Stage 1-3:: Download video as audio file
                    # We have to transcript the audio ourselves if no subtitles exist
                    audio = stage_1_3(
                        url=url,
                        directory=directory,
                        noplaylist=noplaylist,
                    )

                    # Stage 1-4: Transcribe Audio with whisper in Batches
                    # Transcript Variables
                    if audio:
                        project_subtitles = stage_1_4(filepath=audio)

                        # Stage 1-5: Format Whisper Transcripts
                        stage_1_5(
                            chunk_size=chunk_size,
                            filepath=audio,
                            llm_host=llm_host,
                            llm_model=llm_model,
                            num_ctx=num_ctx,
                            project_subtitles=project_subtitles,
                            prompt=transcript_prompt,
                        )
                    else:
                        logger.error(
                            f"{datetime.now()}:Stage 1-3: Error! 'audio' var is None!"
                        )

                else:
                    logger.info(
                        f"{datetime.now()}:Stage 1-2: Subtitle Download Finished"
                    )
                    # Step 3: Format VTT into Transcript
                    stage_1_6(filepath=subtitle)

            # Stage 1-7: Cleanup Files
            # Delete media files now that we have a transcript to process
            logger.info(f"{datetime.now()}:Stage 1-7: Deleting Files")
            delete_files(directory=directory, prefix="video")
            # delete_files(directory=directory, name="subtitles.txt")
            logger.info(f"{datetime.now()}:Stage 1-7: Finished Deleting Files")

        logger.info(f"{datetime.now()}:Stage 1: Finished Stage 1")

    except Exception as e:
        logger.error(f"An error occurred in Stage 1: {e}")


def stage_1_2(url: str, directory: str, noplaylist: str) -> str | None:
    """
    Downloads subtitles from a given URL.

    This function handles the download of subtitle files from a specified URL.
    It utilizes the `download_subtitles` helper function to perform the download
    and returns the downloaded subtitle file path if successful, or None if an
    error occurs.

    Args:
        url: The URL of the subtitle file to download.
        directory: The directory to store the downloaded subtitle file.
        noplaylist: A flag indicating whether to ignore the playlist. Defaults to "True".

    Returns:
        The path to the downloaded subtitle file if successful, or None if an error occurred.

    Raises:
        Exception: If any error occurs during the download process.
    """
    # Stage 1-2: Download Subtitles
    logger.info(f"{datetime.now()}:Stage 1-2: Subtitle Download Starting")
    subtitle = download_subtitles(url, directory, noplaylist=noplaylist)
    logger.debug(f"{datetime.now()}:Stage 1-2: Subtitle var 'subtitle': {subtitle}")
    return subtitle


def stage_1_3(url: str, directory: str, noplaylist: str) -> str | None:
    """
    Downloads audio from a given URL.

    This function handles the download of audio files from a specified URL.
    It utilizes the `download_audio` helper function to perform the download
    and returns the downloaded audio file path if successful, or None if an
    error occurs.

    Args:
        url: The URL of the audio file to download.
        directory: The directory to store the downloaded audio file.
        noplaylist: A flag indicating whether to ignore the playlist. Defaults to "True".

    Returns:
        The path to the downloaded audio file if successful, or None if an error occurred.

    Raises:
        Exception: If any error occurs during the download process.
    """
    # Stage 1-3:: Download video as audio file
    # We have to transcript the audio ourselves if no subtitles exist
    logger.info(f"{datetime.now()}:Stage 1-3: Subtitles Dont Exist! Downloading Audio")
    audio = download_audio(url, directory, noplaylist=noplaylist)
    logger.info(f"{datetime.now()}:Stage 1-3: Download Finished")
    return audio


def stage_1_4(filepath: str) -> str:
    """
    Transcribes audio files using faster_whisper in batches.

    This function utilizes the faster_whisper speech-to-text model to transcribe
    audio files. It handles the transcription process in batches,
    allowing for efficient processing of larger audio files. It checks if
    subtitles already exist and skips transcription if they do.

    Args:
        filepath: The path to the audio file to transcribe.

    Returns:
        The path to the generated subtitle file (subtitles.txt) after
        transcription.

    Raises:
        Exception: If any error occurs during the transcription process.
    """
    # Stage 1-4: Transcribe Audio in Batches
    # Transcript Variables
    project_directory = f"{filepath}"
    project_subtitles = f"{project_directory}/subtitles.txt"

    if os.path.exists(project_subtitles):
        logger.info(
            f"{datetime.now()}:Stage 1-4: Subtitles {project_subtitles} already exist, skipping whisper transcription"
        )
    else:
        logger.info(f"{datetime.now()}:Stage 1-4: Batch Transcription is starting")
        transcribe_file(
            f"{filepath}",
            batch_size=8,
            model_size="medium",
            vad_filter=True,
        )
        logger.info(f"{datetime.now()}:Stage 1-4: Batch Transcription finished")
    return project_subtitles


def stage_1_5(
    chunk_size: int,
    filepath: str,
    llm_host: str,
    llm_model: str,
    num_ctx: int,
    project_subtitles: str,
    prompt: str,
) -> None:
    """
    Formats Whisper transcripts using a Large Language Model (LLM).

    This function takes the raw Whisper transcript and formats it into a
    more readable and polished format using the specified LLM. It handles
    the interaction with the LLM, ensuring that the input is properly
    formatted and the output is saved to a file.

    Args:
        chunk_size: The size of chunks to use when formatting the transcript
            with the LLM.
        filepath: The path to the audio file that was transcribed.
        llm_host: The hostname or IP address of the LLM service.
        llm_model: The name of the LLM model to use for transcript formatting.
        num_ctx: The maximum number of tokens to use in the LLM context.
        project_subtitles: The path to the file containing the Whisper
            transcript.
        prompt: The prompt to use when formatting the transcript with the LLM.

    Raises:
        Exception: If any error occurs during the formatting process.
    """
    # Stage 1-5: Format whisper Transcripts
    # Transcript Variables
    project_directory = f"{filepath}"
    project_json = f"{project_directory}/video.info.json"
    project_transcript = f"{project_directory}/transcript.txt"

    if os.path.exists(project_transcript):
        logger.info(
            f"{datetime.now()}:Stage 1-5: Transcript {project_transcript} already exists, skipping transcript edit"
        )
    else:
        logger.info(f"{datetime.now()}:Stage 1-5: Starting transcript edit")

    # Postfixing intructions
    subtitle = read_file(project_subtitles)
    instructions = read_file(prompt)
    details = "\n\n**TRANSCRIPT DETAILS**\n\n"
    details += "*Please do not include this section in the transcript*!\n"
    extract = extract_metadata(project_json)
    if extract:
        details += extract
    details += "\n\n**TRANSCRIPT**\n"
    instructions = f"{instructions}{details}"

    # Paginate Subtitles
    transcript_pages = paginate_prompt(subtitle, chunk_size=chunk_size)

    # Add instruction to the beginning of each paginated prompt
    for page in transcript_pages:
        page = f"{details}{page}"

    # Send to llm for processing
    transcript = send_prompt(
        input=transcript_pages,
        instructions=instructions,
        model=llm_model,
        host=llm_host,
        num_ctx=num_ctx,
    )

    if transcript:
        write_file(project_transcript, transcript)
    else:
        logger.warning(f"{datetime.now()}:Stage 1-5: No response to write to file!")
    logger.info(f"{datetime.now()}:Stage 1-5: Finished transcript edit")


def stage_1_6(filepath: str) -> None:
    """
    Formats the Whisper transcript into a VTT file.

    This function converts the generated Whisper transcript (in a text
    format) into a VTT (Video Text Tracks) file, which is a standard
    format for subtitles.  It handles the creation of the VTT file,
    ensuring that the transcript is properly formatted and aligned with
    the video.

    Args:
        filepath: The path to the audio file that was transcribed.
    """
    # Step 3: Format Transcript
    # Variables
    project_directory = f"{filepath}"
    project_json = f"{project_directory}/video.info.json"
    project_transcript = f"{project_directory}/transcript.txt"
    project_subtitles = f"{project_directory}/subtitles.txt"

    # Creating details file
    logger.debug(f"{datetime.now()}:Stage 1-6: Extracting Metadata")
    extract_metadata(project_json)

    if os.path.exists(project_transcript):
        logger.info(
            f"{datetime.now()}:Stage 1-6: Transcript {project_transcript} already exists, skipping transcript edit"
        )
    else:
        # Format Transcript
        logger.info(f"{datetime.now()}:Stage 1-6: Starting transcript edit")
        format_vtt_file(project_subtitles, project_transcript)
        logger.info(f"{datetime.now()}:Stage 1-6: Finished transcript edit")


def stage_2(
    llm_host: str,
    llm_model: str,
    highlight_file: str,
    summary_file: str,
    transcript_file: str,
    highlight_prompt: str,
    outline_prompt: str,
    summary_prompt: str,
    chunk_size=2000,
    num_ctx=3000,
) -> None:
    # create summary file
    write_file(summary_file, "")

    # if os.path.exists(highlight_file):
    #    logger.info(
    #        f"{datetime.now()}: Highlight {highlight_file} already exists, skipping Highlights"
    #    )
    # else:
    #    # Create Highlights
    #    stage_2_1(
    #        chunk_size=chunk_size,
    #        llm_host=llm_host,
    #        llm_model=llm_model,
    #        num_ctx=num_ctx,
    #        highlight_file=highlight_file,
    #        highlight_prompt=highlight_prompt,
    #        transcript_file=transcript_file,
    #    )

    if os.path.exists(summary_file):
        logger.info(
            f"{datetime.now()}: Summary {summary_file} already exists, skipping Summary"
        )
    else:
        # Create Summary with outline options
        stage_2_2(
            chunk_size=chunk_size,
            llm_host=llm_host,
            llm_model=llm_model,
            num_ctx=num_ctx,
            summary_file=summary_file,
            outline_prompt=outline_prompt,
            transcript_file=transcript_file,
        )

    logger.info(f"{datetime.now()}: Finished Summary for {transcript_file}")


def stage_2_1(
    chunk_size: int,
    llm_host: str,
    llm_model: str,
    num_ctx: int,
    highlight_file: str,
    highlight_prompt: str,
    transcript_file: str,
) -> None:
    logger.info(f"{datetime.now()}: Starting Highlight for {transcript_file}")
    # paginate transcript
    transcript = read_file(transcript_file)
    pages = paginate_prompt(transcript, chunk_size=chunk_size)

    # Send to llm for processing
    highlight = send_prompt(
        pages,
        instructions=highlight_prompt,
        model=llm_model,
        host=llm_host,
        num_ctx=num_ctx,
    )

    if highlight:
        for item in highlight:
            write_file(
                highlight_file,
                item,
                mode="a",
            )
    else:
        logger.warning(f"{datetime.now()}: No response to write to file!")


def stage_2_2(
    chunk_size: int,
    llm_host: str,
    llm_model: str,
    num_ctx: int,
    summary_file: str,
    outline_prompt: str,
    transcript_file: str,
) -> None:
    logger.info(f"{datetime.now()}: Starting Outline for {transcript_file}")
    # paginate transcript
    transcript = read_file(transcript_file)
    pages = paginate_prompt(transcript, chunk_size=chunk_size)

    # Send to llm for processing
    outline = send_prompt(
        pages,
        instructions=outline_prompt,
        model=llm_model,
        host=llm_host,
        num_ctx=num_ctx,
    )

    if outline:
        for item in outline:
            write_file(
                summary_file,
                f"**Outline**\n{item}\n**End Outline**\n",
                mode="a",
            )
    else:
        logger.warning(f"{datetime.now()}: No response to write to file!")
