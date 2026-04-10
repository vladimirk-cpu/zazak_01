from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.services.queue_service import add_lead_to_queue
from app.core.security import limiter
from app.core.logging import logger
from app.schemas.lead import LeadCreate, LeadSmallForm, LeadLargeForm
import json

router = APIRouter()

@router.post("/submit")
@limiter.limit("5/minute")
async def submit_lead(request: Request, db: AsyncSession = Depends(get_db)):
    # 1. Get and validate body size to prevent OOM
    content_length = request.headers.get("Content-Length")
    if content_length and int(content_length) > 1 * 1024 * 1024: # 1MB limit for JSON
        logger.warning(f"Rejected submission with excessive body size: {content_length}")
        raise HTTPException(status_code=413, detail="Request body too large. Max size is 1MB.")

    try:
        raw_body = await request.body()
        if len(raw_body) > 1 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Request body too large. Max size is 1MB.")
        body_data = json.loads(raw_body)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # 2. Try validating as LeadSmallForm first
    # (Small form has phone and no name)
    data = None
    try:
        if "phone" in body_data and "name" not in body_data:
            data = LeadSmallForm(**body_data)
    except Exception:
        pass

    # 3. Try validating as LeadLargeForm
    if not data:
        try:
            data = LeadLargeForm(**body_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid form data")

    # reCAPTCHA v3 mock validation (keeping if provided in raw data)
    recaptcha_token = body_data.get("recaptcha_token")
    if recaptcha_token is not None:
        # Mock logic
        pass
        
    logger.info(f"Received new {data.form_type} lead submission")
    
    # Transform to universal dictionary
    lead_data = {
        "form_type": data.form_type,
        "phone": data.phone,
        "name": getattr(data, "name", None),
        "email": getattr(data, "email", None),
        "file": getattr(data, "file", None),
        "comment": body_data.get("comment"), # Keep existing comment if present
    }
    
    try:
        db_lead = await add_lead_to_queue(db, lead_data)
        logger.info(f"Lead queued with id={db_lead.id}")
        return {"status": "success", "message": "Lead submitted successfully", "lead_id": db_lead.id}
    except Exception as e:
        logger.error(f"Error adding lead to queue: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
