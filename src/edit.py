import json
import logging
import os
import re
from datetime import datetime

from utility_llm import send_prompt
from utility_os import format_path, read_file, write_file

logger = logging.getLogger(__name__)


def clean_string(input_string):
    """
    Removes double or single quotation marks from a string.

    Args:
        input_string: The string to clean.

    Returns:
        A new string with all quotation marks removed.
    """
    cleaned_string = input_string.replace('"', "").replace("'", "")
    return cleaned_string


def convert_roman_numerals(text: str) -> tuple[int, str]:
    """
    Converts a string containing Roman numerals to its integer equivalent.

    This function attempts to identify and convert Roman numeral patterns within a given
    string into their corresponding integer values.  If successful, the original
    string is updated to remove the Roman numeral representation and replace it with
    the integer value.

    Args:
        text: The input string potentially containing Roman numerals.

    Returns:
        A tuple containing:
            - The integer value of the converted Roman numeral.
            - The modified string with the Roman numeral replaced by its integer equivalent.

    Raises:
        TypeError: If the input argument `text` is not a string.
        Exception: If any other unexpected error occurs during the process.

    Example:
        >>> convert_roman_numerals("I V XI")
        (15, '1 5 11')
        >>> convert_roman_numerals("XIV")
        (14, '14')
        >>> convert_roman_numerals("MCMLXXXIV")
        (1984, '1984')
    """
    roman_pattern = r"\bM{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b"
    roman_map = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    result = 0
    i = 0

    test = re.search(roman_pattern, text, re.IGNORECASE)

    if test:
        test = test.group(0)
        if test:
            logger.debug(f"Roman Numeral Found: {test}")
            for i in range(len(test)):
                if i > 0 and roman_map[test[i]] > roman_map[test[i - 1]]:
                    result += roman_map[test[i]] - 2 * roman_map[test[i - 1]]
                else:
                    result += roman_map[test[i]]
            logger.debug(f"Roman Numeral Integer Eqivalent: {result}")
            text = re.sub(test, f"{result}", text, count=1)
            logger.debug(f"New Header: {text}")

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
    modified_text = re.sub(escaped_old_integer, escaped_new_integer, text, count=1)

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
    match = re.search(r"[0-9]{1-4}", text)
    logger.debug(f"find_integer: Match Object {match}")
    if match:
        return int(match.group(0))
    else:
        return 0


def format_header(
    header: str,
    last_value: int,
    header_section: str,
    llm_host: str,
    llm_model: str,
    last_section=False,
) -> tuple[int, str]:
    """
    Formats a header string based on its content, integer value, and context.

    This function processes a header string, potentially converting Roman numerals
    to integers, updating the integer value if necessary, and reformatting the
    header using an LLM if the formatting rules are met.

    Args:
        header: The header string to be formatted. This string may contain
            Roman numerals or a numerical value.
        last_value: The integer value of the previously formatted header.
        header_section: The content of the section related to the header.
        llm_host: The hostname or IP address of the LLM service.
        llm_model: The name of the LLM model to use.
        last_section: A boolean flag indicating whether this is the last section
            in a group (True) or not (False).

    Returns:
        A tuple containing:
            - The updated integer value of the header.
            - The formatted header string.

    Raises:
        TypeError: If any of the arguments have an incorrect type.
        Exception: If any other unexpected error occurs during the process.
        ValueError: If the header contains invalid Roman numerals or integers.
    """
    # Convert Roman Numerals(Assuming header has Roman Numerals)
    value, header = convert_roman_numerals(header)
    if value == 0:
        # Assuming Header Already has an Integer
        value = find_integer(header)
        if value == 0:
            logger.warning(f"No Integer found for {header}, returning same value")
            return last_value, header

    # Header Integer Updating
    if value == last_value:
        logger.warning("last known value matches current value, returning same value")
    elif value < last_value:
        last_value = last_value + 1
        header = convert_integer(header, value, last_value)
        logger.debug(f"New Header Integer: {header}")
    elif value > last_value:
        if value - last_value == 1:
            last_value = value
            logger.debug(f"Header Integer is incrementing last_value: {last_value}")

        else:
            logger.error("Skipped Header Numbers")
            raise

    # Cleaning Up header itself
    if last_value > 1:
        if (re.search("introduction", header, re.IGNORECASE) and (last_value > 1)) or (
            re.search("conclusion", header, re.IGNORECASE) and (last_section is False)
        ):
            header_list = send_prompt(
                input=[header_section],
                instructions="You are a silent editor\nReturn a Title of 5 words or less based on the information provided",
                host=llm_host,
                model=llm_model,
            )
            new_header = clean_string(header_list[0])
            new_header = f"**{last_value}. {new_header}**"
            logger.debug(f"Header {header} rewrite to {new_header}")
            header = new_header

    return last_value, header


def format_summary_file(
    input_file: str, llm_host: str, llm_model: str, output_file: str
) -> None:
    """
    Formats a summary file by extracting and reformatting sections based on header patterns.

    This function reads a text file containing a summary, splits it into sections
    based on header patterns, and then formats those sections using an external LLM.
    The formatted sections are written to a new output file.

    Args:
        input_file: The path to the input summary file to be formatted.
        llm_host: The hostname or IP address of the LLM service.
        llm_model: The name of the LLM model to use.
        output_file: The path to the output file where the formatted summary will be written.

    Returns:
        None. The function directly writes the formatted summary to the output file.

    Raises:
        FileNotFoundError: If the input file does not exist.
        Exception: If any other unexpected error occurs during the process.
        TypeError: If any of the arguments have an incorrect type.

    Example:
        # Assume you have a file named 'summary.txt' with the following content:

        # **Outline**
        # **I. Introduction**
        # **II. Main Body**
        # **End Outline**
        # **Outline**
        # **III. Conclusion**
        # **End Outline**

        # After running format_summary_file("summary.txt", "localhost", "my_llm", "formatted_summary.txt"),
        # the 'formatted_summary.txt' file will contain:

        # 1. Introduction
        # 2. Main Body
        # 3. Conclusion
    """
    # start_tag = "**Outline**"
    end_tag = "**End Outline**\n"
    header_format = "[*][*].*[*][*]"
    last_value = 0
    last_block = False
    formatted_summary = []
    try:
        logger.debug(f"{datetime.now()}: Starting Summary File Edit")
        # Step 1 - Split text into Blocks by tag
        text = read_file(input_file)
        summary = split_into_chunks(text, end_tag)
        summary_length = len(summary)
        logger.debug(f"Summary Length: {summary_length}")
        # Step 2 - Split Blocks into Section by Heading
        for block_index, block in enumerate(summary):
            if block_index > summary_length:
                logger.warning("Initiating Emergency Break")
                break
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
                            "Here.*(outline|summary|Outline|Summary)", section[0]
                        ):
                            logger.debug(
                                f"Skipping Block:{block_index} Section:{index}"
                            )
                        else:
                            # Trim Header from First Section
                            section = split_into_chunks(section[0], item)
                            logger.debug(
                                f"Summary Block:{block_index} Section:{index} '{item}': {section[0]}"
                            )
                            last_value, item = format_header(
                                header=item,
                                header_section=section[0],
                                llm_host=llm_host,
                                llm_model=llm_model,
                                last_value=last_value,
                            )
                            formatted_summary.append(f"{item}\n{section[0]}")
                    # Middle Sections
                    else:
                        logger.debug(
                            f"Summary Block:{block_index} Section:{index} '{item}': {section[0]}"
                        )
                        last_value, item = format_header(
                            header=item,
                            header_section=section[0],
                            llm_host=llm_host,
                            llm_model=llm_model,
                            last_value=last_value,
                        )
                        formatted_summary.append(f"{item}\n{section[0]}")
                # Last Section
                else:
                    # Check if it's the last block
                    if block_index == summary_length - 1:
                        last_block = True
                        section = split_into_chunks(block, item)
                        logger.debug(
                            f"Summary Block:{block_index} Section:{index} '{item}': {section[0]}"
                        )
                        last_value, item = format_header(
                            header=item,
                            header_section=section[0],
                            llm_host=llm_host,
                            llm_model=llm_model,
                            last_value=last_value,
                            last_section=last_block,
                        )
                        formatted_summary.append(f"{item}\n{section[0]}")
                    else:
                        section = split_into_chunks(block, item)
                        logger.debug(
                            f"Summary Block:{block_index} Section:{index} '{item}': {section[0]}"
                        )
                        last_value, item = format_header(
                            header=item,
                            header_section=section[0],
                            llm_host=llm_host,
                            llm_model=llm_model,
                            last_value=last_value,
                        )
                        formatted_summary.append(f"{item}\n{section[0]}\n")

        for item in formatted_summary:
            # Remove Triple-NewLines
            while re.findall("\n\n\n", item):
                logger.debug(f"{datetime.now()}: Removing Triple-Newlines")
                item = re.sub("\n\n\n", "\n\n", item)
            # Write to file
            write_file(output_file, f"{item}", mode="a", quiet=True)
        logger.info(f"{datetime.now()}: Successfully wrote to {output_file}")

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

    This function splits a given text string into a list of sub-strings
    based on the specified delimiter. It handles multiple occurrences of
    the delimiter by creating separate blocks for each segment.

    Args:
        text: The input text string to be split.  This string should be
              suitable for splitting based on the delimiter.
        delimiter: The string used as a delimiter to split the text.
                   This delimiter will be removed from the resulting chunks.
        replacement: (Optional) A string to append to the end of each
                     resulting chunk. If not provided, the chunks will
                     contain the original text segments.

    Returns:
        A list of strings, where each string represents a chunk of the
        original text.  Empty chunks (strings containing only whitespace)
        are excluded from the returned list.

    Raises:
        TypeError: If `text` is not a string.
        TypeError: If `delimiter` is not a string.

    Examples:
        >>> split_into_chunks("apple,banana,cherry", ",")
        ['apple', 'banana', 'cherry']
        >>> split_into_chunks("apple;banana;cherry", ";", replacement=" - ")
        ['apple - banana - cherry']
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
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Summary Edit
    repo_root = os.getcwd()
    outline = f"{repo_root}/downloads/AWS_re_-Invent_2025_-_Keynote_with_CEO_Matt_Garman/outline.md"
    summary = f"{repo_root}/downloads/AWS_re_-Invent_2025_-_Keynote_with_CEO_Matt_Garman/summary.md"
    format_summary_file(
        input_file=outline,
        llm_host="http://ollama.hf.io:11434",
        llm_model="llama3.2:3b",
        output_file=summary,
    )
