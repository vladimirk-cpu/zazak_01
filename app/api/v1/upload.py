from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid
import aiofiles
from app.core.logging import logger

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
]
UPLOAD_DIR = "./data/uploads"

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1. Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Rejected file with invalid MIME type: {file.content_type}")
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: PDF, DOC, DOCX, XLS, XLSX. Received: {file.content_type}"
        )

    # 2. Validate File Size
    # FastAPI >= 0.94.0 has file.size property.
    file_size = getattr(file, "size", None)
    
    if file_size is None:
        # Fallback for older versions: check size by reading
        await file.seek(0)
        chunk = await file.read(MAX_FILE_SIZE + 1)
        file_size = len(chunk)
        await file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        logger.warning(f"Rejected file with excessive size: {file_size} bytes")
        raise HTTPException(status_code=400, detail="File too large. Max size is 10MB.")

    # 3. Generate unique name
    # Sanitize filename to prevent path traversal
    safe_filename = os.path.basename(file.filename)
    file_uuid = uuid.uuid4().hex
    unique_filename = f"{file_uuid}_{safe_filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # 4. Save file asynchronously
    try:
        await file.seek(0)
        contents = await file.read()
        actual_size = len(contents)
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            await out_file.write(contents)
        
        logger.info(f"File uploaded successfully: {unique_filename} (Read: {actual_size} bytes)")
        return {
            "file_uuid": file_uuid,
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        # Cleanup if partially written
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Internal server error while saving file")
