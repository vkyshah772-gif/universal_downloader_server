from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from yt_dlp import YoutubeDL
import requests
import os
import uuid

app = FastAPI()

# Allow access from your Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple health endpoint
@app.get("/")
def home():
    return {"status": "server running"}


# -------- UNIVERSAL FORMAT EXTRACTOR (YouTube, TikTok, FB, etc.) ----------
@app.get("/extract")
def extract(url: str = Query(..., description="Video or audio page URL")):
    """
    Return downloadable formats (video/audio) from YouTube, TikTok, Facebook,
    Instagram, etc. Flutter will pick one format and download with Dio.
    """
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "nocheckcertificate": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    formats = []
    for f in info.get("formats", []):
        if not f.get("url"):
            continue

        # Build human-readable quality label
        quality = f.get("format_note") or ""
        height = f.get("height")
        if height:
            quality = f"{height}p {quality}".strip()

        # Sometimes only audio (vcodec = 'none')
        if f.get("vcodec") == "none":
            if f.get("acodec") != "none":
                quality = f"AUDIO {f.get('acodec', '')}".strip()

        label = quality or f.get("ext") or "unknown"

        formats.append(
            {
                "id": f.get("format_id"),
                "ext": f.get("ext"),
                "label": label,
                "acodec": f.get("acodec"),
                "vcodec": f.get("vcodec"),
                "filesize": f.get("filesize") or f.get("filesize_approx"),
                "url": f.get("url"),
            }
        )

    return {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "formats": formats,
    }


# -------- OPTIONAL: direct file downloader (for plain links) ----------
@app.post("/download")
def download_file(url: str):
    """
    Simple direct-file downloader (PDF, MP4, ZIP etc.). Not used by Flutter
    right now, but kept for future use.
    """
    try:
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        fname = url.split("/")[-1].split("?")[0]
        if not fname:
            fname = f"file_{uuid.uuid4()}"
        path = os.path.join("downloads", fname)

        r = requests.get(url, stream=True, timeout=60)
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download file")

        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 512):
                if chunk:
                    f.write(chunk)

        return FileResponse(path, media_type="application/octet-stream", filename=fname)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
