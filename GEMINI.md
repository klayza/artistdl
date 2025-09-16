# GEMINI.md

## Project Overview

This project is a Python application for downloading music. It fetches an artist's top tracks from the Last.fm API, searches for them on YouTube Music, and then downloads the audio using `yt-dlp`. The main technologies used are Python, `ytmusicapi`, `yt-dlp`, and the Last.fm API.

The core logic is encapsulated in the `MusicDownloader` class in `src/artistdl.py`. This class orchestrates the process of fetching track information, searching for songs, and downloading the audio. The application is configured through a `.env` file, which should contain the Last.fm API key.

## Building and Running

To build and run this project, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/klayza/artistdl
    cd artistdl
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the environment:**
    *   Rename `.env.example` to `.env`.
    *   Add your Last.fm API key to the `.env` file:
        ```
        LAST_FM_KEY=your_last_fm_api_key
        ```
    *   (Optional) If you are using a browser cookie for YouTube Music, make sure the file is named `cookies.txt` and is in the root directory.

4.  **Run the application:**
    ```bash
    python src/app.py
    ```

## Development Conventions

*   **Configuration:** All configuration is managed through environment variables loaded from a `.env` file.
*   **Logging:** The project uses the `logging` module for logging. Logs are written to `music_downloader.log` and also to the console.
*   **Structure:** The main application logic is separated into classes in `src/artistdl.py`, with a clear separation of concerns for interacting with external APIs and for handling audio downloads. The entry point of the application is `src/app.py`.
*   **Error Handling:** The application uses a custom exception class, `MusicDownloaderError`, for handling errors related to the music download process.
