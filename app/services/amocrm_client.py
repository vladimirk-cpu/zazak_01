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

    if not settings.AMOCRM_SUBDOMAIN or not settings.AMOCRM_CLIENT_ID:
        logger.info(f"Mock AMOCRM send ({form_type}) requested")
        return True
    
    # Real implementation placeholder for AmoCRM API v4
    try:
        # 1. Сформировать тело запроса к /api/v4/leads
        # 2. Указать pipeline_id и status_id из настроек
        # 3. Добавить кастомное поле для типа формы (AMOCRM_FORM_TYPE_FIELD_ID)
        # 4. Если есть файл - логика загрузки (заглушка)
        # 5. Привязать контакты (имя, телефон, email)
        
        payload = {
            "name": f"Заявка с сайта ({form_type})",
            "pipeline_id": settings.AMOCRM_PIPELINE_ID,
            "status_id": settings.AMOCRM_STATUS_ID,
            "custom_fields_values": [
                {
                    "field_id": settings.AMOCRM_FORM_TYPE_FIELD_ID,
                    "values": [{"value": form_type}]
                }
            ]
        }
        
        if file:
            # TODO: Implement file upload logic to AmoCRM
            logger.info(f"File upload requested for lead: {file}")
            pass

        logger.info(f"Mock AMOCRM v4 call with payload: {payload}")
        return True
    except Exception as e:
        logger.error(f"Error in send_to_amocrm: {e}")
        return False
