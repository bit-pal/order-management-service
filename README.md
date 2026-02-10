# Сервис управления заказами (Order Management Service)

Сервис на FastAPI: аутентификация (JWT OAuth2), заказы, кеширование в Redis, очередь сообщений RabbitMQ и фоновые задачи Celery.

## Стек

- **API:** FastAPI, Pydantic
- **БД:** PostgreSQL, SQLAlchemy (async), Alembic
- **Кеш:** Redis (заказы, TTL 5 мин)
- **Очередь событий:** RabbitMQ (event-bus: событие `new_order`)
- **Фоновые задачи:** Celery (брокер Redis)
- **Безопасность:** JWT, CORS, rate limiting, только ORM

## Требования

- Docker и Docker Compose (рекомендуется)
- либо: Python 3.12+, PostgreSQL, Redis, RabbitMQ

## Установка и запуск

### Вариант 1: Docker Compose (рекомендуется)

1. Клонируйте репозиторий и перейдите в каталог проекта.

2. Создайте файл `.env` из примера и при необходимости отредактируйте (обязательно задайте `SECRET_KEY` для production):

   ```bash
   cp .env.example .env
   ```

3. Запустите все сервисы:

   ```bash
   docker-compose up --build
   ```

4. После старта:
   - **API:** http://localhost:8000  
   - **Swagger UI:** http://localhost:8000/docs  
   - **ReDoc:** http://localhost:8000/redoc  

Состав контейнеров: `postgres`, `redis`, `rabbitmq`, `api` (FastAPI + миграции), `celery_worker`, `consumer` (подписка на RabbitMQ и запуск задач Celery).

### Вариант 2: Локальный запуск (без Docker)

1. Создайте виртуальное окружение и установите зависимости:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate   # Linux/macOS
   pip install -r requirements.txt
   ```

2. Поднимите PostgreSQL, Redis и RabbitMQ (локально или в Docker).

3. Создайте `.env` по образцу `.env.example` и укажите хосты (например, `localhost`).

4. Примените миграции:

   ```bash
   alembic upgrade head
   ```

5. В трёх отдельных терминалах запустите:

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   celery -A celery_app worker --loglevel=info
   python -m consumer.run_consumer
   ```

## API

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/v1/register/` | Регистрация (email, пароль) |
| POST | `/api/v1/token/` | Получение JWT (OAuth2 Password: username=email, password) |
| POST | `/api/v1/orders/` | Создание заказа (только авторизованные) |
| GET | `/api/v1/orders/{order_id}/` | Получение заказа (сначала из Redis) |
| PATCH | `/api/v1/orders/{order_id}/` | Обновление статуса заказа |
| GET | `/api/v1/orders/user/{user_id}/` | Список заказов пользователя |

В Swagger UI (`/docs`) можно получить токен через "Authorize" (username = email, password = пароль пользователя) и вызывать защищённые эндпоинты.

## Переменные окружения (.env)

Основные переменные заданы в `.env.example`:

- `SECRET_KEY` — секрет для JWT (обязательно в production).
- `POSTGRES_*`, `REDIS_*`, `RABBITMQ_*` — подключение к БД, Redis и RabbitMQ.
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` — брокер и backend для Celery (Redis).
- `CORS_ORIGINS` — разрешённые origins через запятую.
- `RATE_LIMIT_PER_MINUTE` — лимит запросов в минуту на IP.

## Критерии приёмки (соответствие ТЗ)

- Реализованы все перечисленные API-эндпоинты.
- Регистрация и JWT (OAuth2 Password Flow), защита эндпоинтов заказа.
- Redis: кеш заказов при GET, инвалидация при PATCH.
- RabbitMQ: при создании заказа публикуется событие `new_order`; отдельный consumer подписан на очередь и запускает задачу Celery.
- Celery: фоновая задача обработки заказа (sleep 2 c, вывод в лог).
- Развёртывание через `docker-compose up`.
- Swagger UI и README с установкой и запуском.
- Ошибки обрабатываются с корректными HTTP-статусами, конфигурация через переменные окружения без хардкода секретов.
