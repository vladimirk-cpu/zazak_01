import httpx
from app.core.config import settings
from app.core.logging import logger

async def send_to_amocrm(lead_data: dict) -> bool:
    name = lead_data.get("name")
    phone = lead_data.get("phone")
    email = lead_data.get("email")
    file = lead_data.get("file")
    comment = lead_data.get("comment")
    form_type = lead_data.get("form_type", "large")

    try:
        url = f"https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads"
        headers = {
            "Authorization": f"Bearer {settings.AMOCRM_LONG_TERM_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": f"Заявка с сайта ({lead_data.get('form_type', 'unknown')})",
            "pipeline_id": settings.AMOCRM_PIPELINE_ID,
            "status_id": settings.AMOCRM_STATUS_ID,
        }
        
        if settings.AMOCRM_FORM_TYPE_FIELD_ID:
            payload["custom_fields_values"] = [
                {
                    "field_id": settings.AMOCRM_FORM_TYPE_FIELD_ID,
                    "values": [{"value": lead_data.get('form_type', 'unknown')}]
                }
            ]
            
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=[payload])
            
        if response.status_code in (200, 201):
            logger.info("Lead successfully sent to AMOCRM")
            return True
        else:
            logger.error(f"Error sending to AMOCRM: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error in send_to_amocrm: {e}")
        return False
