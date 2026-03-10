# ⚡ Быстрая справка

Самые частые команды для быстрого доступа.

> 💡 **Для полного списка команд**: `make help` или см. [MAKEFILE.md](MAKEFILE.md)

## 🚀 Основные команды

```bash
make up           # Запустить все сервисы
make down         # Остановить все
make rebuild      # Пересобрать и перезапустить
make restart-api  # Перезапустить API
make ps           # Статус контейнеров
make logs-api     # Логи API
make help         # Все доступные команды
```

## 🔍 Диагностика

```bash
make diagnose     # Полная диагностика системы
make health       # Проверить API
make logs-errors  # Показать ошибки
```

## 🗄️ База данных

```bash
make db-init      # Заполнить БД тестовыми данными
make db-tables    # Список таблиц
make db-stats     # Статистика
make db-indexes   # Добавить индексы
```

## 🧪 Тестирование

```bash
make test              # Все тесты
make test-clickhouse   # Только ClickHouse
make test-cache-warmup # Тест прогрева кэша
make test-api-health   # Проверка здоровья API
```

## ⚡ Кэширование (NEW!)

```bash
# Диагностика кэша
curl http://localhost:8000/api/v1/debug/cache/status

# Управление TTL
curl -X POST http://localhost:8000/api/v1/debug/cache/set-ttl/4
curl http://localhost:8000/api/v1/debug/cache/current-ttl

# Прогрев кэша
curl -X POST http://localhost:8000/api/v1/debug/cache/warmup/auto
curl http://localhost:8000/api/v1/debug/cache/warmup/stats

# Тестирование
make test-cache-warmup
make test-api-health
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
| Kafka | 9092 | Events (localhost) |
| Kafka Internal | 29092 | Docker контейнеры |
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

### API возвращает 500 ошибку
```bash
make db-init           # Создать тестовые данные
make logs-errors       # Посмотреть ошибки
```

### ClickHouse не подключается
```bash
make fix-clickhouse    # Автоматическое исправление
make db-reset          # Полный сброс БД
```

### Docker образ устарел
```bash
make build             # Собрать образы
make rebuild           # Пересобрать и перезапустить
```

### Нужно очистить все
```bash
make clean-all         # Полная очистка (включая volumes)
```

## 📚 Документация

- **[README.md](../README.md)** - Главная страница
- **[INDEX.md](INDEX.md)** - Навигация по документам
- **[MAKEFILE.md](MAKEFILE.md)** - Полное руководство по командам
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Решение проблем
- **[TESTING.md](TESTING.md)** - Тестирование

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
git status                              # Статус
git commit -m "Fix bug"                 # Commit
git push origin main                    # Push
```

## 💡 Полезные ссылки

- **[FastAPI Docs](https://fastapi.tiangolo.com/)** - Документация FastAPI
- **[ClickHouse Docs](https://clickhouse.com/docs/)** - Документация ClickHouse
- **[Swagger UI](http://localhost:8000/docs)** - Интерактивная API документация

---

**💡 Совет**: Начните с `make up && make db-init` - это самый простой способ запустить проект!

