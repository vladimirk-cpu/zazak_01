from sqlalchemy.ext.asyncio import AsyncSession
from app.models.lead import PendingLead
from app.services.encryption import encrypt
from datetime import datetime

async def add_lead_to_queue(db: AsyncSession, lead_data: dict) -> PendingLead:
    lead = PendingLead(
        name_encrypted=encrypt(lead_data.get("name", "")),
        phone_encrypted=encrypt(lead_data.get("phone", "")),
        email_encrypted=encrypt(lead_data.get("email")) if lead_data.get("email") else None,
        file_encrypted=encrypt(lead_data.get("file")) if lead_data.get("file") else None,
        comment_encrypted=encrypt(lead_data.get("comment")) if lead_data.get("comment") else None,
        form_type=lead_data.get("form_type", "large"),
        created_at=datetime.utcnow(),
        next_retry_at=datetime.utcnow()
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead
