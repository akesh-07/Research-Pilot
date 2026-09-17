import os
import shutil
from fastapi import UploadFile, HTTPException
from typing import List
from app.core.config import settings
from app.core.logging import logger
from app.schemas.research import UploadedFileMeta

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

def save_upload_files(files: List[UploadFile]) -> List[UploadedFileMeta]:
    uploaded_files_meta = []
    
    if not os.path.exists(settings.UPLOAD_DIR):
        os.makedirs(settings.UPLOAD_DIR)
        
    for file in files:
        if file.filename:
            # Check extension
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                logger.warning(f"File {file.filename} has unsupported extension {ext}")
                # We can choose to skip or raise error. 
                # Let's skip it to allow other files.
                continue
                
            file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
            
            try:
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                size = os.path.getsize(file_path)
                # Check max size (MB to bytes)
                if size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                    os.remove(file_path)
                    logger.warning(f"File {file.filename} exceeds max size {settings.MAX_FILE_SIZE_MB}MB")
                    continue
                    
                meta = UploadedFileMeta(
                    filename=file.filename,
                    size=size,
                    path=file_path
                )
                uploaded_files_meta.append(meta)
            except Exception as e:
                logger.error(f"Error saving file {file.filename}: {e}")
                
    return uploaded_files_meta
