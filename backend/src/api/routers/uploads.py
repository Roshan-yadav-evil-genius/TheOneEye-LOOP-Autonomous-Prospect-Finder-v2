from fastapi import APIRouter, UploadFile, File
import shutil
import os
import uuid
from pathlib import Path

router = APIRouter(prefix="/api/v1/upload", tags=["Uploads"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/thumbnail")
async def upload_thumbnail(file: UploadFile = File(...)):
    # Generate a unique filename to prevent collisions
    extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"url": f"/static/uploads/{unique_filename}"}
