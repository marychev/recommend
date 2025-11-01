# ⚡ Быстрая справка

Команды и ссылки для быстрого доступа.

## 🚀 Команды запуска

```bash
# Запустить все сервисы (Docker)
docker-compose up -d

# Запустить только ClickHouse
docker-compose up -d clickhouse

# Запустить приложение
python -m app.main

# Запустить с авторелоадом
uvicorn app.main:app --reload
```

## 🧪 Команды тестирования

```bash
# Пересоздать ClickHouse с правильной конфигурацией
bash scripts/docker-reset-clickhouse.sh

# Все тесты
pytest -v

# Только ClickHouse тесты
pytest tests/clickhouse/ -v

# Только API тесты
pytest tests/test_api.py -v

# С покрытием
pytest --cov=app --cov-report=html

# Конкретный тест
pytest tests/clickhouse/test_connection.py::TestClickHouseConnection::test_connection_success -v
```

## 📊 Утилиты

```bash
# Генерация тестовых данных
python scripts/seed_data.py

# Проверка состояния
curl http://localhost:8000/api/v1/health
```

## 🔗 URL-адреса

```
API Swagger:     http://localhost:8000/docs
API ReDoc:       http://localhost:8000/redoc
Health Check:    http://localhost:8000/api/v1/health
ClickHouse HTTP: http://localhost:8123/
Redis:           localhost:6379
Kafka:           localhost:9092
```

## 🔌 Порты

| Сервис | Порт | Примечание |
|--------|------|------------|
| FastAPI | 8000 | REST API |
| ClickHouse HTTP | 8123 | Для приложения ✅ |
| ClickHouse Native | 9000 | Для CLI |
| Redis | 6379 | Cache |
| Kafka | 9092 | Events |
| Zookeeper | 2181 | Kafka coord |

## 📝 Проверка сервисов

```bash
# ClickHouse
curl http://localhost:8123/
# Ответ: Ok.

# Redis
redis-cli ping
# Ответ: PONG

# API
curl http://localhost:8000/
# Ответ: {"message": "Music Recommendation System API", ...}

# Docker containers
docker-compose ps
```

## 🐛 Быстрые исправления

### ClickHouse не подключается
```bash
bash scripts/docker-reset-clickhouse.sh
```

### Нужно очистить все
```bash
docker-compose down
docker volume prune -f
docker-compose up -d
```

### Забыли порт
См. [PORTS.md](PORTS.md) - ClickHouse использует порт **8123** (не 9000!)

## 📚 Документация

```bash
# Главная
cat README.md

# Документация
cat docs/INDEX.md

# Тесты
cat docs/RUN_TESTS.md

# Порты
cat docs/PORTS.md
```

## 🎯 API Примеры

### Создать пользователя
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@test.com", "age": 25}'
```

### Создать трек
```bash
curl -X POST http://localhost:8000/api/v1/tracks \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Song", "artist": "Test Artist", "genre": "Rock"}'
```

### Отправить событие
```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "track_id": 1, "action_type": "play", "listen_duration_seconds": 180}'
```

### Получить рекомендации
```bash
curl http://localhost:8000/api/v1/recommendations/1
```

## 🔄 Git команды

```bash
# Статус
git status

# Commit (не больше 8 слов!)
git commit -m "Add recommendation system"

# Push
git push origin main
```

## 💾 Backup

```bash
# ClickHouse данные
docker run --rm --volumes-from music_recommend_clickhouse \
  -v $(pwd)/backup:/backup ubuntu tar cvf /backup/clickhouse.tar /var/lib/clickhouse

# Redis snapshot
docker exec music_recommend_redis redis-cli SAVE
```

## 📖 Полезные ссылки

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [ClickHouse Docs](https://clickhouse.com/docs/)
- [Pytest Docs](https://docs.pytest.org/)
- [Docker Docs](https://docs.docker.com/)

---

**Сохраните эту страницу в закладки!** 📌

