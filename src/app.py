import logging
import os
from pathlib import Path
from ytmusicapi import YTMusic
from dotenv import load_dotenv

from util import setup_logging
from artistdl import MusicDownloader


def main():
    """Main function"""
    # Load environment variables
    load_dotenv()

    # Setup logging
    setup_logging("DEBUG")
    logger = logging.getLogger(__name__)

    # Get API key
    api_key = os.getenv("LAST_FM_KEY")
    if not api_key:
        logger.error("LAST_FM_KEY not found in environment variables")
        return

    # Initialize downloader
    try:
        downloader = MusicDownloader(api_key)

        # Download top tracks for an artist
        artist = "Cerulean"
        limit = 10

        logger.info(f"Starting download for {artist}")
        stats = downloader.download_artist_top_tracks(artist, limit)

        logger.info("Download process completed!")
        logger.info(f"Final statistics: {stats}")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)


if __name__ == "__main__":
    main()
