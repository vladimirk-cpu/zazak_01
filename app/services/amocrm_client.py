import httpx
import os
from pathlib import Path
from typing import Optional
from app.core.config import settings
from app.core.logging import logger

# Кэш для drive_url, чтобы не запрашивать при каждой заявке
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
        
        logger.info(f"Fetching drive_url from AmoCRM account settings...")
        response = await client.get(f"{base_url}/api/v4/account", headers=headers, params=params)
        
        if response.status_code != 200:
            logger.error(f"Failed to get account info. Status: {response.status_code}, Response: {response.text}")
            return None
            
        data = response.json()
        drive_url = data.get("_embedded", {}).get("drive_url")
        
        if drive_url:
            _DRIVE_URL_CACHE = drive_url
            logger.info(f"AmoCRM drive_url obtained: {drive_url}")
            return drive_url
        else:
            logger.error(f"AmoCRM response does not contain drive_url. Response keys: {list(data.keys())}")
            # Это может указывать на отсутствие прав у токена
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
            logger.warning(f"File with UUID {file_uuid} not found locally in {uploads_dir}")
            return None
            
        file_path = matching_files[0]
        file_name = file_path.name
        file_size = file_path.stat().st_size
        
        # 2. Получение drive_url
        drive_url = await _get_drive_url(client)
        if not drive_url:
            logger.error("Skipping file upload because drive_url is missing")
            return None

        # 3. Создание сессии загрузки
        session_url = f"https://{drive_url}/v1.0/sessions"
        headers = {"Authorization": f"Bearer {settings.AMOCRM_LONG_TERM_TOKEN}"}
        session_payload = {
            "file_name": file_name,
            "file_size": file_size
        }
        
        logger.info(f"Creating AmoCRM upload session: {file_name} ({file_size} bytes)")
        session_res = await client.post(session_url, headers=headers, json=session_payload)
        
        if session_res.status_code != 201:
            logger.error(f"Failed to create upload session. Status: {session_res.status_code}, Response: {session_res.text}")
            return None
            
        session_data = session_res.json()
        upload_url = session_data.get("_links", {}).get("upload", {}).get("href")
        
        if not upload_url:
            logger.error("AmoCRM session response does not contain upload_url")
            return None

        # 4. Загрузка файла (PUT)
        with open(file_path, "rb") as f:
            file_content = f.read()
            
        logger.info(f"Uploading file binary to AmoCRM (PUT {upload_url})")
        upload_headers = {"Content-Type": "application/octet-stream"}
        # Согласно документации Drive API, для самого PUT запроса на upload_url 
        # токен иногда не требуется, если он уже вшит в URL, но добавим для надежности если нужно.
        # Однако пользователь просил именно Content-Type.
        
        upload_res = await client.put(upload_url, content=file_content, headers=upload_headers, timeout=60.0)
        
        if upload_res.status_code not in (200, 201):
            logger.error(f"Failed to upload binary data. Status: {upload_res.status_code}, Response: {upload_res.text}")
            return None
            
        upload_data = upload_res.json()
        amo_file_uuid = upload_data.get("uuid")
        
        if amo_file_uuid:
            logger.info(f"File uploaded successfully to AmoCRM. UUID: {amo_file_uuid}")
            return amo_file_uuid
        else:
            logger.error(f"AmoCRM upload response missing uuid. Response: {upload_data}")
            return None

    except Exception as e:
        logger.error(f"Error during AmoCRM file upload process: {e}")
        return None

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
            
            # Теги передаются как массив объектов (API v4)
            payload = [{
                "name": f"Заявка с лендинга ({form_type})",
                "pipeline_id": settings.AMOCRM_PIPELINE_ID,
                "status_id": settings.AMOCRM_STATUS_ID,
                "tags": [{"name": "Запрос с лендинга"}],
                "custom_fields_values": custom_fields
            }]

            response = await client.post(f"{base_url}/api/v4/leads", headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            lead_id = data['_embedded']['leads'][0]['id']
            logger.info(f"Lead created successfully in AmoCRM. ID: {lead_id}")

        except Exception as e:
            logger.error(f"Failed to create lead in AmoCRM: {e}")
            return False, None

        # 2. Загрузка и прикрепление файла (если есть)
        if file_uuid:
            amo_file_uuid = await _upload_file_to_amo(client, file_uuid)
            
            if amo_file_uuid:
                try:
                    # Прикрепление файла к сделке через Note (тип file)
                    note_url = f"{base_url}/api/v4/leads/{lead_id}/notes"
                    note_payload = [
                        {
                            "note_type": "file",
                            "params": {
                                "file_uuid": amo_file_uuid
                            }
                        }
                    ]
                    note_res = await client.post(note_url, headers=headers, json=note_payload)
                    note_res.raise_for_status()
                    logger.info(f"File {amo_file_uuid} successfully attached to lead {lead_id}")
                except Exception as e:
                    logger.error(f"Failed to attach file to lead {lead_id}: {e}")
            else:
                logger.warning(f"File attachment skipped for lead {lead_id} due to upload error")

        return True, lead_id
