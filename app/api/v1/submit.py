from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.lead import LeadCreate
from app.core.dependencies import get_db
from app.services.queue_service import add_lead_to_queue
from app.core.security import limiter
from app.core.logging import logger

router = APIRouter()

@router.post("/submit")
@limiter.limit("5/minute")
async def submit_lead(request: Request, lead: LeadCreate, db: AsyncSession = Depends(get_db)):
    # reCAPTCHA v3 mock validation
    if lead.recaptcha_token is not None:
        # Mock logic
        pass
        
    logger.info("Received new lead submission")
    
    try:
        db_lead = await add_lead_to_queue(db, lead.name, lead.phone, lead.comment)
        logger.info(f"Lead queued with id={db_lead.id}")
        return {"status": "success", "message": "Lead submitted successfully", "lead_id": db_lead.id}
    except Exception as e:
        logger.error(f"Error adding lead to queue: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
