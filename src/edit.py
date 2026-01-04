import json
import logging
import os
import re
from datetime import datetime

from utility_os import format_path, read_file, write_file

logger = logging.getLogger(__name__)


def convert_roman_numerals(text: str) -> tuple[int, str]:
    """
    Finds all occurrences of Roman numerals within a string.

    Args:
        text: The input string to search.

    Returns:
        A list of strings, where each string is a matched Roman numeral.
        Returns an empty list if no Roman numerals are found.
    """
    roman_pattern = r"\bM{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b"
    roman_map = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    result = 0
    i = 0

    test = re.search(roman_pattern, text, re.IGNORECASE)

    if test:
        logger.debug(f"Roman Numeral Found: {test}")
        test = test.group(0)
        while i < len(test):
            if i + 1 < len(test) and roman_map[test[i]] < roman_map[test[i + 1]]:
                result += roman_map[test[i + 1]] - roman_map[test[i]]
                i += 2
            else:
                result += roman_map[test[i]]
                i += 1
        logger.debug(f"Roman Numerals converted: {result}")
        text = re.sub(test, f"{result}", text)
        logger.debug(f"New Header: {text}")
        return result, text
    else:
        return result, text


def convert_integer(text: str, old_integer: int, new_integer: int) -> str:
    """
    Finds the first occurrence of an integer in a string and replaces it with a new integer.

    Args:
        text: The input string to search.
        old_integer: The integer to be replaced.
        new_integer: The integer to replace with.

    Returns:
        The modified string with the first occurrence of the old integer replaced by the new integer.
        Returns the original string if the old integer is not found.
    """

    escaped_new_integer = str(new_integer)

    # Escape the old integer in the regex pattern to prevent it from being treated as a special character
    escaped_old_integer = str(old_integer)

    # Perform the replacement using re.sub
    modified_text = re.sub(escaped_old_integer, escaped_new_integer, text)

    return modified_text


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


def find_integer(text: str) -> int:
    """
    Finds the first integer within a string.

    Args:
        text: The input string to search.

    Returns:
        The integer value found in the string, or None if no integer is found.
    """
    match = re.search(r"\d+", text)  # Use \d+ to match one or more digits
    if match:
        return int(match.group(0))
    else:
        return 0


def format_header(header: str, last_value: int) -> tuple[int, str]:
    # Changing Header Numbers
    # Assuming header has roman Numerals
    # Convert Roman Numerals
    value, header = convert_roman_numerals(header)
    if value == 0:
        # Assuming Header Already has an Integer
        value = find_integer(header)
        if value == 0:
            logger.warning(f"No Integer found for {header}, returning same value")
            return last_value, header

    if value == last_value:
        logger.warning("last known value matches current value, returning same value")
        return last_value, header
    elif value < last_value:
        last_value = last_value + 1
        header = convert_integer(header, value, last_value)
        logger.debug(f"New Header Integer: {header}")
        return last_value, header
    elif value > last_value:
        if value - last_value == 1:
            last_value = value
            logger.debug(f"Header Integer is incrementing last_value: {header}")
            return last_value, header
        else:
            logger.error("Skipped Header Numbers")
            raise


def format_summary_file(filepath) -> None:
    # start_tag = "**Outline**"
    end_tag = "**End Outline**\n"
    header_format = "[*][*].*[*][*]"
    last_value = 0
    try:
        logger.debug(f"{datetime.now()}: Starting Summary File Edit")
        # Step 1 - Split text into Blocks by tag
        text = read_file(input_file)
        summary = split_into_chunks(text, end_tag)
        # Step 2 - Split Blocks into Section by Heading
        for block_index, block in enumerate(summary):
            logger.debug(f"Block Index: {block_index}")
            # Find All Headers
            headers = re.findall(header_format, block)
            for index, item in enumerate(headers):
                # Access the next element using the current index + 1
                next_index = index + 1
                # Outline Sections
                if next_index < len(headers):  # Add this check to prevent errors
                    next_item = headers[next_index]
                    section = split_into_chunks(block, next_item)
                    block = section[1]
                    # Section 0
                    if index == 0:
                        # Skipping Introductory statements
                        if re.search(
                            "Here.*is.*(outline|summary|Outline|Summary)", section[0]
                        ):
                            logger.debug(
                                f"Skipping Block:{block_index} Section:{index}"
                            )
                        else:
                            # Trim Header from First Section
                            section = split_into_chunks(section[0], item)
                            logger.debug(
                                f"Summary Block {index} '{item}': {section[0]}"
                            )
                            last_value, item = format_header(item, last_value)
                    # Middle Sections
                    else:
                        logger.debug(f"Summary Block {index} '{item}': {section[0]}")
                        last_value, item = format_header(item, last_value)
                # Last Section
                else:
                    section = split_into_chunks(block, item)
                    logger.debug(f"Summary Block {index} '{item}': {section[0]}")
                    last_value, item = format_header(item, last_value)

    except FileNotFoundError:
        logger.error(f"{datetime.now()}: Error: File not found at {input_file}")
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


def split_into_chunks(text: str, delimiter: str, replacement=None) -> list:
    """
    Splits a text string into blocks based on a delimiter,
    handling multiple occurrences of the delimiter.

    Args:
        text: The input text string.
        delimiter: The delimiter string to split the text by.

    Returns:
        A list of strings, where each string is a block.
    """

    blocks = []
    split_text = text.split(delimiter)

    if replacement:
        for item in split_text:
            if bool(item):
                blocks.append(item + replacement)
    else:
        for item in split_text:
            if bool(item):
                blocks.append(item)

    return blocks


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # Summary Edit
    repo_root = os.getcwd()
    summary = f"{repo_root}/downloads/AWS_re_-Invent_2025_-_Keynote_with_CEO_Matt_Garman/summary.md"
    format_summary_file(summary)
