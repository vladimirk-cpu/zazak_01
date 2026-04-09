import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from app.core.dependencies import async_session
from app.models.lead import PendingLead
from app.services.encryption import decrypt
from app.services.max_client import send_to_max
from app.services.amocrm_client import send_to_amocrm
from app.services.email_client import send_email_notification
from app.core.logging import logger

MAX_ATTEMPTS = 5

async def process_pending_leads():
    async with async_session() as db:
        stmt = select(PendingLead).where(
            PendingLead.next_retry_at <= datetime.utcnow(),
            (PendingLead.max_sent == False) | (PendingLead.amocrm_sent == False),
            PendingLead.attempts < MAX_ATTEMPTS
        )
        result = await db.execute(stmt)
        leads = result.scalars().all()

        for lead in leads:
            logger.info(f"Processing lead id={lead.id}, attempt={lead.attempts + 1}")
            
            name = decrypt(lead.name_encrypted)
            phone = decrypt(lead.phone_encrypted)
            email = decrypt(lead.email_encrypted) if lead.email_encrypted else None
            file = decrypt(lead.file_encrypted) if lead.file_encrypted else None
            comment = decrypt(lead.comment_encrypted) if lead.comment_encrypted else ""
            form_type = lead.form_type

            lead.attempts += 1

            if not lead.max_sent:
                text = f"Новая заявка! ({form_type})\nИмя: {name}\nТелефон: {phone}"
                if email: text += f"\nEmail: {email}"
                if file: text += f"\nФайл: {file}"
                if comment: text += f"\nКомментарий: {comment}"
                
                success = await send_to_max(text)
                if success:
                    lead.max_sent = True

            if not lead.amocrm_sent:
                lead_data = {
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "file": file,
                    "comment": comment,
                    "form_type": form_type
                }
                success = await send_to_amocrm(lead_data)
                if success:
                    lead.amocrm_sent = True
                
                # Best-effort email notification
                try:
                    await send_email_notification(lead_data)
                except Exception as e:
                    logger.error(f"Failed to send email notification for lead {lead.id}: {e}")

            if lead.max_sent and lead.amocrm_sent:
                logger.info(f"Lead id={lead.id} successfully processed")
            else:
                # Exponential backoff: 1 min, 2 min, 4 min, 8 min...
                delay_minutes = 2 ** (lead.attempts - 1)
                lead.next_retry_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
                logger.warning(f"Lead id={lead.id} processing failed. Next retry at {lead.next_retry_at}")

            await db.commit()

async def worker_loop():
    logger.info("Starting background worker for pending leads...")
    while True:
        try:
            await process_pending_leads()
        except Exception as e:
            logger.error(f"Error in worker loop: {e}")
        await asyncio.sleep(10)
