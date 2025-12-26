import json
import logging
import os
import re
from datetime import datetime

from llm import paginate_transcript, send_transcript


def extract_metadata(file_path):
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
            return None

        extracted_data = "\n\n**TRANSCRIPT DETAILS**\n\n"
        extracted_data += "*Please do not include this section in the transcript*!\n"

        # Extract upload_date
        extracted_data += f"* Upload Date: {video_info.get('upload_date')}\n"
        extracted_data += f"* Channel: {video_info.get('channel')}\n"
        extracted_data += f"* Title: {video_info.get('fulltitle')}\n"
        extracted_data += f"* URL: {video_info.get('webpage_url_domain')}\n"
        extracted_data += f"* Description: {video_info.get('description')}\n"
        extracted_data += "\n\n**TRANSCRIPT**\n"

        return extracted_data

    except FileNotFoundError:
        logging.error(f"File not found at {file_path}")
        return None
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None


def format_vtt_file(vtt_file_path, output_file_path):
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
            logger.info(f"{datetime.now()}: Removing double-newlines")
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
    except Exception as e:
        logger.error(f"{datetime.now()}: An error occurred: {e}")


def read_file(file_path):
    """
    Reads the entire contents of a file and returns it as a string.

    This function reads the entire content of a file and returns it as a single string.
    It handles potential errors gracefully, such as a file not being found.

    Args:
        file_path (str): The path to the file to be read.

    Returns:
        str: The contents of the file as a string.
             Returns None if the file cannot be read.

    Raises:
        None
    """

    try:
        with open(file_path, "r") as f:
            contents = f.read()
        return contents
    except FileNotFoundError:
        logger.error(f"{datetime.now()}: File not found at {file_path}")
        return None
    except Exception as e:
        logger.error(f"{datetime.now()}: An error occurred: {e}")
        return None


def write_file(file_path, content, mode="w"):
    """
    Writes content to a file.

    This function writes the provided content to a file.  It supports various modes,
    including writing (default), appending, and exclusive creation.

    Args:
        file_path (str): The path to the file to be written to.
        content (str or list): The content to write to the file.
                              If a list is provided, it will be joined into a string.
        mode (str, optional): The file writing mode. Defaults to 'w' (write).
                              Other options include 'a' (append) and 'x' (exclusive creation).

    Returns:
        None

    Raises:
        None
    """

    try:
        with open(file_path, mode) as f:
            if type(content) is list:
                f.write("".join(str(i) for i in content))
            if type(content) is str:
                f.write(content)
        logger.info(f"{datetime.now()}: Successfully wrote to {file_path}")
    except Exception as e:
        logger.info(
            f"{datetime.now()}: An error occurred while writing to {file_path}: {e}"
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    # --- LLM Configuration ---
    ollama_Model = "gemma3:4b"

    repo_root = os.getcwd()
    prompt_file = f"{repo_root}/prompts/transcript.prompt.md"
    json_file = transcript = (
        f"{repo_root}/downloads/AWS_re_-Invent_2025_-_Keynote_with_CEO_Matt_Garman/video.info.json"
    )
    transcript = f"{repo_root}/downloads/AWS_re_-Invent_2025_-_Keynote_with_CEO_Matt_Garman/video.en.vtt"
    temp_transcript = f"{repo_root}/downloads/AWS_re_-Invent_2025_-_Keynote_with_CEO_Matt_Garman/video.en.vtt.txt"
    final_transcript = f"{repo_root}/downloads/AWS_re_-Invent_2025_-_Keynote_with_CEO_Matt_Garman/edited_transcript.txt"

    logger.info(f"{datetime.now()}: starting transcript edit")
    # This is only for vtt files
    format_vtt_file(transcript, temp_transcript)

    # This section is only for Whisper transcripts
    original_text = read_file(temp_transcript)
    instructions = read_file(prompt_file)
    details = extract_metadata(json_file)
    instructions = f"{instructions}{details}"
    pages = paginate_transcript(original_text, chunk_size=4000, logger=logger)
    for page in pages:
        page = f"{details}{page}"
    edited_text = send_transcript(
        pages, instructions, ollama_Model, num_ctx=5000, logger=logger
    )

    if edited_text:
        write_file(final_transcript, edited_text)
    else:
        logger.warning(f"{datetime.now()}: No reponse to write to file!")
