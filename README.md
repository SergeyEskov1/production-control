# Production Control API

Backend система для управления производственными партиями.

## Технологический стек

- **FastAPI** — REST API
- **PostgreSQL** — база данных
- **SQLAlchemy 2.0** — ORM (async)
- **Alembic** — миграции БД
- **Redis** — кэширование
- **RabbitMQ** — брокер сообщений
- **Celery** — асинхронные задачи
- **MinIO** — файловое хранилище
- **Docker Compose** — контейнеризация

## Быстрый старт
```bash
git clone https://github.com/SergeyEskov1/production-control.git
cd production-control
docker compose up --build
```

API доступен на http://localhost:8000
Документация: http://localhost:8000/docs

## Сервисы

| Сервис | URL |
|--------|-----|
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| RabbitMQ | http://localhost:15672 |
| MinIO | http://localhost:9001 |
| Flower | http://localhost:5555 |

## API Эндпоинты

### Партии
- `POST /api/v1/batches` — создание партий
- `GET /api/v1/batches` — список с фильтрацией
- `GET /api/v1/batches/{id}` — партия по ID
- `PATCH /api/v1/batches/{id}` — обновление

### Продукция
- `POST /api/v1/products` — добавить продукцию
- `POST /api/v1/batches/{id}/aggregate` — агрегация

### Асинхронные задачи
- `POST /api/v1/tasks/batches/{id}/aggregate-async` — массовая агрегация
- `POST /api/v1/tasks/batches/{id}/reports` — генерация отчёта
- `GET /api/v1/tasks/{task_id}` — статус задачи

### Webhooks
- `POST /api/v1/webhooks` — создать подписку
- `GET /api/v1/webhooks` — список подписок
- `PATCH /api/v1/webhooks/{id}` — обновить
- `DELETE /api/v1/webhooks/{id}` — удалить
- `GET /api/v1/webhooks/{id}/deliveries` — история доставок

### Аналитика
- `GET /api/v1/analytics/dashboard` — статистика
- `GET /api/v1/analytics/batches/{id}` — статистика партии
- `POST /api/v1/analytics/compare-batches` — сравнение

## Запуск тестов
```bash
docker compose exec api pytest tests/ -v
```

## Структура проекта
```
src/
├── api/v1/          # Роутеры и схемы
├── core/            # Настройки, БД, кэш
├── data/            # Модели и репозитории
├── domain/          # Бизнес логика
├── storage/         # MinIO сервис
├── tasks/           # Celery задачи
└── utils/           # Утилиты
```
