import logging
import os

import yt_dlp


def delete_webm_files(directory):
    """
    Deletes all files inside a directory that end with .webm.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".webm"):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                except OSError as e:
                    print(f"Error deleting {file_path}: {e}")


def download_file(url, output_dir):
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
        "keepvideo": "True",
        "postprocessors": [
            {  # Convert to m4a(mp4)
                "key": "FFmpegVideoConvertor",
                "preferedformat": "m4a",
            },
            {  # Extract audio using ffmpeg
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
                "nopostoverwrites": "true",
            },
        ],
    }

    with yt_dlp.YoutubeDL(params=ydl_opts) as ydl:
        ydl.download(url)

    logger.info(f"File downloaded to: '{output_dir}'")

    return f"{output_dir}"


if __name__ == "__main__":
    # Configure Logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # video_url = "https://youtu.be/q3Sb9PemsSo?si=w8aGr1Ss3Gt7eKz5"  # Replace with your desired YouTube URL
    video_url = "https://www.youtube.com/watch?v=HhBph2M5ZaU"
    download_directory = "downloads"  # Specify your desired download directory
    download_file(video_url, download_directory)
    delete_webm_files(download_directory)
