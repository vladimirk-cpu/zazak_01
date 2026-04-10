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
| Файловые операции | aiofiles (асинхронно) |
| Email клиент | aiosmtplib (SMTP с TLS) |
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
│ │ ├── health.py
│ │ └── upload.py
│ ├── models/lead.py
│ ├── schemas/lead.py
│ ├── services/
│ │ ├── max_client.py
│ │ ├── amocrm_client.py
│ │ ├── queue_service.py
│ │ ├── encryption.py
│ │ └── email_client.py
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
AMOCRM_REDIRECT_URI=https://ваш-домен.ru/amocrm/callback
AMOCRM_PIPELINE_ID=123456
AMOCRM_STATUS_ID=654321
AMOCRM_FORM_TYPE_FIELD_ID=123456

RECAPTCHA_SECRET_KEY=xxx
RATELIMIT_DEFAULT=5/minute
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
LOG_LEVEL=INFO
LOG_FILE_PATH=/app/data/logs
Docker
Образ: python:3.10-slim

Volume: ./data:/app/data

Healthcheck: curl -f http://localhost:8000/health || exit 1

## Особенности реализации
- Автоматическое создание папки `data/uploads/` при инициализации БД (`init_db`).
- Имя загруженного файла: `{uuid4}_{original_name}`.
- Валидация размера (10 МБ) и расширений (PDF, Word, Excel).
- Имя файла очищается через `os.path.basename()` (защита от Path Traversal).
- Прямое чтение `contents = await file.read()` для гарантии записи всех байт.

## Безопасность (Hardening)
- **CORS**: Ограничен белый список доменов (BASE_URL + localhost).
- **Rate Limiting**: 5 запросов в минуту на отправку форм (slowapi).
- **Body Size**: Лимит 1 МБ на JSON-тело запроса (защита от OOM).
- **Pydantic Hardening**: Поля имеют `max_length` для защиты БД от спама длинными строками.
- **Privacy**: Персональные данные (ПДн) исключены из логов во всех сервисах.
- **Stability**: Воркер обрабатывает каждый лид в изолированном блоке `try...except`.
- **Docker**: Использование `.dockerignore` для исключения секретов из образа.

## Оптимизация SQLite (Concurrency & Performance)
- **WAL Mode**: Включено `PRAGMA journal_mode=WAL` для параллельного чтения и записи без блокировок.
- **Tuning**: Увеличен таймаут ожидания до 30 секунд и включен `pool_pre_ping`.
- **Worker Refactoring**: Из воркера удалены долгие транзакции; сетевые вызовы (AmoCRM, Email) вынесены за пределы блокировок базы данных.