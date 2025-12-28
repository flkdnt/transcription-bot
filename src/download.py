import logging
import os
from datetime import datetime

import yt_dlp

logger = logging.getLogger(__name__)


def download_audio(url, output_dir, noplaylist="False"):
    """
    Downloads audio from a YouTube URL using yt-dlp.

    This function utilizes the yt-dlp library to download audio from a
    given YouTube video URL. It employs a specific postprocessor to extract
    the audio in WAV format and saves it to the specified output directory.

    Args:
        url (str): The URL of the YouTube video.
        output_dir (str): The directory where the downloaded audio file
            should be saved. The function will create this directory if
            it doesn't exist.
        noplaylist (str, optional): A flag indicating whether to handle
            playlists. Defaults to "False".

    Returns:
        str: The full path to the downloaded audio file if the download
             was successful, otherwise None.
    """

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    options = {
        "outtmpl": os.path.join(
            f"{output_dir}/%(title)s", "video.%(ext)s"
        ),  # Customize filename
        "logger": logger,
        "extractor_args": {"youtube": {"player_client": ["default"]}},
        "restrictfilenames": "True",
        "format": "bestaudio",  # Download the best quality
        # "keepvideo": "True",
        "noplaylist": noplaylist,
        "writeinfojson": "True",
        "postprocessors": [
            # {  # Convert to m4a(mp4)
            #    "key": "FFmpegVideoConvertor",
            #    "preferedformat": "m4a",
            # },
            {  # Extract audio using ffmpeg
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
                "nopostoverwrites": "true",
            },
        ],
    }

    download = ytdlp_download(options, url)

    if validate_file(download, "video", ".wav"):
        logger.info(
            f"{datetime.now()}: Audio file video.wav has been Downloaded to: {download}"
        )
        return download
    else:
        logger.info(f"{datetime.now()}: Audio file video.wav has NOT been Downloaded!")
        return None


def download_subtitles(url, output_dir, noplaylist="False"):
    """
    Downloads subtitles from a YouTube URL using yt-dlp.

    This function utilizes the yt-dlp library to download subtitle files
    from a given YouTube video URL. It constructs the output filename
    using a predefined template and handles any potential errors during
    the download process.

    Args:
        url (str): The URL of the YouTube video.
        output_dir (str): The directory where the downloaded subtitle file
            should be saved. The function will create this directory if it
            doesn't exist.
        noplaylist (str, optional):  A flag indicating whether to handle
            playlists. Defaults to "False".

    Returns:
        str: The full path to the downloaded subtitle file if the download
             was successful, otherwise None.
    """

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    options = {
        "outtmpl": os.path.join(
            f"{output_dir}/%(title)s", "video.%(ext)s"
        ),  # Customize filename
        "logger": logger,
        "extractor_args": {"youtube": {"player_client": ["default"]}},
        "restrictfilenames": "True",
        "noplaylist": noplaylist,
        "writeinfojson": "True",
        "writesubtitles": "True",
        # "writeautomaticsub": "True",
        "skip_download": "True",
        "subtitlesformat": "vtt",
        # "subtitleslangs": "en",
    }

    download = ytdlp_download(options, url)

    if validate_file(download, "video", ".vtt"):
        logger.info(
            f"{datetime.now()}: Subtitle File video*.vtt has been Downloaded to: {download}"
        )
        return download
    else:
        logger.info(
            f"{datetime.now()}: Subtitle File video*.vtt has Not been Downloaded!"
        )
        return None


def download_video(url, output_dir, noplaylist="False"):
    """
    Downloads a video from a YouTube URL using yt-dlp.

    This function utilizes the yt-dlp library to download a video from a
    given YouTube URL. It downloads the best quality video and audio
    streams and then converts the combined stream to an m4a(mp4) format.
    It saves the downloaded file to the specified output directory.

    Args:
        url (str): The URL of the YouTube video.
        output_dir (str): The directory where the downloaded video file
            should be saved. The function will create this directory if
            it doesn't exist.
        noplaylist (str, optional): A flag indicating whether to handle
            playlists. Defaults to "False".

    Returns:
        str: The full path to the downloaded video file if the download
             was successful, otherwise None.
    """

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    options = {
        "outtmpl": os.path.join(
            f"{output_dir}/%(title)s", "video.%(ext)s"
        ),  # Customize filename
        "logger": logger,
        "extractor_args": {"youtube": {"player_client": ["default"]}},
        "restrictfilenames": "True",
        "format": "bestvideo+bestaudio/best",  # Download the best quality
        "noplaylist": noplaylist,
        "writeinfojson": "True",
        "print": "after_move:filename",
        "postprocessors": [
            {  # Convert to m4a(mp4)
                "key": "FFmpegVideoConvertor",
                "preferedformat": "m4a",
            }
        ],
    }

    download = ytdlp_download(options, url)

    if validate_file(download, "video", ".m4a"):
        logger.info(
            f"{datetime.now()}: Video File video.m4a has been Downloaded to: {download}"
        )
        return download
    else:
        logger.info(f"{datetime.now()}: Video File video.m4a has Not been Downloaded!")
        return None


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
             Returns None if the input `filename` is empty.
    """
    if not filename:
        logger.warning("No parameter 'filename' passed to format_path")
        return None

    parts = filename.split(os.sep)
    if len(parts) > 1:
        return os.path.join(*parts[:-1])
    else:
        return filename


def validate_file(path, start_filter, end_filter):
    """
    Searches for a file within a given path that starts with 'start_filter' and ends with 'end_filter'

    Args:
        path: The directory to search within.

    Returns:
        True if file exists or False if it doesn't exists
    """
    try:
        files = os.listdir(path)
        found = False
        logger.info(f"{datetime.now()}: validate_files - 'files' var: {files}")
        for filename in files:
            if filename.startswith(start_filter) and filename.endswith(end_filter):
                found = True
                break

        return found

    except FileNotFoundError:
        return None


def ytdlp_download(options, url):
    """
    Downloads a file from a YouTube URL using yt-dlp.

    This function utilizes the yt-dlp library to download a file from a
    given YouTube URL. It handles filename formatting and validation
    after the download.

    Args:
        options (dict): A dictionary containing yt-dlp download options.
        url (str): The URL of the YouTube video.
        pre_filter (str): A string to prepend to the log message.
        post_filter (str): A string to append to the log message.

    Returns:
        str: The full path to the downloaded file if successful,
             otherwise None.
    """
    logger.info(f"{datetime.now()}: Starting Download of {url}...")

    with yt_dlp.YoutubeDL(params=options) as ydl:
        info = ydl.extract_info(url, download=True)
        fname = ydl.prepare_filename(info)
        ydl.close()

    fname = format_path(fname)

    return fname


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    video_url = ""
    download_directory = "downloads"  # Specify your desired download directory
    subtitles = download_subtitles(video_url, download_directory)
    if subtitles is None:
        download_audio(video_url, download_directory)
