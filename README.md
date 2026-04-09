# Backend API

## Локальный запуск
1. Создайте `.env` файл на основе `.env.example`:
   `cp .env.example .env` (или скопируйте файл вручную)
2. Запустите Docker Compose:
   `docker-compose up --build`

## Отправка тестовой заявки
```bash
curl -X POST http://localhost:8000/api/submit \
  -H "Content-Type: application/json" \
  -d '{"name":"Тест","phone":"+79991234567","comment":"Тестовая заявка"}'
```

## Healthcheck
```bash
curl http://localhost:8000/health
```

## На что обратить внимание при тестировании
1. Логи работы приложения сохраняются в `data/logs/app.log` и выводятся в консоль docker.
2. Проверьте запуск фоновой задачи — после отправки корректного запроса должны появиться логи о начале попыток отправки через замоканные API MAX Messenger и AMOCRM.
3. ПДн (имя, телефон) должны сохраняться в базе данных `/data/app.db` в зашифрованном виде.
4. Ограничение запросов (rate limiter) настроено на 5 запросов в минуту. На 6-й запрос придет ошибка `429 Too Many Requests`.
