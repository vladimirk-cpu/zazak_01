from sqlalchemy.ext.asyncio import AsyncSession
from app.models.lead import PendingLead
from app.services.encryption import encrypt
from datetime import datetime

async def add_lead_to_queue(db: AsyncSession, name: str, phone: str, comment: str = None) -> PendingLead:
    lead = PendingLead(
        name_encrypted=encrypt(name),
        phone_encrypted=encrypt(phone),
        comment_encrypted=encrypt(comment) if comment else None,
        created_at=datetime.utcnow(),
        next_retry_at=datetime.utcnow()
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead
