import httpx
from app.core.config import settings
from app.core.logging import logger

async def send_to_amocrm(name: str, phone: str, comment: str) -> bool:
    if not settings.AMOCRM_SUBDOMAIN or not settings.AMOCRM_CLIENT_ID:
        logger.info(f"Mock AMOCRM send: name='{name}' phone='{phone}' comment='{comment}'")
        return True
    
    # Real implementation would require OAuth2 token generation and refresh logic
    # Here is a mock implementation pretending to send using an endpoint
    logger.info(f"Mock AMOCRM send via API: name='{name}' phone='{phone}'")
    return True
