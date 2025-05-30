# uploader.py
from fastapi import FastAPI, UploadFile
from pathlib import Path
from prefect.events import emit_event

app = FastAPI()
UPLOAD_DIR = Path("/data/uploads")

@app.post("/upload/")
async def upload_image(file: UploadFile):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        f.write(await file.read())
    emit_event(
        event="image.uploaded",
        resource={"prefect.resource.id": "image-uploader"},
        details={"image_path": str(dest)},
    )
    return {"status": "ok", "path": str(dest)}
