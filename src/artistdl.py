import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
import requests
from ytmusicapi import YTMusic
import yt_dlp
from dotenv import load_dotenv


class MusicDownloaderError(Exception):
    """Custom exception for music downloader errors"""

    pass


class LastFMClient:
    """Client for Last.fm API interactions"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://ws.audioscrobbler.com/2.0/"
        self.logger = logging.getLogger(__name__ + ".LastFMClient")

    def get_top_tracks(self, artist_name: str, limit: int = 50) -> List[str]:
        """
        Get top tracks for an artist from Last.fm

        Args:
            artist_name: Name of the artist
            limit: Maximum number of tracks to retrieve

        Returns:
            List of track names

        Raises:
            MusicDownloaderError: If API request fails or no tracks found
        """
        self.logger.info(f"Fetching top {limit} tracks for artist: {artist_name}")

        params = {
            "method": "artist.gettoptracks",
            "artist": artist_name,
            "api_key": self.api_key,
            "format": "json",
            "limit": limit,
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if "toptracks" not in data or "track" not in data["toptracks"]:
                self.logger.error(f"No tracks found for artist: {artist_name}")
                self.logger.debug(f"API response: {data}")
                raise MusicDownloaderError(f"No tracks found for artist: {artist_name}")

            tracks = data["toptracks"]["track"]
            track_names = [track["name"] for track in tracks]

            self.logger.info(f"Found {len(track_names)} tracks for {artist_name}")
            self.logger.debug(f"Track names: {track_names}")

            return track_names

        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch tracks for {artist_name}: {e}")
            raise MusicDownloaderError(f"Failed to fetch tracks: {e}")


class YouTubeMusicClient:
    """Client for YouTube Music interactions"""

    def __init__(self):
        self.ytmusic = YTMusic()
        self.logger = logging.getLogger(__name__ + ".YouTubeMusicClient")

    def search_song(self, artist: str, track: str) -> Optional[Dict]:
        """
        Search for a song on YouTube Music

        Args:
            artist: Artist name
            track: Track name

        Returns:
            Dictionary containing song information or None if not found
        """
        query = f"{artist} - {track}"
        self.logger.debug(f"Searching YouTube Music for: {query}")

        try:
            results = self.ytmusic.search(query, filter="songs")

            if not results:
                self.logger.warning(f"No results found for: {query}")
                return None

            song = results[0]
            song_info = {
                "videoId": song.get("videoId"),
                "title": song.get("title"),
                "artists": [a["name"] for a in song.get("artists", [])],
                "album": (
                    song.get("album", {}).get("name") if song.get("album") else None
                ),
                "duration": song.get("duration"),
                "resultType": song.get("resultType"),
            }

            self.logger.debug(
                f"Found song: {song_info['title']} by {song_info['artists']}"
            )
            return song_info

        except Exception as e:
            self.logger.error(f"Error searching for '{query}': {e}")
            return None


class AudioDownloader:
    """Handler for audio downloading using yt-dlp"""

    def __init__(self, base_output_dir: str = "downloads", audio_format: str = "mp3"):
        self.base_output_dir = Path(base_output_dir)
        self.audio_format = audio_format
        self.logger = logging.getLogger(__name__ + ".AudioDownloader")

    def download_song(self, video_id: str, output_subdir: str = "") -> Optional[str]:
        """
        Download a song by video ID

        Args:
            video_id: YouTube video ID
            output_subdir: Subdirectory within base output directory

        Returns:
            Path to downloaded file or None if download failed
        """
        if not video_id:
            self.logger.error("No video ID provided for download")
            return None

        output_dir = (
            self.base_output_dir / output_subdir
            if output_subdir
            else self.base_output_dir
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        url = f"https://music.youtube.com/watch?v={video_id}"
        self.logger.info(f"Downloading from: {url}")
        self.logger.info(f"Output directory: {output_dir}")

        ydl_opts = {
            "cookiefile": "cookies.txt",
            "format": "bestaudio/best",
            "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
            "quiet": True,  # Suppress yt-dlp output, use our logging instead
            "noplaylist": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": self.audio_format,
                    "preferredquality": "192",
                }
            ],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                output_file = ydl.prepare_filename(info).replace(
                    info["ext"], self.audio_format
                )

                self.logger.info(f"Successfully downloaded: {info.get('title')}")
                self.logger.debug(f"Output file: {output_file}")

                return output_file

        except Exception as e:
            self.logger.error(f"Failed to download video {video_id}: {e}")
            return None


class MusicDownloader:
    """Main class to manage music downloads"""

    def __init__(
        self,
        lastfm_api_key: str,
        output_dir: str = "downloads",
        audio_format: str = "mp3",
    ):
        self.lastfm_client = LastFMClient(lastfm_api_key)
        self.ytmusic_client = YouTubeMusicClient()
        self.audio_downloader = AudioDownloader(output_dir, audio_format)
        self.logger = logging.getLogger(__name__ + ".MusicDownloader")

    def download_artist_top_tracks(
        self, artist: str, limit: int = 50
    ) -> Dict[str, int]:
        """
        Download top tracks for an artist

        Args:
            artist: Artist name
            limit: Maximum number of tracks to download

        Returns:
            Dictionary with download statistics
        """
        if not artist:
            raise ValueError("Artist name cannot be empty")

        self.logger.info(
            f"Starting download process for artist: {artist} (limit: {limit})"
        )

        # Get top tracks from Last.fm
        try:
            top_tracks = self.lastfm_client.get_top_tracks(artist, limit)
        except MusicDownloaderError as e:
            self.logger.error(f"Failed to get top tracks: {e}")
            return {"total": 0, "found": 0, "downloaded": 0, "failed": 0}

        # Search for tracks on YouTube Music
        found_tracks = []
        for track in top_tracks:
            self.logger.debug(f"Searching for: {artist} - {track}")
            track_data = self.ytmusic_client.search_song(artist, track)
            found_tracks.append(track_data)

        # Filter out None results
        valid_tracks = [track for track in found_tracks if track is not None]

        self.logger.info(
            f"Found {len(valid_tracks)} out of {len(top_tracks)} tracks on YouTube Music"
        )

        # Download tracks
        downloaded_count = 0
        failed_count = 0

        for i, track in enumerate(valid_tracks, 1):
            if not track:
                continue

            self.logger.info(
                f"Downloading track {i}/{len(valid_tracks)}: {track.get('title')}"
            )

            # Use first artist name for subdirectory
            artist_name = (
                track.get("artists", [artist])[0] if track.get("artists") else artist
            )
            result = self.audio_downloader.download_song(
                track.get("videoId"), artist_name
            )

            if result:
                downloaded_count += 1
                self.logger.info(f"Successfully downloaded: {track.get('title')}")
            else:
                failed_count += 1
                self.logger.warning(f"Failed to download: {track.get('title')}")

        stats = {
            "total": len(top_tracks),
            "found": len(valid_tracks),
            "downloaded": downloaded_count,
            "failed": failed_count,
        }

        self.logger.info(f"Download completed. Stats: {stats}")
        return stats


def main():
    """Main function"""
    # Load environment variables
    load_dotenv()

    # Setup logging
    setup_logging("DEBUG")  # Change to "DEBUG" for more detailed logs
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
