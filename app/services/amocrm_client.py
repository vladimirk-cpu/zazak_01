import httpx
import os
from pathlib import Path
from typing import Optional
from app.core.config import settings
from app.core.logging import logger

# Кэш для drive_url
_DRIVE_URL_CACHE: Optional[str] = None

async def _get_drive_url(client: httpx.AsyncClient) -> Optional[str]:
    """
    Получает drive_url из настроек аккаунта AmoCRM.
    """
    global _DRIVE_URL_CACHE
    if _DRIVE_URL_CACHE:
        return _DRIVE_URL_CACHE

    try:
        base_url = f"https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru"
        headers = {"Authorization": f"Bearer {settings.AMOCRM_LONG_TERM_TOKEN}"}
        params = {"with": "drive_url"}
        
        logger.info("Fetching drive_url from AmoCRM account settings...")
        response = await client.get(f"{base_url}/api/v4/account", headers=headers, params=params)
        
        if response.status_code != 200:
            logger.error(f"Failed to get account info. Status: {response.status_code}")
            return None
            
        data = response.json()
        drive_url = data.get("drive_url")
        
        if drive_url:
            _DRIVE_URL_CACHE = drive_url
            logger.info(f"Drive URL: {drive_url}")
            return drive_url
        else:
            logger.error("AmoCRM response does not contain drive_url")
            return None
            
    except Exception as e:
        logger.error(f"Error while getting AmoCRM drive_url: {e}")
        return None

async def _upload_file_to_amo(client: httpx.AsyncClient, file_uuid: str) -> Optional[str]:
    """
    Загружает файл в AmoCRM через Drive API и возвращает его uuid.
    """
    try:
        # 1. Поиск локального файла
        uploads_dir = Path(settings.DATA_DIR) / "uploads"
        matching_files = list(uploads_dir.glob(f"{file_uuid}_*"))
        
        if not matching_files:
            logger.warning(f"File with UUID {file_uuid} not found locally")
            return None
            
        file_path = matching_files[0]
        file_name = file_path.name
        file_size = file_path.stat().st_size
        
        # 2. Получение drive_url
        drive_url = await _get_drive_url(client)
        if not drive_url:
            return None

        # 3. Создание сессии загрузки
        if not (drive_url.startswith("http://") or drive_url.startswith("https://")):
            drive_url = f"https://{drive_url}"
            
        session_url = f"{drive_url}/v1.0/sessions"
        headers = {"Authorization": f"Bearer {settings.AMOCRM_LONG_TERM_TOKEN}"}
        session_payload = {
            "file_name": file_name,
            "file_size": file_size
        }
        
        logger.info(f"Creating upload session for {file_name}")
        session_res = await client.post(session_url, headers=headers, json=session_payload)
        
        if session_res.status_code not in (200, 201):
            logger.error(f"Failed to create upload session: {session_res.status_code}")
            return None
            
        resp_data = session_res.json()
        upload_url = resp_data.get("upload_url")
        if not upload_url:
            logger.error("No upload_url in session creation response")
            return None

        # 4. Загрузка файла (PUT)
        with open(file_path, "rb") as f:
            file_content = f.read()
            
        logger.info(f"Uploading file binary to {upload_url}")
        upload_headers = {"Content-Type": "application/octet-stream"}
        
        put_resp = await client.put(upload_url, content=file_content, headers=upload_headers, timeout=60.0)
        logger.info(f"File upload status: {put_resp.status_code}")
        
        if put_resp.status_code != 200:
            logger.error(f"File upload failed: {put_resp.status_code} - {put_resp.text}")
            return None
            
        file_info = put_resp.json()
        amo_file_uuid = file_info.get("uuid")
        
        if amo_file_uuid:
            logger.info(f"File uploaded to Drive, UUID: {amo_file_uuid}")
            return amo_file_uuid
        else:
            logger.error("No uuid in file upload response")
            return None

    except Exception as e:
        logger.error(f"Error during file upload process: {e}")
        return None

async def send_to_amocrm(lead_data: dict) -> tuple[bool, int | None]:
    """
    Создает сделку в AmoCRM и прикрепляет файл.
    """
    phone = lead_data.get("phone")
    name = lead_data.get("name") or ""
    email = lead_data.get("email") or ""
    file_uuid = lead_data.get("file")
    form_type = lead_data.get("form_type", "unknown")
    
    base_url = f"https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru"
    headers = {
        "Authorization": f"Bearer {settings.AMOCRM_LONG_TERM_TOKEN}",
        "Content-Type": "application/json"
    }

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
            
            # В v4 для создания сделки не используем tags в основном запросе (по заданию)
            payload = [{
                "name": f"Заявка с лендинга ({form_type})",
                "pipeline_id": settings.AMOCRM_PIPELINE_ID,
                "status_id": settings.AMOCRM_STATUS_ID,
                "custom_fields_values": custom_fields
            }]

            response = await client.post(f"{base_url}/api/v4/leads", headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            lead_id = data['_embedded']['leads'][0]['id']
            logger.info(f"Lead created in AmoCRM. ID: {lead_id}")

            # Отдельное добавление тега по ID через PATCH
            if settings.AMOCRM_TAG_ID != 0:
                try:
                    tag_payload = {"tags_to_add": [{"id": settings.AMOCRM_TAG_ID}]}
                    tag_resp = await client.patch(f"{base_url}/api/v4/leads/{lead_id}", headers=headers, json=tag_payload)
                    tag_resp.raise_for_status()
                    logger.info(f"Tag {settings.AMOCRM_TAG_ID} added to lead {lead_id}")
                except Exception as e:
                    logger.error(f"Failed to add tag {settings.AMOCRM_TAG_ID} to lead {lead_id}: {e}")
            else:
                logger.warning("AMOCRM_TAG_ID is not set (0), skipping tag attachment")

        except Exception as e:
            logger.error(f"Failed to create lead in AmoCRM: {e}")
            return False, None

        # 2. Загрузка и прикрепление файла
        if file_uuid:
            amo_file_uuid = await _upload_file_to_amo(client, file_uuid)
            
            if amo_file_uuid:
                try:
                    note_url = f"{base_url}/api/v4/leads/{lead_id}/notes"
                    note_payload = [
                        {
                            "note_type": "file",
                            "params": {
                                "file_uuid": amo_file_uuid
                            }
                        }
                    ]
                    note_resp = await client.post(note_url, headers=headers, json=note_payload)
                    note_resp.raise_for_status()
                    logger.info(f"File attached to lead {lead_id}")
                except Exception as e:
                    logger.error(f"Failed to attach file to lead {lead_id}: {e}")
            else:
                logger.warning(f"File attachment skipped for lead {lead_id}")

        return True, lead_id
