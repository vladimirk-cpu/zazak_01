import aiosmtplib
from email.message import EmailMessage
from app.core.config import settings
from app.core.logging import logger

async def send_email_notification(lead_data: dict) -> bool:
    try:
        msg = EmailMessage()
        form_type = lead_data.get('form_type', 'Неизвестная форма')
        msg['Subject'] = f"[Лендинг] Новая заявка ({form_type})"
        msg['From'] = settings.MAIL_FROM
        msg['To'] = settings.MAIL_TO
        
        body_lines = []
        # Определяем заполнение в зависимости от полей (малая форма = только телефон)
        if lead_data.get('name') or lead_data.get('email') or lead_data.get('comment'):
            body_lines.append(f"Имя: {lead_data.get('name', 'Не указано')}")
            body_lines.append(f"Телефон: {lead_data.get('phone', 'Не указан')}")
            body_lines.append(f"Email: {lead_data.get('email', 'Не указан')}")
            if lead_data.get('comment'):
                body_lines.append(f"Комментарий: {lead_data['comment']}")
        else:
            body_lines.append(f"Телефон: {lead_data.get('phone', 'Не указан')}")
            
        if lead_data.get('file_uuid'):
            body_lines.append(f"Файл (UUID): {lead_data['file_uuid']}")
            
        msg.set_content("\n".join(body_lines))

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info(f"Email successfully sent to {settings.MAIL_TO} for form {form_type}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        return False
