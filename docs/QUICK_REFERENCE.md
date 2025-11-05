# ⚡ Быстрая справка

Самые частые команды для быстрого доступа.

> 💡 **Для полного списка команд**: `make help` или см. [MAKEFILE.md](MAKEFILE.md)

## 🚀 Основные команды

```bash
make quickstart    # Запустить всё сразу (рекомендуется)
make up           # Запустить все сервисы
make down         # Остановить все
make restart      # Перезапустить
make ps           # Статус контейнеров
make logs-api     # Логи API
make help         # Все доступные команды
```

## 🔍 Диагностика

```bash
make diagnose     # Полная диагностика системы
make health       # Проверить API
make health       # Health check
make logs-errors  # Показать ошибки
```

## 🗄️ База данных

```bash
make db-init      # Инициализация БД (идемпотентно)
make db-tables    # Список таблиц
make db-stats     # Статистика
make seed-quick   # Быстрые тестовые данные
make seed         # Полные тестовые данные (10k записей)
```

## 🧪 Тестирование

```bash
make test              # Все тесты
make test              # Все тесты
make test-clickhouse   # Только ClickHouse
make test-clickhouse   # Только ClickHouse
```

## 🔗 URL-адреса

```
Frontend UI:     http://localhost:8080
Kafka UI:        http://localhost:8081  ⭐ Мониторинг Kafka
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
| Frontend UI | 8080 | Web интерфейс |
| Kafka UI | 8081 | Мониторинг Kafka ⭐ |
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
make seed-quick        # Создать тестовые данные
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
make restart           # Перезапустить всё
```

### Нужно очистить все
```bash
make clean-all         # Полная очистка (включая volumes)
```

## 📚 Документация

- **[README.md](../README.md)** - Главная страница
- **[INDEX.md](INDEX.md)** - Навигация по документам
- **[MAKEFILE.md](MAKEFILE.md)** - Полное руководство по командам
- **[API_ERROR_500.md](API_ERROR_500.md)** - Решение ошибки 500
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Решение проблем
- **[RUN_TESTS.md](RUN_TESTS.md)** - Запуск тестов
- **[PORTS.md](PORTS.md)** - Справочник портов

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
git commit -m "Fix bug"                 # Commit (≤8 слов!) [[memory:7077760]]
git push origin main                    # Push
```

## 💡 Полезные ссылки

- **[FastAPI Docs](https://fastapi.tiangolo.com/)** - Документация FastAPI
- **[ClickHouse Docs](https://clickhouse.com/docs/)** - Документация ClickHouse
- **[Swagger UI](http://localhost:8000/docs)** - Интерактивная API документация

---

**💡 Совет**: Начните с `make quickstart` - это самый простой способ запустить проект!

