## Description

Literally just type in the name of an artist and it downloads their top music. ez pz. It checks lastfm for the top 50 tracks and then downloads from YT music.

## Install

You will need:

- Last FM api key (get that here: https://www.last.fm/api/accounts)
- cookies.txt (optional, but reccomended)

1. `git clone https://github.com/klayza/artistdl`
2. `cd artistdl`
3. `pip install -r requirements.txt`
4. rename `.env.example` to `.env`
5. get lastfm api key and set `LAST_FM_KEY` in `.env` file
6. (optional) if you are using a browser cookie then make sure the file is named `cookies.txt` and is in this directory
7. Run `python3 main.py`
