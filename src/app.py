import logging
import os
from pathlib import Path
from ytmusicapi import YTMusic
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

from util import setup_logging
from artistdl import MusicDownloader

# Load environment variables
load_dotenv()

# Setup logging
setup_logging("DEBUG")
logger = logging.getLogger(__name__)

# Get API key
api_key = os.getenv("LAST_FM_KEY")
if not api_key:
    logger.error("LAST_FM_KEY not found in environment variables")
    exit()

# Initialize downloader
downloader = MusicDownloader(api_key)

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        artist = request.form.get("artist")
        limit = int(request.form.get("limit", 10))
        if artist:
            downloader.add_artist_to_queue(artist, limit)
    return render_template("index.html")

@app.route("/queue")
def queue():
    return jsonify(downloader.get_queue())

def main():
    """Main function"""
    app.run(debug=True)


if __name__ == "__main__":
    main()
