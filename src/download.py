import logging
import os
from datetime import datetime

import yt_dlp


def download_file(url, output_dir, noplaylist="False", logger=None):
    """
    Downloads a file from a URL using yt-dlp.

    Args:
        url: The URL of the file to download.
        output_dir: The directory where the downloaded file should be saved.
    """

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        "outtmpl": os.path.join(
            f"{output_dir}/%(title)s", "video.%(ext)s"
        ),  # Customize filename
        "extractor_args": {"youtube": {"player_client": ["default"]}},
        "restrictfilenames": "True",
        "format": "bestvideo+bestaudio/best",  # Download the best quality
        # "keepvideo": "True",
        "noplaylist": noplaylist,
        "writeinfojson": "True",
        "writesubtitles": "True",
        "writeautomaticsub": "True",
        "subtitlesformat": "vtt",
        # "subtitleslangs": "en",
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

    logger.info(f"{datetime.now()}: Starting Download of {url}...")

    with yt_dlp.YoutubeDL(params=ydl_opts) as ydl:
        ydl.download(url)

    logger.info(f"{datetime.now()}: ...Downloaded to: '{output_dir}'")

    return f"{output_dir}"


if __name__ == "__main__":
    # Configure Logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    video_url = "https://www.youtube.com/watch?v=HhBph2M5ZaU"
    download_directory = "downloads"  # Specify your desired download directory
    download_file(video_url, download_directory)
