from app.core.config import settings
from app.core.logging import logger

async def send_email_notification(lead_data: dict) -> bool:
    """
    Отправляет уведомление о заявке на email.
    Пока заглушка: логирует данные и возвращает True.
    В будущем заменим на реальную отправку через SMTP.
    """
    logger.info(f"Email notification (stub): would send email to {settings.MAIL_TO}")
    logger.info(f"Subject: [Лендинг] Новая заявка ({lead_data.get('form_type', 'unknown')})")
    
    # Optional: prettify lead data for log output
    details = ", ".join([f"{k}={v}" for k, v in lead_data.items() if v])
    logger.info(f"Body details: {details}")
    
    return True
