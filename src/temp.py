import os
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, TIT2, TPE1


def apply_mp3_tags():
    """
    Apply MP3 tags to songs based on their directory structure:
    downloads/{artist}/{trackname}
    """
    downloads_dir = "downloads"

    # Check if downloads directory exists
    if not os.path.exists(downloads_dir):
        print("Downloads directory not found")
        return

    # Loop through artist directories
    for artist in os.listdir(downloads_dir):
        artist_path = os.path.join(downloads_dir, artist)

        if os.path.isdir(artist_path):
            # Loop through tracks in artist directory
            for track in os.listdir(artist_path):
                if track.endswith(".mp3"):
                    track_path = os.path.join(artist_path, track)

                    try:
                        # Get track name without extension
                        track_name = os.path.splitext(track)[0]

                        # Try to load existing ID3 tags or create new ones
                        try:
                            audio = EasyID3(track_path)
                        except:
                            audio = ID3()

                        # Set artist and title tags
                        audio["artist"] = artist
                        audio["title"] = track_name

                        # Save the tags
                        audio.save(track_path)
                        print(f"Tagged: {artist} - {track_name}")

                    except Exception as e:
                        print(f"Error tagging {track_path}: {str(e)}")


if __name__ == "__main__":
    apply_mp3_tags()
