#!/usr/bin/env python3
"""
MP3 Metadata Enricher

This module provides functionality to extract MP3 metadata and enrich it with
additional information from MusicBrainz, including cover art from the Cover Art Archive.

Requirements:
pip install mutagen musicbrainzngs requests Pillow

Usage:
    result = enrich_mp3_metadata('/path/to/file.mp3')
    print(result)
"""

import os
import sys
import requests
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3NoHeaderError
    import musicbrainzngs as mb
    from PIL import Image
    import io
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Please install with: pip install mutagen musicbrainzngs requests Pillow")
    sys.exit(1)


class MP3MetadataEnricher:
    """Class to handle MP3 metadata extraction and enrichment."""

    def __init__(self, user_agent: str = "MP3MetadataEnricher/1.0"):
        """
        Initialize the enricher with MusicBrainz configuration.

        Args:
            user_agent: User agent string for MusicBrainz API requests
        """
        # Configure MusicBrainz
        mb.set_useragent("MP3MetadataEnricher", "1.0")
        mb.set_rate_limit(limit_or_interval=1.0, new_requests=1)

    def extract_basic_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract basic metadata from MP3 file.

        Args:
            file_path: Path to the MP3 file

        Returns:
            Dictionary containing basic metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.lower().endswith(".mp3"):
            raise ValueError("File must be an MP3")

        try:
            audio_file = MP3(file_path)
        except Exception as e:
            raise ValueError(f"Invalid MP3 file: {e}")

        metadata = {
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "duration": getattr(audio_file.info, "length", 0),
            "bitrate": getattr(audio_file.info, "bitrate", 0),
            "sample_rate": getattr(audio_file.info, "sample_rate", 0),
            "channels": getattr(audio_file.info, "channels", 0),
        }

        # Extract ID3 tags
        if audio_file.tags:
            tag_mapping = {
                "title": ["TIT2", "TITLE"],
                "artist": ["TPE1", "ARTIST"],
                "album": ["TALB", "ALBUM"],
                "albumartist": ["TPE2", "ALBUMARTIST"],
                "date": ["TDRC", "DATE"],
                "genre": ["TCON", "GENRE"],
                "track": ["TRCK", "TRACKNUMBER"],
                "disc": ["TPOS", "DISCNUMBER"],
            }

            for key, tag_variants in tag_mapping.items():
                value = None
                for tag in tag_variants:
                    if tag in audio_file.tags:
                        value = str(audio_file.tags[tag][0])
                        break
                metadata[key] = value

            # Handle cover art
            for tag in audio_file.tags.values():
                if hasattr(tag, "type") and tag.type == 3:  # Cover art
                    metadata["has_embedded_cover"] = True
                    metadata["embedded_cover_data"] = tag.data
                    break
            else:
                metadata["has_embedded_cover"] = False

        return metadata

    def search_musicbrainz(self, artist: str, title: str) -> List[Dict[str, Any]]:
        """
        Search MusicBrainz for recording information.

        Args:
            artist: Artist name
            title: Track title

        Returns:
            List of matching recordings
        """
        if not artist or not title:
            return []

        try:
            # Search for recordings
            query = f'artist:"{artist}" AND recording:"{title}"'
            result = mb.search_recordings(query=query, limit=10)

            recordings = []
            for recording in result.get("recording-list", []):
                rec_info = {
                    "mbid": recording["id"],
                    "title": recording.get("title", ""),
                    "length": recording.get("length"),
                    "disambiguation": recording.get("disambiguation", ""),
                    "artists": [
                        artist["name"] for artist in recording.get("artist-credit", [])
                    ],
                    "releases": [],
                }

                # Get release information
                if "release-list" in recording:
                    for release in recording["release-list"]:
                        release_info = {
                            "mbid": release["id"],
                            "title": release.get("title", ""),
                            "date": release.get("date", ""),
                            "country": release.get("country", ""),
                            "status": release.get("status", ""),
                            "packaging": release.get("packaging", ""),
                            "barcode": release.get("barcode", ""),
                        }

                        # Get artist and label info
                        if "artist-credit" in release:
                            release_info["artists"] = [
                                artist["name"] for artist in release["artist-credit"]
                            ]

                        if "label-info-list" in release:
                            release_info["labels"] = [
                                {
                                    "name": label.get("label", {}).get("name", ""),
                                    "catalog_number": label.get("catalog-number", ""),
                                }
                                for label in release["label-info-list"]
                            ]

                        rec_info["releases"].append(release_info)

                recordings.append(rec_info)

            return recordings

        except Exception as e:
            print(f"MusicBrainz search error: {e}")
            return []

    def get_cover_art(self, release_mbid: str, size: str = "500") -> Optional[bytes]:
        """
        Fetch cover art from Cover Art Archive.

        Args:
            release_mbid: MusicBrainz release ID
            size: Image size ('250', '500', '1200', or None for original)

        Returns:
            Cover art image data as bytes, or None if not found
        """
        try:
            if size:
                url = f"https://coverartarchive.org/release/{release_mbid}/front-{size}"
            else:
                url = f"https://coverartarchive.org/release/{release_mbid}/front"

            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.content

        except Exception as e:
            print(f"Cover art fetch error: {e}")

        return None

    def save_cover_art(self, image_data: bytes, output_path: str) -> bool:
        """
        Save cover art image to file.

        Args:
            image_data: Image data as bytes
            output_path: Path to save the image

        Returns:
            True if successful, False otherwise
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            image.save(output_path)
            return True
        except Exception as e:
            print(f"Error saving cover art: {e}")
            return False

    def enrich_metadata(
        self, file_path: str, save_cover: bool = True, cover_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract and enrich MP3 metadata with MusicBrainz data and cover art.

        Args:
            file_path: Path to MP3 file
            save_cover: Whether to save cover art to file
            cover_dir: Directory to save cover art (defaults to same as MP3)

        Returns:
            Dictionary containing enriched metadata
        """
        # Extract basic metadata
        metadata = self.extract_basic_metadata(file_path)

        artist = metadata.get("artist")
        title = metadata.get("title")

        if not artist or not title:
            print("Warning: Missing artist or title - cannot enrich metadata")
            return metadata

        print(f"Searching MusicBrainz for: {artist} - {title}")

        # Search MusicBrainz
        recordings = self.search_musicbrainz(artist, title)

        if recordings:
            best_match = recordings[0]  # Take the first result
            metadata["musicbrainz"] = best_match

            # Try to get additional metadata from best release
            if best_match["releases"]:
                best_release = best_match["releases"][0]

                # Update metadata with MusicBrainz info
                if not metadata.get("album") and best_release.get("title"):
                    metadata["enriched_album"] = best_release["title"]

                if best_release.get("date"):
                    metadata["enriched_date"] = best_release["date"]

                if best_release.get("labels"):
                    metadata["enriched_labels"] = best_release["labels"]

                # Fetch cover art
                if save_cover:
                    cover_art = self.get_cover_art(best_release["mbid"])
                    if cover_art:
                        if not cover_dir:
                            cover_dir = os.path.dirname(file_path)

                        base_name = os.path.splitext(os.path.basename(file_path))[0]
                        cover_path = os.path.join(cover_dir, f"{base_name}_cover.jpg")

                        if self.save_cover_art(cover_art, cover_path):
                            metadata["cover_art_path"] = cover_path
                            metadata["cover_art_downloaded"] = True
                        else:
                            metadata["cover_art_downloaded"] = False
                    else:
                        metadata["cover_art_available"] = False
        else:
            print("No matches found in MusicBrainz")
            metadata["musicbrainz_found"] = False

        return metadata


def enrich_mp3_metadata(
    file_path: str, save_cover: bool = True, cover_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to enrich MP3 metadata.

    Args:
        file_path: Path to MP3 file
        save_cover: Whether to save cover art to file
        cover_dir: Directory to save cover art

    Returns:
        Dictionary containing enriched metadata
    """
    enricher = MP3MetadataEnricher()
    return enricher.enrich_metadata(file_path, save_cover, cover_dir)


def print_metadata(metadata: Dict[str, Any]):
    """Pretty print metadata information."""
    print("\n" + "=" * 60)
    print("MP3 METADATA REPORT")
    print("=" * 60)

    # Basic file info
    print(f"File: {metadata.get('file_path', 'Unknown')}")
    print(f"Size: {metadata.get('file_size', 0):,} bytes")
    print(f"Duration: {metadata.get('duration', 0):.2f} seconds")
    print(f"Bitrate: {metadata.get('bitrate', 0)} kbps")
    print(f"Sample Rate: {metadata.get('sample_rate', 0)} Hz")
    print(f"Channels: {metadata.get('channels', 0)}")

    # Basic tags
    print("\nBasic Tags:")
    for key in ["title", "artist", "album", "albumartist", "date", "genre", "track"]:
        value = metadata.get(key)
        if value:
            print(f"  {key.title()}: {value}")

    # Enriched data
    if "musicbrainz" in metadata:
        mb_data = metadata["musicbrainz"]
        print(f"\nMusicBrainz ID: {mb_data.get('mbid', 'Unknown')}")

        if mb_data.get("releases"):
            release = mb_data["releases"][0]
            print(f"Release: {release.get('title', 'Unknown')}")
            print(f"Release Date: {release.get('date', 'Unknown')}")
            print(f"Country: {release.get('country', 'Unknown')}")

            if release.get("labels"):
                print("Labels:")
                for label in release["labels"]:
                    print(
                        f"  {label.get('name', 'Unknown')} ({label.get('catalog_number', 'No catalog#')})"
                    )

    # Cover art
    if metadata.get("cover_art_downloaded"):
        print(f"\nCover art saved to: {metadata.get('cover_art_path')}")
    elif metadata.get("has_embedded_cover"):
        print("\nHas embedded cover art")

    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Enrich MP3 metadata using MusicBrainz"
    )
    parser.add_argument("file_path", help="Path to MP3 file")
    parser.add_argument(
        "--no-cover", action="store_true", help="Skip cover art download"
    )
    parser.add_argument("--cover-dir", help="Directory to save cover art")

    args = parser.parse_args()

    try:
        metadata = enrich_mp3_metadata(
            args.file_path, save_cover=not args.no_cover, cover_dir=args.cover_dir
        )

        print_metadata(metadata)

        # Optionally save metadata as JSON
        json_path = os.path.splitext(args.file_path)[0] + "_metadata.json"
        with open(json_path, "w", encoding="utf-8") as f:
            # Remove binary data before saving
            save_metadata = {
                k: v for k, v in metadata.items() if k != "embedded_cover_data"
            }
            json.dump(save_metadata, f, indent=2, ensure_ascii=False)

        print(f"\nMetadata saved to: {json_path}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
