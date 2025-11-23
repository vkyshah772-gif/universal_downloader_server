from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import uuid

app = FastAPI()

# CORS for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/")
def home():
    return {"status": "server running"}

# Main download API
@app.post("/download")
def download_file(url: str):
    try:
        # Create temp folder
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        # Generate unique filename
        file_name = url.split("/")[-1].split("?")[0]
        if file_name == "":
            file_name = f"file_{uuid.uuid4()}"
        file_path = f"downloads/{file_name}"

        # Download file
        response = requests.get(url, stream=True, timeout=60)

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download file")

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 512):
                if chunk:
                    f.write(chunk)

        return FileResponse(
            file_path,
            media_type="application/octet-stream",
            filename=file_name,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
