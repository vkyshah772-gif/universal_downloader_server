from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from yt_dlp import YoutubeDL

app = FastAPI()

# Allow access from anywhere (important for your Flutter app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/extract")
def extract(url: str):
    """
    Extract downloadable formats (video/audio) from YouTube, TikTok, Facebook,
    Instagram, direct files, and 1000+ supported sites.
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

        quality = f.get("format_note") or ""
        if f.get("height"):
            quality = f"{f.get('height')}p {quality}".strip()

        formats.append(
            {
                "id": f.get("format_id"),
                "ext": f.get("ext") or "",
                "quality": quality or "Unknown",
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
