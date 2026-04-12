# Backend API

## Локальный запуск
1. Создайте `.env` файл на основе `.env.example`:
   `cp .env.example .env` (или скопируйте файл вручную)
2. Запустите Docker Compose:
   `docker-compose up --build`
   *По умолчанию данные сохраняются в `./data`.*

## Деплой на Amvera
Проект готов к деплою на Amvera. Используйте `amvera.yml`. 
Persistent volume должен быть примонтирован в `/data`.
Переменная окружения `DATA_DIR` установлена в `/data`.

## Healthcheck
```bash
curl http://localhost:8000/health
```

## На что обратить внимание
1. Все данные (база, логи, загрузки) сохраняются в директорию, указанную в `DATA_DIR`.
2. Логи доступны в `{DATA_DIR}/logs/app.log`.
3. ПДн сохраняются в зашифрованном виде в `{DATA_DIR}/app.db`.
