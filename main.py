import requests
from ytmusicapi import YTMusic
import yt_dlp
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("LAST_FM_KEY")
BASE_URL = "http://ws.audioscrobbler.com/2.0/"

ytmusic = YTMusic()


def download_song(video_id, output_dir="downloads", audio_format="mp3"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    url = f"https://music.youtube.com/watch?v={video_id}"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "quiet": False,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # print(info)
        return ydl.prepare_filename(info).replace(info["ext"], audio_format)


def search_song_on_ytmusic(artist, track):
    query = f"{artist} {track}"
    results = ytmusic.search(query, filter="songs")

    if not results:
        return None

    song = results[0]
    # return song
    return {
        "videoId": song.get("videoId"),
        "title": song.get("title"),
        "artists": [a["name"] for a in song.get("artists", [])],
        "album": song.get("album", {}).get("name") if song.get("album") else None,
        "duration": song.get("duration"),
        "resultType": song.get("resultType"),
    }


def get_top_tracks(artist_name, limit=50):
    params = {
        "method": "artist.gettoptracks",
        "artist": artist_name,
        "api_key": API_KEY,
        "format": "json",
        "limit": limit,
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if "toptracks" not in data or "track" not in data["toptracks"]:
        print("No tracks found or invalid artist name.")
        return []

    tracks = data["toptracks"]["track"]
    track_names = [track["name"] for track in tracks]

    return track_names


if __name__ == "__main__":
    artist = "Camellia"
    top_tracks = get_top_tracks(artist, 10)
    tracks = []
    for track in top_tracks:
        result = search_song_on_ytmusic(artist, track)
        tracks.append(result)

    for track in tracks:
        download_song(track["videoId"])
    # result = search_song_on_ytmusic("Camellia", "crystallized")
    # print(result)
