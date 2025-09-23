## Description

Literally just type in the name of an artist and it downloads their top music. ez pz. It checks lastfm for the top 50 tracks and then downloads from YT music. Or you can do top 1000 songs.

## Setup

You will need:

- Last FM api key (get that here: https://www.last.fm/api/accounts)
- cookies.txt (optional, but reccomended. use this guide: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)


Install:

1. `git clone https://github.com/klayza/artistdl`
2. `cd artistdl`
3. `pip install -r requirements.txt`
4. rename `.env.example` to `.env`
5. get lastfm api key and set `LAST_FM_KEY` in `.env` file
6. (optional) if you are using a browser cookie then make sure the file is named `cookies.txt` and is in this directory
7. Run `python3 main.py`

## Note

This method is not very fast, I downloaded 100 songs and on average it takes 30 minutes or 18 seconds for each track

## Todo

- apply mp3 tags upon download

  - known tags
  - beets lookup

- database

  - store ytm id for every song (so we avoid downloading duplicates)

- frontend
  - download progress
  - view downloads (speed dial view)
  - view artists
  - theme: monospace font, simple, text based (no fancy lines, borders just ascii)
  - set api key and upload cookies.txt
