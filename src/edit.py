import json
import logging
import os
import re
from datetime import datetime

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


def format_header(header: str, index: int, prefix: str) -> str:
    """Formats a header string with a sequential number prefix.

    This function modifies a header string by adding a prefix (e.g., "1.", "2.")
    and ensuring the number is correctly formatted, handling potential existing
    numbers in the header.

    Args:
        header: The input header string.
        index: The sequential index to be added as a prefix.
        prefix: The prefix of the header to be filtered on (e.g., "###", "**").

    Returns:
        The modified header string with the formatted index.

    Raises:
        TypeError: If any of the input arguments have an incorrect type.

    Example:
        format_header("# This Is a MarkDown Header", 4, "#") == "# 4 This Is a MarkDown Header"
    """
    # Starting count at 1
    index = index + 1
    # Find any current numbers
    match = re.search(r"([0-9]{1,4}\.[0-9]{1,4})|([0-9]{1,4}\.)", header)
    # logger.debug(f"find_integer: Match Object {match}")
    if match:
        if header.startswith(prefix):
            # Escape Index Value
            escaped_new_integer = str(index)
            # Escape the old integer in the regex pattern to prevent it from being treated as a special character
            escaped_old_integer = str(match.group(0))
            # Perform the replacement using re.sub
            header = re.sub(escaped_old_integer, escaped_new_integer, header, count=1)
        else:
            # Escape Index Value
            escaped_new_integer = str(index)
            escaped_new_integer = f"{prefix} {escaped_new_integer}"
            # Escape the old integer in the regex pattern to prevent it from being treated as a special character
            escaped_old_integer = str(match.group(0))
            # Perform the replacement using re.sub
            header = re.sub(escaped_old_integer, escaped_new_integer, header, count=1)

    else:
        logger.info(
            f"No Header Numbers found for {header}, inserting new Header Number"
        )
        if header.startswith(prefix):
            # Escape Index Value
            escaped_new_integer = str(index)
            escaped_new_integer = f"{prefix} {escaped_new_integer}"
            # Perform the replacement using re.sub
            header = re.sub(prefix, escaped_new_integer, header, count=1)
        else:
            # Escape Index Value
            escaped_new_integer = str(index)
            escaped_new_integer = f"{prefix} {escaped_new_integer}"
            # Perform the replacement using re.sub
            header = re.sub(r"^", escaped_new_integer, header, count=1)

    logger.debug(f"New Header Integer: {header}")
    return header


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

        # Remove markers
        content = re.sub(r"&gt;", "", content)

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


def split_text(input_file: str, prefix: str, header=True) -> list[dict[str, str]]:
    """Splits a text file into sections based on a given prefix.

    This function reads a text file, splits it into sections using a regular
    expression that matches lines starting with the specified prefix, and returns
    a list of dictionaries, where each dictionary represents a section
    with the section header as the key and the section content as the value.

    Args:
        input_file: The path to the input text file to be split.
        prefix: The prefix string to use for splitting the file.
        header: A boolean flag indicating whether to format the header section
                using the `format_header` function. Defaults to True.

    Returns:
        A list of dictionaries, where each dictionary represents a section
        with the section header as the key and the section content as the
        value.

    Raises:
        FileNotFoundError: If the input file does not exist.
        Exception: If any other unexpected error occurs during the process.
        TypeError: If any of the arguments have an incorrect type.

    Example:
        # Assume you have a file named 'input.txt' with the following content:
        # ### Section 1
        # This is the content of section 1.
        # ### Section 2
        # This is the content of section 2.

        # After running split_text("input.txt", "###"),
        # the function will return:
        # [{'### Section 1': 'This is the content of section 1.',
        #   '### Section 2': 'This is the content of section 2.'}]
    """
    split_text = []
    filter = f"{prefix}.*"

    try:
        logger.debug(f"{datetime.now()}: Starting File Split")
        # Step 1 - Read File and Grab divisions
        text = read_file(input_file)
        divisions = re.findall(filter, text)
        index_size = len(divisions)
        for index, division in enumerate(divisions):
            lt_raw = []
            rt_raw = []
            rt_section = []
            section = []
            # Access the next element using the current index + 1
            next_index = index + 1
            # logger.debug(f"{datetime.now()}: Index {index}: {division}")
            # Sections
            if next_index < index_size:  # Add this check to prevent errors
                next_division = divisions[next_index]
                # Right Trim - Split on next division
                rt_section = text.split(next_division)
                # Iterate through split for only non-empty values
                for item in rt_section:
                    if bool(item):
                        rt_raw.append(item)
                # Left Trim - split on current division
                lt_raw = rt_raw[0].split(division)

                if len(lt_raw) > 1:
                    section = lt_raw[1]
                else:
                    logger.debug(
                        f"section: {section}\nrt_section: {rt_section}\nlt_raw: {lt_raw}\nrt_raw: {rt_raw}"
                    )
                    logger.error(
                        f"ERROR SPLITTING TEXT: DIVISION {index}: {division} not found!"
                    )
            else:
                raw = []
                section = []
                # Left Trim - split on current division
                raw = text.split(division)
                if len(raw) > 1:
                    section = raw[1]
                else:
                    logger.debug(f"section: {section}\nraw: {raw}")
                    logger.error(
                        f"ERROR SPLITTING TEXT: LAST DIVISION{division} not found!"
                    )
            # logger.debug(f"Section {index}: '{division}': {section}")
            split_text.append({f"{division}": f"{section}"})
        # After List is built, Return Split Text
        logger.debug(f"{datetime.now()}: Ending File Split")
        return split_text
    except FileNotFoundError:
        logger.error(f"{datetime.now()}: Error: File not found at {input_file}")
        raise
    except Exception as e:
        logger.error(f"{datetime.now()}: An error occurred: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # Summary Edit
    repo_root = os.getcwd()
    chapters = f"{repo_root}/downloads/AWS_re_-Invent_2025_-_Keynote_with_CEO_Matt_Garman/chapters.md"
    summary = f"{repo_root}/downloads/AWS_re_-Invent_2025_-_Keynote_with_CEO_Matt_Garman/summary.md"
    # Split text by Chapter
    sections = split_text(input_file=chapters, prefix="###")
