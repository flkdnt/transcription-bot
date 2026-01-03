import json
import logging
import os
import re
from datetime import datetime

from utility_llm import paginate_prompt, send_prompt
from utility_os import format_path, read_file, write_file

logger = logging.getLogger(__name__)


def extract_metadata(file_path) -> str | None:
    """
    Extracts specific fields from the video.info.json file using the json library.

    Args:
        file_path (str): The path to the video.info.json file.

    Returns:
        str: A string containing the extracted fields(in Markdown Format), or None if an error occurred.
    """
    try:
        with open(file_path, "r") as f:
            data = f.read()

        # Attempt to parse the JSON data
        try:
            video_info = json.loads(data)
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON format in {file_path}")
            raise

        extracted_data = ""

        # Extract upload_date
        extracted_data += f"* Upload Date: {video_info.get('upload_date')}\n"
        extracted_data += f"* Channel: {video_info.get('channel')}\n"
        extracted_data += f"* Title: {video_info.get('fulltitle')}\n"
        extracted_data += f"* URL: {video_info.get('webpage_url')}\n"
        extracted_data += f"* Description: {video_info.get('description')}\n"

        # Write MD to File for future processing
        home_folder = format_path(file_path)
        details_file = f"{home_folder}/description.md"
        logger.debug(f"{datetime.now()}: details file location: {details_file}")
        write_file(details_file, extracted_data)

        return extracted_data

    except FileNotFoundError:
        logging.error(f"{datetime.now()}: File not found at {file_path}")
        raise
    except Exception as e:
        logging.error(f"{datetime.now()}: An error occurred: {e}")
        raise


def format_summary_file(filepath) -> None:
    try:
        logger.debug(f"{datetime.now()}:Starting Summary File Edit")
        # Step 1 - Split text into chunks by tag
        summary = read_file(filepath)
        summary = summary.split("**End Outline**")
        logger.info(summary)

    except FileNotFoundError:
        logger.error(f"{datetime.now()}: Error: File not found at {filepath}")
        raise
    except Exception as e:
        logger.error(f"{datetime.now()}: An error occurred: {e}")
        raise


def format_vtt_file(vtt_file_path, output_file_path) -> None:
    """
    Converts a .vtt file to a text file containing only the captions (timecodes and text).

    This function extracts the caption text from a .vtt file and saves it to a text file.
    It removes the WEBVTT header and any associated metadata, leaving only the text content.

    Args:
        vtt_file_path (str): The path to the input .vtt file.
        output_file_path (str, optional): The path to save the output text file.
                                         If None, the output text is logged to the console.
                                         Defaults to None.

    Returns:
        None

    Notes:
        - This function assumes the input .vtt file follows the WEBVTT format.
        - It removes the WEBVTT header and any associated metadata from the input file.
        - If `output_file_path` is None, the extracted caption text is logged to the console instead.

    Raises:
        FileNotFoundError: If the specified .vtt file is not found.
        Exception: If any other error occurs during the process.
    """

    try:
        with open(vtt_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Remove WEBVTT Header
        content = re.sub(r"^WEBVTT\n[a-zA-Z: ]*\n[a-zA-Z: ]*\n\n", "", content)

        # Remove timestamps and audio descriptions.
        # TODO: Create Param to make Audio Description removal optional
        caption_regex = re.compile(r"([0-9:. ]*-->[0-9:. ]*)|([(][) a-z0-9].*)")
        content = caption_regex.sub("", content)
        while re.findall("\n\n", content):
            logger.debug(f"{datetime.now()}: Removing double-newlines")
            content = re.sub("\n\n", "\n", content)

        # Remove Leading Space in transcript
        content = re.sub(r"^\n", "", content)

        # Remove all newlines that dont have proper punctuation
        content = re.sub(r"((?<![?!.])\n)", " ", content)

        # Write Edited transcript
        with open(output_file_path, "w", encoding="utf-8") as outfile:
            outfile.write(content)
        logger.info(
            f"{datetime.now()}: Successfully converted {vtt_file_path} to {output_file_path}"
        )

    except FileNotFoundError:
        logger.error(f"{datetime.now()}: Error: File not found at {vtt_file_path}")
        raise
    except Exception as e:
        logger.error(f"{datetime.now()}: An error occurred: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    # --- LLM Configuration ---
    ollama_model = ""

    repo_root = os.getcwd()
    prompt_file = f"{repo_root}/prompts/transcript.prompt.md"
    json_file = transcript = f"{repo_root}/downloads/FOLDER/video.info.json"
    transcript = f"{repo_root}/downloads/FOLDER/video.en.vtt"
    temp_transcript = f"{repo_root}/downloads/FOLDER/video.en.vtt.txt"
    final_transcript = f"{repo_root}/downloads/FOLDER/edited_transcript.txt"

    logger.info(f"{datetime.now()}: starting transcript edit")
    # This is only for vtt files
    format_vtt_file(transcript, temp_transcript)

    # This section is only for Whisper transcripts
    original_text = read_file(temp_transcript)
    instructions = read_file(prompt_file)
    details = "\n\n**TRANSCRIPT DETAILS**\n\n"
    details += "*Please do not include this section in the transcript*!\n"
    details += extract_metadata(json_file)
    details += "\n\n**TRANSCRIPT**\n"
    instructions = f"{instructions}{details}"
    pages = paginate_prompt(original_text, chunk_size=4000, logger=logger)
    for page in pages:
        page = f"{details}{page}"
    edited_text = send_prompt(
        pages, instructions, ollama_model, num_ctx=5000, logger=logger
    )

    if edited_text:
        write_file(final_transcript, edited_text)
    else:
        logger.warning(f"{datetime.now()}: No reponse to write to file!")
