import httpx
from app.core.config import settings
from app.core.logging import logger

async def send_to_max(text: str) -> bool:
    if not settings.MAX_BOT_TOKEN or not settings.MAX_CHAT_ID:
        logger.info("Mock MAX Messenger send requested")
        return True
    
    url = f"{settings.MAX_API_URL}/messages"
    headers = {
        "Authorization": settings.MAX_BOT_TOKEN
    }
    params = {
        "chat_id": settings.MAX_CHAT_ID,
        "text": text
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=params, timeout=10.0)
            response.raise_for_status()
            logger.info("Successfully sent message to MAX Messenger")
            return True
    except Exception as e:
        logger.error(f"Failed to send to MAX Messenger: {e}")
        return False
