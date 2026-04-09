# Архитектурные решения

## Стек
| Компонент | Выбор |
|-----------|-------|
| Бэкенд | FastAPI |
| Фронтенд | HTML/CSS/JS |
| База данных | SQLite (persistent volume) |
| Очередь | SQLite + in-memory retry |
| Шифрование | Fernet |
| Логирование | RotatingFileHandler + stdout |
| Контейнеризация | Docker + docker-compose |
| Rate limiting | slowapi |

## Структура проекта
/app
├── app/
│ ├── main.py
│ ├── core/
│ │ ├── config.py
│ │ ├── security.py
│ │ ├── logging.py
│ │ └── dependencies.py
│ ├── api/v1/
│ │ ├── submit.py
│ │ └── health.py
│ ├── models/lead.py
│ ├── schemas/lead.py
│ ├── services/
│ │ ├── max_client.py
│ │ ├── amocrm_client.py
│ │ ├── queue_service.py
│ │ └── encryption.py
│ └── worker/retry_worker.py
├── data/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md

text

## Переменные окружения (.env.example)
```bash
ENVIRONMENT=development
SECRET_KEY=your-32-char-fernet-key
BASE_URL=http://localhost:8000

MAX_API_URL=https://api.max.ru/v1
MAX_BOT_TOKEN=your_token
MAX_CHAT_ID=123456

AMOCRM_SUBDOMAIN=company
AMOCRM_CLIENT_ID=xxx
AMOCRM_CLIENT_SECRET=xxx
AMOCRM_PIPELINE_ID=123456
AMOCRM_STATUS_ID=654321

RECAPTCHA_SECRET_KEY=xxx
RATELIMIT_DEFAULT=5/minute
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
LOG_LEVEL=INFO
LOG_FILE_PATH=/app/data/logs
Docker
Образ: python:3.10-slim

Volume: ./data:/app/data

Healthcheck: curl -f http://localhost:8000/health || exit 1