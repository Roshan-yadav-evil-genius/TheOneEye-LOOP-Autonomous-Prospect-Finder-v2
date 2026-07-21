from fastapi import APIRouter, UploadFile, File
import shutil
import os
import uuid
from pathlib import Path

from core.config import get_settings

router = APIRouter(prefix="/api/v1/upload", tags=["Uploads"])

@router.post("/thumbnail")
async def upload_thumbnail(file: UploadFile = File(...)):
    settings = get_settings()
    upload_dir = Path("instance") / settings.env / "upload"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate a unique filename to prevent collisions
    extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    file_path = upload_dir / unique_filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"url": f"/static/uploads/{unique_filename}"}

@router.post("/icon")
async def upload_icon(file: UploadFile = File(...)):
    settings = get_settings()
    upload_dir = Path("instance") / settings.env / "upload"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate a unique filename to prevent collisions
    extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    file_path = upload_dir / unique_filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"url": f"/static/uploads/{unique_filename}"}
