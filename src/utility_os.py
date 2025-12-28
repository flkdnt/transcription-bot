import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


def delete_media_files(directory):
    """
    Deletes all files from a specified directory that start with the prefix "video".
    These files are likely downloaded media files, possibly from a service like YouTube (yt-dlp).
    Example Files: video.info.json, video.webm, video.wav, video.en.vtt, etc.

    Args:
        directory (str): The path to the directory from which to delete files.

    Returns:
        None.  The function performs the deletion directly.

    Raises:
        Exception: If any error occurs during the file deletion process.
    """
    try:
        for root, directories, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                if os.path.isfile(filepath) and filename.startswith("video"):
                    os.remove(filepath)
                    logger.debug(f"{datetime.now()}: Deleted {filepath}")
    except Exception as e:
        logger.error(f"{datetime.now()}: Error deleting files: {e}")


def format_path(filename):
    """
    Trims the filename from the end of a path and returns the path itself.

    This function removes the filename from the end of a given path string,
    returning the remaining path. It handles cases where the input filename
    is empty or if the path consists of only a single part.

    Args:
        filename (str): The path string from which to remove the filename.

    Returns:
        str: The path string with the filename removed.
    """

    if not filename:
        logger.error("No parameter 'filename' passed to format_path")
        exit()

    try:
        parts = filename.split(os.sep)
        if len(parts) > 1:
            if parts[0] == "":
                parts[0] = "/"
        dir = os.path.join(*parts[:-1])
        # logger.debug(f"{datetime.now()}:format_path: var dir = {dir}")
        return dir
    except Exception as e:
        logger.error(f"{datetime.now()}: An error occurred in format_path: {e}")
        raise


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
        raise
    except Exception as e:
        logger.error(f"{datetime.now()}: An error occurred: {e}")
        raise


def validate_file(path, start_filter, end_filter, return_path=False):
    """
    Searches for a file within a given path that starts with 'start_filter' and ends with 'end_filter'

    Args:
        path: The directory to search within.
        start_filter (str): The string to start the filename with.
        end_filter (str): The string to end the filename with.
        return_path (bool, optional): If True, returns the full path to the file. Defaults to False.

    Returns:
        bool: True if a matching file is found, False otherwise.
    """
    try:
        files = os.listdir(path)
        found = False
        logger.debug(f"{datetime.now()}: validate_files - 'files' var: {files}")
        for filename in files:
            if filename.startswith(start_filter) and filename.endswith(end_filter):
                found = True
                fullpath = f"{path}/{filename}"
                if return_path:
                    return fullpath
        else:
            return found

    except FileNotFoundError:
        logger.error(f"{datetime.now()}: Directory not found: {path}")
        raise  # Raise the FileNotFoundError


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
        logger.error(
            f"{datetime.now()}: An error occurred while writing to {file_path}: {e}"
        )
        raise
