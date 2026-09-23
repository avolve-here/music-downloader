from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import os
import subprocess
import uuid
import requests
import shutil


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Music Downloader API",
    version="3.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DOWNLOADS_DIR = os.path.join(
    BASE_DIR,
    "downloads"
)

os.makedirs(
    DOWNLOADS_DIR,
    exist_ok=True
)


# =========================================================
# MODELS
# =========================================================

class MusicAnalyzeRequest(BaseModel):
    url: str


class MusicDownloadRequest(BaseModel):
    url: str
    format: str = "mp3"
    bitrate: str = "320k"


# =========================================================
# VALIDATION
# =========================================================

def validate_spotify_url(url: str):

    url = url.strip()

    if not url:
        raise HTTPException(
            status_code=400,
            detail="Spotify URL is required."
        )

    if "spotify.com" not in url.lower():
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid Spotify URL."
        )

    return url


def safe_format(value: str):

    allowed_formats = {
        "mp3",
        "m4a",
        "opus",
        "ogg",
        "flac",
        "wav"
    }

    value = value.lower().strip()

    if value not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format."
        )

    return value


def safe_bitrate(value: str):

    allowed_bitrates = {
        "128k",
        "192k",
        "320k"
    }

    value = value.lower().strip()

    if value not in allowed_bitrates:
        raise HTTPException(
            status_code=400,
            detail="Unsupported bitrate."
        )

    return value


# =========================================================
# FIND FFMPEG
# =========================================================

def find_ffmpeg():

    ffmpeg = shutil.which("ffmpeg")

    if ffmpeg:
        return ffmpeg

    possible_paths = [

        os.path.join(
            BASE_DIR,
            "ffmpeg",
            "bin",
            "ffmpeg.exe"
        ),

        os.path.join(
            BASE_DIR,
            "ffmpeg-9.0.1-essentials_build",
            "bin",
            "ffmpeg.exe"
        ),

        os.path.join(
            os.path.dirname(BASE_DIR),
            "ffmpeg-9.0.1-essentials_build",
            "bin",
            "ffmpeg.exe"
        ),

        os.path.join(
            os.path.dirname(
                os.path.dirname(BASE_DIR)
            ),
            "ffmpeg-9.0.1-essentials_build",
            "bin",
            "ffmpeg.exe"
        )
    ]

    for path in possible_paths:

        if os.path.isfile(path):
            return path

    return None


# =========================================================
# CREATE DOWNLOAD DIRECTORY
# =========================================================

def create_download_directory():

    job_id = uuid.uuid4().hex

    directory = os.path.join(
        DOWNLOADS_DIR,
        job_id
    )

    os.makedirs(
        directory,
        exist_ok=True
    )

    return job_id, directory


# =========================================================
# FIND AUDIO FILE
# =========================================================

def find_audio_file(directory: str):

    if not os.path.isdir(directory):
        return None

    for root, directories, filenames in os.walk(directory):

        for filename in filenames:

            file_path = os.path.join(
                root,
                filename
            )

            if os.path.isfile(file_path):
                return file_path

    return None


# =========================================================
# OUTPUT EXTENSION
# =========================================================

def get_extension(audio_format: str):

    mapping = {
        "mp3": "mp3",
        "m4a": "m4a",
        "opus": "opus",
        "ogg": "ogg",
        "flac": "flac",
        "wav": "wav"
    }

    return mapping[audio_format]


# =========================================================
# DOWNLOAD + CONVERT
# =========================================================

def process_download(
    search_query: str,
    output_dir: str,
    audio_format: str,
    bitrate: str
):

    # -----------------------------------------------------
    # FIND FFMPEG
    # -----------------------------------------------------

    ffmpeg = find_ffmpeg()

    if not ffmpeg:

        raise RuntimeError(
            "FFmpeg was not found."
        )

    print()
    print("========================================")
    print("Starting download")
    print("Search:", search_query)
    print("Format:", audio_format)
    print("Bitrate:", bitrate)
    print("FFmpeg:", ffmpeg)
    print("========================================")
    print()


    # -----------------------------------------------------
    # DOWNLOAD NATIVE AUDIO WITH YT-DLP
    # -----------------------------------------------------

    source_template = os.path.join(
        output_dir,
        "source.%(ext)s"
    )

    command = [
    "yt-dlp",
    f"ytsearch1:{search_query}",
    "--no-playlist",
    "-f",
    "bestaudio/best",
    "--concurrent-fragments",
    "16",
    "--no-part",
    "--no-overwrites",
    "--output",
    source_template
]

    print("Downloading audio source...")
    print(
        "Command:",
        " ".join(command)
    )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=600
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print("yt-dlp output:")
        print(result.stderr)

    if result.returncode != 0:

        raise RuntimeError(
            "Unable to download the audio source."
        )


    # -----------------------------------------------------
    # FIND SOURCE FILE
    # -----------------------------------------------------

    source_file = find_audio_file(
        output_dir
    )

    if not source_file:

        raise RuntimeError(
            "Audio source was downloaded but no file was found."
        )

    print(
        "Source audio:",
        source_file
    )


    # -----------------------------------------------------
    # FINAL FILE
    # -----------------------------------------------------

    final_filename = (
        "download."
        + get_extension(audio_format)
    )

    final_path = os.path.join(
        output_dir,
        final_filename
    )


    # -----------------------------------------------------
    # FFMPEG COMMAND
    # -----------------------------------------------------

    ffmpeg_command = [
        ffmpeg,
        "-y",
        "-i",
        source_file,
        "-vn"
    ]


    # -----------------------------------------------------
    # FORMAT SETTINGS
    # -----------------------------------------------------

    if audio_format == "mp3":

        ffmpeg_command += [
            "-codec:a",
            "libmp3lame",
            "-b:a",
            bitrate
        ]

    elif audio_format == "m4a":

        ffmpeg_command += [
            "-codec:a",
            "aac",
            "-b:a",
            bitrate
        ]

    elif audio_format == "opus":

        ffmpeg_command += [
            "-codec:a",
            "libopus",
            "-b:a",
            bitrate
        ]

    elif audio_format == "ogg":

        ffmpeg_command += [
            "-codec:a",
            "libvorbis",
            "-b:a",
            bitrate
        ]

    elif audio_format == "flac":

        ffmpeg_command += [
            "-codec:a",
            "flac"
        ]

    elif audio_format == "wav":

        ffmpeg_command += [
            "-codec:a",
            "pcm_s16le"
        ]


    ffmpeg_command += [
        final_path
    ]


    # -----------------------------------------------------
    # CONVERT
    # -----------------------------------------------------

    print()
    print("Converting with FFmpeg...")
    print(
        "Command:",
        " ".join(ffmpeg_command)
    )

    conversion = subprocess.run(
        ffmpeg_command,
        capture_output=True,
        text=True,
        timeout=600
    )

    if conversion.stdout:
        print(conversion.stdout)

    if conversion.stderr:
        print("FFmpeg output:")
        print(conversion.stderr)

    if conversion.returncode != 0:

        raise RuntimeError(
            "Audio conversion failed."
        )


    # -----------------------------------------------------
    # VERIFY FILE
    # -----------------------------------------------------

    if not os.path.isfile(final_path):

        raise RuntimeError(
            "Audio conversion completed but the final file was not found."
        )


    print()
    print("========================================")
    print("Download ready")
    print("File:", final_path)
    print("========================================")
    print()


    return final_path


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "status": "online",
        "service": "Music Downloader API",
        "version": "3.0.0"
    }


# =========================================================
# ANALYZE
# =========================================================

@app.post("/api/music/analyze")
def analyze_music(
    request: MusicAnalyzeRequest
):

    url = validate_spotify_url(
        request.url
    )


    # -----------------------------------------------------
    # SPOTIFY METADATA
    # -----------------------------------------------------

    try:

        response = requests.get(
            "https://open.spotify.com/oembed",
            params={
                "url": url
            },
            timeout=15
        )

        response.raise_for_status()

        metadata = response.json()

    except requests.RequestException:

        raise HTTPException(
            status_code=400,
            detail="Unable to reach Spotify."
        )


    title = metadata.get(
        "title"
    )

    artist = metadata.get(
        "author_name"
    )

    thumbnail = metadata.get(
        "thumbnail_url"
    )


    if not title:

        raise HTTPException(
            status_code=400,
            detail="Unable to identify the Spotify track."
        )


    print()
    print("========================================")
    print("Spotify analyzed")
    print("Title:", title)
    print("Artist:", artist)
    print("URL:", url)
    print("========================================")
    print()


    # -----------------------------------------------------
    # RETURN METADATA ONLY
    # -----------------------------------------------------

    return {

        "status": "success",

        "title": title,

        "artist": artist,

        "thumbnail": thumbnail,

        "spotify_url": url
    }


# =========================================================
# DOWNLOAD
# =========================================================

@app.post("/api/music/download")
def download_music(
    request: MusicDownloadRequest
):

    url = validate_spotify_url(
        request.url
    )

    audio_format = safe_format(
        request.format
    )

    bitrate = safe_bitrate(
        request.bitrate
    )


    # -----------------------------------------------------
    # GET SPOTIFY METADATA AGAIN
    # -----------------------------------------------------
    # This happens only after the user clicks Download.

    try:

        response = requests.get(
            "https://open.spotify.com/oembed",
            params={
                "url": url
            },
            timeout=15
        )

        response.raise_for_status()

        metadata = response.json()

    except requests.RequestException:

        raise HTTPException(
            status_code=400,
            detail="Unable to reach Spotify."
        )


    title = metadata.get(
        "title"
    )

    artist = metadata.get(
        "author_name"
    )


    if not title:

        raise HTTPException(
            status_code=400,
            detail="Unable to identify the Spotify track."
        )


    # -----------------------------------------------------
    # BUILD SEARCH QUERY
    # -----------------------------------------------------

    search_query = title

    if artist:

        search_query = (
            f"{artist} - {title}"
        )


    # -----------------------------------------------------
    # CREATE JOB DIRECTORY
    # -----------------------------------------------------

    job_id, output_dir = (
        create_download_directory()
    )


    print()
    print("========================================")
    print("Download requested")
    print("Job:", job_id)
    print("Search:", search_query)
    print("Format:", audio_format)
    print("Bitrate:", bitrate)
    print("========================================")
    print()


    # -----------------------------------------------------
    # DOWNLOAD + CONVERT
    # -----------------------------------------------------

    try:

        file_path = process_download(
            search_query,
            output_dir,
            audio_format,
            bitrate
        )

    except subprocess.TimeoutExpired:

        shutil.rmtree(
            output_dir,
            ignore_errors=True
        )

        raise HTTPException(
            status_code=504,
            detail="Download timed out."
        )

    except FileNotFoundError:

        shutil.rmtree(
            output_dir,
            ignore_errors=True
        )

        raise HTTPException(
            status_code=500,
            detail="yt-dlp was not found."
        )

    except RuntimeError as error:

        shutil.rmtree(
            output_dir,
            ignore_errors=True
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    except Exception as error:

        print()
        print("Download error:")
        print(repr(error))
        print()

        shutil.rmtree(
            output_dir,
            ignore_errors=True
        )

        raise HTTPException(
            status_code=500,
            detail="Something went wrong while downloading the audio."
        )


    # -----------------------------------------------------
    # RETURN FILE DIRECTLY
    # -----------------------------------------------------

    return FileResponse(

        path=file_path,

        filename=os.path.basename(
            file_path
        ),

        media_type="application/octet-stream"
    )