
import logging
import os
import json
from pathlib import Path
import datetime
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic
import yt_dlp

from artistdl import AudioDownloader, Tagger, MusicDownloaderError
from util import setup_logging

# Setup logging
setup_logging("INFO")
logger = logging.getLogger(__name__)


class FavoritesSync:
    def __init__(self, db_file="favorites.json"):
        load_dotenv()
        self.download_dir = Path(os.getenv("DOWNLOAD_DIR", "downloads"))
        self.audio_downloader = AudioDownloader(self.download_dir)
        self.tagger = Tagger()
        self.db_file = Path(db_file)
        self.database = self.load_database()
        if not Path("oauth.json").exists():
            logger.error("oauth.json not found. Please run 'ytmusicapi oauth' to generate it.")
            self.ytmusic = None
        else:
            self.ytmusic = YTMusic("oauth.json")

    def load_database(self) -> dict:
        if self.db_file.exists():
            with open(self.db_file, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {"spotify": [], "ytmusic": []}
        return {"spotify": [], "ytmusic": []}

    def save_database(self):
        with open(self.db_file, "w") as f:
            json.dump(self.database, f, indent=4)

    def is_duplicate(self, song_id: str, platform: str) -> bool:
        return any(song["id"] == song_id for song in self.database.get(platform, []))

    def add_to_database(self, song_id: str, artist: str, track: str, platform: str):
        self.database[platform].append(
            {
                "id": song_id,
                "artist": artist,
                "track": track,
                "download_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            }
        )
        self.save_database()

    def get_spotify_liked_songs(self):
        logger.info("Fetching liked songs from Spotify...")
        try:
            sp = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                    redirect_uri="http://localhost:8888/callback",
                    scope="user-library-read",
                )
            )
            results = sp.current_user_saved_tracks(limit=50)
            liked_songs = []
            while results:
                for item in results["items"]:
                    track = item["track"]
                    artist = track["artists"][0]["name"]
                    song_title = track["name"]
                    liked_songs.append(
                        {"artist": artist, "title": song_title, "id": track["id"]}
                    )
                if results["next"]:
                    results = sp.next(results)
                else:
                    results = None
            logger.info(f"Found {len(liked_songs)} liked songs on Spotify.")
            return liked_songs
        except Exception as e:
            logger.error(f"Could not get Spotify liked songs: {e}")
            return []

    def get_ytmusic_liked_songs(self):
        if not self.ytmusic:
            return []
        logger.info("Fetching liked songs from YouTube Music...")
        try:
            liked_songs = self.ytmusic.get_liked_songs(limit=9999)
            logger.info(
                f"Found {len(liked_songs['tracks'])} liked songs on YouTube Music."
            )
            return liked_songs["tracks"]
        except Exception as e:
            logger.error(f"Could not get YouTube Music liked songs: {e}")
            return []

    def sync(self):
        logger.info("Starting favorites sync...")

        # Sync Spotify
        spotify_songs = self.get_spotify_liked_songs()
        if self.ytmusic:
            for song in spotify_songs:
                if self.is_duplicate(song["id"], "spotify"):
                    logger.debug(f"Skipping duplicate Spotify song: {song['artist']} - {song['title']}")
                    continue

                logger.info(f"Searching for Spotify song: {song['artist']} - {song['title']}")
                yt_song = self.ytmusic.search(f"{song['artist']} {song['title']}", filter="songs", limit=1)
                if yt_song:
                    video_id = yt_song[0]["videoId"]
                    result = self.audio_downloader.download_song(
                        video_id, "Favorites/Spotify"
                    )
                    if result:
                        self.add_to_database(song["id"], song["artist"], song["title"], "spotify")
                        self.tagger.apply_tags(
                            result["output_file"],
                            song["artist"],
                            song["title"],
                            album=yt_song[0].get("album", {}).get("name"),
                            artwork_url=yt_song[0].get("thumbnails", [{}])[0].get("url"),
                        )
                        logger.info(f"Downloaded Spotify favorite: {song['artist']} - {song['title']}")
                    else:
                        logger.error(f"Failed to download Spotify favorite: {song['artist']} - {song['title']}")

        # Sync YouTube Music
        if self.ytmusic:
            ytmusic_songs = self.get_ytmusic_liked_songs()
            for song in ytmusic_songs:
                video_id = song["videoId"]
                if self.is_duplicate(video_id, "ytmusic"):
                    logger.debug(f"Skipping duplicate YouTube Music song: {song['title']}")
                    continue
                
                artist = song['artists'][0]['name'] if song['artists'] else 'Unknown Artist'
                title = song['title']

                result = self.audio_downloader.download_song(
                    video_id, "Favorites/YTMusic"
                )
                if result:
                    self.add_to_database(video_id, artist, title, "ytmusic")
                    self.tagger.apply_tags(
                        result["output_file"],
                        artist,
                        title,
                        album=song.get("album", {}).get("name"),
                        artwork_url=song.get("thumbnails", [{}])[0].get("url"),
                    )
                    logger.info(f"Downloaded YouTube Music favorite: {title}")
                else:
                    logger.error(f"Failed to download YouTube Music favorite: {title}")

        logger.info("Favorites sync finished.")


if __name__ == "__main__":
    sync = FavoritesSync()
    sync.sync()
