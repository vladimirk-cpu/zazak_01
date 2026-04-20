import httpx
import os
from pathlib import Path
from app.core.config import settings
from app.core.logging import logger

async def send_to_amocrm(lead_data: dict) -> tuple[bool, int | None]:
    """
    Создает сделку в AmoCRM и прикрепляет файл, если он есть.
    Возвращает (success, lead_id).
    """
    phone = lead_data.get("phone")
    name = lead_data.get("name") or ""
    email = lead_data.get("email") or ""
    file_uuid = lead_data.get("file")
    form_type = lead_data.get("form_type", "unknown")
    comment = lead_data.get("comment") or ""

    headers = {
        "Authorization": f"Bearer {settings.AMOCRM_LONG_TERM_TOKEN}",
        "Content-Type": "application/json"
    }
    base_url = f"https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Создание сделки
        try:
            custom_fields = [
                {"field_id": settings.AMOCRM_FORM_TYPE_FIELD_ID, "values": [{"value": form_type}]},
                {"field_id": settings.AMOCRM_PHONE_FIELD_ID, "values": [{"value": phone}]}
            ]
            
            if email:
                custom_fields.append({"field_id": settings.AMOCRM_EMAIL_FIELD_ID, "values": [{"value": email}]})
            if name:
                custom_fields.append({"field_id": settings.AMOCRM_NAME_FIELD_ID, "values": [{"value": name}]})
            
            # Добавляем комментарий в название или отдельное поле? 
            # По заданию просто формируем название с типом формы.
            
            payload = [{
                "name": f"Заявка с лендинга ({form_type})",
                "pipeline_id": settings.AMOCRM_PIPELINE_ID,
                "status_id": settings.AMOCRM_STATUS_ID,
                "tags": ["Запрос с лендинга"],
                "custom_fields_values": custom_fields
            }]

            response = await client.post(f"{base_url}/api/v4/leads", headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            lead_id = data['_embedded']['leads'][0]['id']
            logger.info(f"Lead created successfully in AmoCRM. ID: {lead_id}")

        except httpx.HTTPError as e:
            logger.error(f"Failed to create lead in AmoCRM: {e}")
            return False, None
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected response format from AmoCRM while creating lead: {e}")
            return False, None

        # 2. Загрузка и прикрепление файла (если есть)
        if file_uuid:
            try:
                uploads_dir = Path(settings.DATA_DIR) / "uploads"
                # Ищем файл по шаблону {file_uuid}_*
                matching_files = list(uploads_dir.glob(f"{file_uuid}_*"))
                
                if not matching_files:
                    logger.warning(f"File with UUID {file_uuid} not found in {uploads_dir}")
                else:
                    file_path = matching_files[0]
                    filename = file_path.name
                    
                    # Загрузка файла в AmoCRM
                    with open(file_path, "rb") as f:
                        file_content = f.read()
                        
                    # Files API требует multipart/form-data
                    # По заданию: POST /api/v4/files
                    files = {"file": (filename, file_content, "application/octet-stream")}
                    
                    # Примечание: Для загрузки файлов заголовки Content-Type не нужны (httpx выставит сам)
                    upload_headers = {"Authorization": f"Bearer {settings.AMOCRM_LONG_TERM_TOKEN}"}
                    
                    upload_res = await client.post(f"{base_url}/api/v4/files", headers=upload_headers, files=files)
                    logger.info(f"AmoCRM file upload status: {upload_res.status_code}")
                    upload_res.raise_for_status()
                    
                    upload_data = upload_res.json()
                    file_id = upload_data['_embedded']['files'][0]['id']
                    logger.info(f"File {filename} uploaded to AmoCRM. ID: {file_id}")
                    
                    # Прикрепление файла к сделке
                    # POST /api/v4/leads/{lead_id}/files
                    attach_payload = {"files": [{"id": file_id}]}
                    attach_res = await client.post(f"{base_url}/api/v4/leads/{lead_id}/files", headers=headers, json=attach_payload)
                    attach_res.raise_for_status()
                    
                    logger.info(f"File {file_id} successfully attached to lead {lead_id}")

            except httpx.HTTPError as e:
                # Согласно заданию: не прерывать выполнение при ошибке с файлом, но залогировать
                logger.error(f"Error handling file for lead {lead_id}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error handling file for lead {lead_id}: {e}")

        return True, lead_id
