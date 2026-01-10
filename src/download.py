import logging
import os
from datetime import datetime

import yt_dlp

from utility_os import format_path, validate_file

logger = logging.getLogger(__name__)


def download_audio(url, output_dir, noplaylist="False") -> str | None:
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
        # Customize filename
        "outtmpl": os.path.join(f"{output_dir}/%(title)s", "video.%(ext)s"),
        # Download Archive
        "download_archive": f"{output_dir}/archive.txt",
        # Integrate with the Logger object
        "logger": logger,
        # Specifying site and Client
        "extractor_args": {"youtube": {"player_client": ["default"]}},
        # Best Practice for file names
        "restrictfilenames": "True",
        # Download the best Audio quality
        "format": "bestaudio",
        # Only needed if we grab screenshots from video
        # "keepvideo": "True",
        # noplaylist param(We might not want to download entire playlists)
        "noplaylist": noplaylist,
        # Don't overwrite video/audio
        "overwrites": False,
        # Needed for Metadata
        "writeinfojson": "True",
        "postprocessors": [
            # Only needed if we grab screenshots from video
            # {  # Convert to m4a(mp4)
            #    "key": "FFmpegVideoConvertor",
            #    "preferedformat": "m4a",
            # },
            # Extract audio using ffmpeg
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
                "nopostoverwrites": "true",
            },
        ],
    }

    download = ytdlp_download(options, url)
    download = format_path(download)
    logger.debug(f"{datetime.now()}:download_video: var download = {download} ")

    if validate_file(download, "video", ".wav"):
        logger.info(
            f"{datetime.now()}: Audio file video.wav has been Downloaded to: {download}"
        )
        return download
    else:
        logger.info(f"{datetime.now()}: Audio file video.wav has NOT been Downloaded!")
        return None


def download_subtitles(url, output_dir, noplaylist="False") -> str | None:
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
        # Download Archive
        "download_archive": f"{output_dir}/archive.txt",
        "logger": logger,
        "extractor_args": {"youtube": {"player_client": ["default"]}},
        "restrictfilenames": "True",
        "noplaylist": noplaylist,
        "overwrites": False,
        "writeinfojson": "True",
        "writesubtitles": "True",
        # "writeautomaticsub": "True",
        "skip_download": "True",
        "subtitlesformat": "vtt",
        # "subtitleslangs": "en",
    }

    download = ytdlp_download(options, url)
    home_folder = format_path(download)
    logger.debug(f"{datetime.now()}:download_video: var download = {download} ")

    filepath = validate_file(home_folder, "video", ".vtt", return_path=True)

    if filepath:
        logger.info(
            f"{datetime.now()}: Subtitle File video*.vtt has been Downloaded to: {home_folder}"
        )
        # Rename to a consistent filename
        new_name = f"{home_folder}/subtitles.txt"
        if type(filepath) is str:
            os.rename(filepath, new_name)
        else:
            logger.error("var 'filepath' is not a string!")
            raise
        logger.debug(
            f"{datetime.now()}: Subtitle File video*.vtt has been Renamed to: {new_name}"
        )
        # return directory
        return home_folder
    else:
        logger.warning(
            f"{datetime.now()}: Subtitle File video*.vtt has Not been Downloaded!"
        )
        return None


def download_video(url, output_dir, noplaylist="False") -> str | None:
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
        # Customize filename
        "outtmpl": os.path.join(f"{output_dir}/%(title)s", "video.%(ext)s"),
        # Download Archive
        "download_archive": f"{output_dir}/archive.txt",
        "logger": logger,
        "extractor_args": {"youtube": {"player_client": ["default"]}},
        "restrictfilenames": "True",
        "format": "bestvideo+bestaudio/best",  # Download the best quality
        "noplaylist": noplaylist,
        "overwrites": False,
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
    download = format_path(download)
    logger.debug(f"{datetime.now()}:download_video: var download = {download} ")

    if validate_file(download, "video", ".m4a"):
        logger.info(
            f"{datetime.now()}: Video File video.m4a has been Downloaded to: {download}"
        )
        return download
    else:
        logger.warning(
            f"{datetime.now()}: Video File video.m4a has Not been Downloaded!"
        )
        return None


def ytdlp_download(options, url) -> str | None:
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

    return fname


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    video_url = ""
    download_directory = "downloads"  # Specify your desired download directory
    subtitles = download_subtitles(video_url, download_directory)
    if subtitles is None:
        download_audio(video_url, download_directory)
