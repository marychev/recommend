# 📝 Makefile - Краткое руководство

## 🚀 Быстрый старт

```bash
# Запустить всё одной командой
make quickstart
```

Эта команда:
1. ✅ Остановит старые контейнеры
2. ✅ Запустит все сервисы (включая API)
3. ✅ Инициализирует базу данных
4. ✅ Проверит что API работает
5. ✅ Покажет ссылки на документацию

## 📊 Проверка статуса

```bash
# Полная информация о проекте
make info

# Проверить работает ли API
make api-status

# Проверить health check
make health

# Статус всех контейнеров
make ps
```

## 🐳 Управление сервисами

### Запуск

```bash
make up              # Запустить ВСЕ сервисы (включая API)
make up-api          # Только API контейнер
make up-infra        # Только инфраструктура (без API)
make up-clickhouse   # Только ClickHouse
make up-redis        # Только Redis
make up-kafka        # Только Kafka + Zookeeper
```

### Остановка

```bash
make down            # Остановить все сервисы
make stop-api        # Остановить локальный API (не Docker)
```

### Перезапуск

```bash
make restart         # Перезапустить все
make rebuild         # Пересобрать ВСЕ образы и перезапустить
make rebuild-api     # Пересобрать только API образ (быстрее!)
```

## 📋 Логи

```bash
make logs            # Логи всех сервисов
make logs-api        # Только API
make logs-clickhouse # Только ClickHouse
make logs-kafka      # Только Kafka
make logs-redis      # Только Redis
```

## 🗄️ База данных

```bash
make db-init         # Инициализация БД (безопасно, идемпотентно)
make db-reset        # Полный сброс БД (удаляет данные!)
make db-shell        # Открыть clickhouse-client
make db-tables       # Список таблиц
make db-stats        # Статистика по таблицам
make seed            # Генерация тестовых данных
```

## 🧪 Тестирование

```bash
make test            # Все тесты
make test-coverage   # С покрытием кода
make test-api        # Только API тесты
make test-clickhouse # Только ClickHouse тесты
```

## 💻 Локальная разработка

```bash
make install         # Установить Python зависимости
make run-api         # Запустить API локально (не в Docker)
make stop-api        # Остановить локальный API
```

**Типичный сценарий разработки:**
```bash
# 1. Запустить только инфраструктуру
make up-infra

# 2. Инициализировать БД
make db-init

# 3. Запустить API локально для отладки
make run-api

# 4. В другом терминале смотреть логи
make logs-clickhouse
```

## 🧹 Очистка

```bash
make clean           # Очистить кэши Python
make clean-all       # Полная очистка (включая volumes!)
```

## 🎨 Качество кода

```bash
make lint            # Проверка линтерами
make format          # Форматирование кода (black)
```

## 📚 Документация

```bash
make docs            # Открыть Swagger UI в браузере
make help            # Показать все доступные команды
make info            # Информация о проекте
```

## 🔍 Диагностика проблем

### API не запускается

```bash
# 1. Проверьте статус
make api-status

# 2. Посмотрите логи (ВАЖНО!)
make logs-api

# 3. Если видите ошибки "ModuleNotFoundError" - пересоберите образ
make rebuild-api

# 4. Проверьте все контейнеры
make ps

# 5. Попробуйте перезапустить
make restart

# 6. Если не помогло - полная пересборка
make rebuild
```

### Ошибка "ModuleNotFoundError: No module named 'aiochclient'"

Это значит что Docker образ устарел. **Решение:**

```bash
# Пересобрать API образ
make rebuild-api

# Или полная пересборка всех образов
make rebuild
```

### ClickHouse не работает

```bash
# 1. Проверьте сервисы
make check-services

# 2. Исправьте проблемы
make fix-clickhouse

# 3. Полный сброс
make db-reset
```

### "Порт уже занят"

```bash
# Остановите все контейнеры
make down

# Проверьте что остановилось
docker ps

# Запустите заново
make up
```

## 💡 Полезные комбинации

```bash
# Полный перезапуск с чистой БД
make clean-all && make quickstart

# Тесты с покрытием и очисткой кэша
make clean && make test-coverage

# Посмотреть логи API в реальном времени
make logs-api

# Быстрая проверка что всё работает
make ps && make api-status && make health
```

## 🌐 Важные URL

После запуска `make up` или `make quickstart`:

- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **ClickHouse HTTP:** http://localhost:8123
- **Redis:** localhost:6379
- **Kafka:** localhost:9092

## ⚙️ Переменные окружения

Makefile автоматически использует файл `.env`:

```bash
# Создайте .env из примера (если ещё не создан)
cat > .env << 'EOF'
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
API_PORT=8000
# ... остальные настройки
EOF
```

## 🆘 Помощь

```bash
# Показать все команды с описанием
make help

# Информация о проекте и статусе
make info
```

## 📖 См. также

- [README.md](README.md) - Основная документация
- [docs/DB_INIT.md](docs/DB_INIT.md) - Инициализация БД
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Решение проблем
- [docs/INDEX.md](docs/INDEX.md) - Навигация по документации

---

**🎯 Запомните главное:**
- `make quickstart` - запустить всё
- `make api-status` - проверить API
- `make help` - список всех команд

