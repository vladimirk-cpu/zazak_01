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
    # 1. Fetch leads that need processing
    async with async_session() as db:
        stmt = select(PendingLead).where(
            PendingLead.next_retry_at <= datetime.utcnow(),
            (PendingLead.max_sent == False) | (PendingLead.amocrm_sent == False),
            PendingLead.attempts < MAX_ATTEMPTS
        )
        result = await db.execute(stmt)
        leads = result.scalars().all()

    # 2. Iterate and process outside the initial reading session
    for lead in leads:
        try:
            logger.info(f"Processing lead id={lead.id}, attempt={lead.attempts + 1}")
            
            # Decrypt outside the database lock
            name = decrypt(lead.name_encrypted)
            phone = decrypt(lead.phone_encrypted)
            email = decrypt(lead.email_encrypted) if lead.email_encrypted else None
            file = decrypt(lead.file_encrypted) if lead.file_encrypted else None
            comment = decrypt(lead.comment_encrypted) if lead.comment_encrypted else ""
            form_type = lead.form_type

            # New state to save
            max_sent = lead.max_sent
            amocrm_sent = lead.amocrm_sent
            attempts = lead.attempts + 1

            if not max_sent:
                text = f"Новая заявка! ({form_type})\nИмя: {name}\nТелефон: {phone}"
                if email: text += f"\nEmail: {email}"
                if file: text += f"\nФайл: {file}"
                if comment: text += f"\nКомментарий: {comment}"
                
                success = await send_to_max(text)
                if success:
                    max_sent = True

            if not amocrm_sent:
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
                    amocrm_sent = True
                
                # Best-effort email notification
                try:
                    await send_email_notification(lead_data)
                except Exception as e:
                    logger.error(f"Failed to send email notification for lead {lead.id}: {e}")

            # 3. Update database in a new brief transaction
            async with async_session() as db:
                # Refresh our local 'lead' object or fetch a fresh one to update
                stmt = select(PendingLead).where(PendingLead.id == lead.id)
                res = await db.execute(stmt)
                db_lead = res.scalar_one()
                
                db_lead.attempts = attempts
                db_lead.max_sent = max_sent
                db_lead.amocrm_sent = amocrm_sent
                
                if max_sent and amocrm_sent:
                    logger.info(f"Lead id={lead.id} successfully processed")
                else:
                    # Exponential backoff: 1 min, 2 min, 4 min, 8 min...
                    delay_minutes = 2 ** (db_lead.attempts - 1)
                    db_lead.next_retry_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
                    logger.warning(f"Lead id={lead.id} processing failed. Next retry at {db_lead.next_retry_at}")
                
                await db.commit()

        except Exception as e:
            logger.error(f"Critical error processing lead id={lead.id}: {e}")
            continue

async def worker_loop():
    logger.info("Starting background worker for pending leads...")
    while True:
        try:
            await process_pending_leads()
        except Exception as e:
            logger.error(f"Error in worker loop: {e}")
        await asyncio.sleep(10)
