# Контекст проекта
**Проект:** Лендинг для компании по технической сертификации  
**Дата:** 21.03.2026

## Ключевые требования
- Python 3.10, фиксированные зависимости
- Docker + docker-compose
- Логирование без ПДн (только ID заявок)
- Очередь на SQLite + ретраи (экспоненциальная задержка)
- Шифрование ПДн (Fernet)
- Заглушки для MAX и AMOCRM до получения реальных данных

## Команды для локального запуска
```bash
# Запуск контейнера
docker-compose up --build

# Проверка healthcheck
curl http://localhost:8000/health

# Отправка тестовой заявки
curl -X POST http://localhost:8000/api/submit \
  -H "Content-Type: application/json" \
  -d '{"name":"Тест","phone":"+79991234567","comment":"Тестовая заявка"}'
## Статус реализации
- [x] Бэкенд готов и протестирован локально.
- [x] Все эндпоинты (`/health`, `/api/submit`) доступны.
- [x] База данных и логирование настроены в папке `/data`.

## Ожидаемые файлы (Все созданы)
Dockerfile, docker-compose.yml, requirements.txt, .env.example

app/main.py

app/core/config.py, security.py, logging.py, dependencies.py

app/api/v1/submit.py, health.py

app/models/lead.py

app/schemas/lead.py

app/services/max_client.py, amocrm_client.py, queue_service.py, encryption.py

app/worker/retry_worker.py

README.md (с инструкцией по запуску)

Ссылки на документацию
MAX Bot API: https://api.max.ru/v1/messages?chat_id=... (заголовок Authorization: токен, без Bearer)

AMOCRM API v4: https://www.amocrm.ru/developers

FastAPI: https://fastapi.tiangolo.com

Docker: https://docs.docker.com