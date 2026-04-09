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
    try:
        if file.size > MAX_FILE_SIZE:
            logger.warning(f"Rejected file with excessive size: {file.size} bytes")
            raise HTTPException(status_code=400, detail="File too large. Max size is 10MB.")
    except AttributeError:
        # Fallback for older FastAPI versions
        try:
            await file.seek(0)
            # Read 1 byte more than max size to check
            chunk = await file.read(MAX_FILE_SIZE + 1)
            if len(chunk) > MAX_FILE_SIZE:
                logger.warning("Rejected file with excessive size (streaming check)")
                raise HTTPException(status_code=400, detail="File too large. Max size is 10MB.")
            await file.seek(0)
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            logger.error(f"Error checking file size (streaming): {e}")
            raise HTTPException(status_code=500, detail="Error validating file")
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        logger.error(f"Error checking file size: {e}")
        raise HTTPException(status_code=500, detail="Error validating file")

    # 3. Generate unique name
    file_uuid = uuid.uuid4().hex
    extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{file_uuid}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # 4. Save file asynchronously
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            # Read and write in chunks to handle memory efficiently
            while content := await file.read(1024 * 1024):  # 1MB chunks
                await out_file.write(content)
        
        logger.info(f"File uploaded successfully: {unique_filename}")
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
