# 📝 Makefile - Полное руководство

Все команды для управления проектом Music Recommendation System.

## 🚀 Быстрый старт

```bash
# Запустить ВСЁ одной командой (backend + frontend)
make quickstart

# Посмотреть все команды
make help

# Информация о проекте
make info
```

---

## 📚 Содержание

- [Основные команды](#основные-команды)
- [Docker команды](#docker-команды)
- [База данных](#база-данных)
- [Frontend UI](#frontend-ui)
- [Тестирование](#тестирование)
- [Данные](#данные)
- [Логи и диагностика](#логи-и-диагностика)
- [Качество кода](#качество-кода)
- [Очистка](#очистка)
- [Примеры сценариев](#примеры-сценариев)

---

## Основные команды

### `make quickstart` - Полный запуск системы

Запускает всю систему (backend + frontend) одной командой.

**Что происходит:**
1. Останавливает старые контейнеры
2. Собирает Docker образы (если нужно)
3. Запускает все сервисы
4. Ждет запуска ClickHouse (15 сек)
5. Инициализирует базу данных
6. Проверяет health check
7. Запускает Frontend UI

**Результат:**
- ✅ API: http://localhost:8000
- ✅ Swagger: http://localhost:8000/docs
- ✅ Frontend: http://localhost:8080

**Время:** ~30-45 секунд

### `make help` - Справка

Показывает все доступные команды с описанием.

### `make info` - Информация о проекте

Показывает:
- URL всех сервисов
- Статус контейнеров
- Важные файлы
- Быстрые команды
- Подсказки при ошибках

---

## Docker команды

### Запуск сервисов

```bash
make up              # Запустить ВСЕ сервисы
make up-api          # Только API
make up-clickhouse   # Только ClickHouse
make up-kafka        # Только Kafka + Zookeeper
make up-redis        # Только Redis
```

### Остановка

```bash
make down            # Остановить все сервисы
make stop-api        # Остановить локальный API (не Docker)
```

### Перезапуск

```bash
make restart         # Остановить и запустить все
```

### Статус

```bash
make ps              # Показать статус контейнеров
```

### Сборка образов

```bash
make build           # Собрать Docker образы

# Если нужно пересобрать с нуля:
docker compose down
make build
make up
```

---

## База данных

### Инициализация

```bash
make db-init         # Создать таблицы (безопасно, идемпотентно)
make db-reset        # Пересоздать ClickHouse с нуля (данные удаляются!)
```

### Просмотр

```bash
make db-shell        # Открыть clickhouse-client
make db-tables       # Показать список таблиц
make db-stats        # Статистика: размер и количество строк
```

### Примеры запросов в db-shell

```sql
-- Показать пользователей
SELECT * FROM users LIMIT 10;

-- Показать треки
SELECT * FROM tracks LIMIT 10;

-- Статистика
SELECT count() FROM user_track_interactions;
```

---

## Frontend UI

### Запуск

```bash
make ui              # Запустить на порту 8080
make ui-open         # Открыть в браузере
make ui-stop         # Остановить
```

### `make ui` - Запуск Frontend

**Что делает:**
- Проверяет доступность API
- Запускает Python HTTP сервер на порту 8080
- Выводит URL для открытия

**Результат:**
```
✅ Frontend UI запущен!
   http://localhost:8080
```

**Требования:**
- Python установлен
- Порт 8080 свободен
- API запущено (рекомендуется)

### `make ui-open` - Открыть в браузере

Автоматически открывает http://localhost:8080 в браузере по умолчанию.

**Поддержка:**
- ✅ Windows
- ✅ Linux
- ✅ macOS

### `make ui-stop` - Остановка Frontend

Останавливает HTTP сервер на порту 8080.

---

## Тестирование

```bash
make test            # Запустить все тесты
make test-clickhouse # Только тесты ClickHouse
make test-watch      # Режим watch (автоперезапуск)
```

**Пример вывода:**
```
🧪 Запуск тестов...
====== 60 passed in 8.5s ======
```

---

## Данные

### Генерация тестовых данных

```bash
make seed            # Полный набор (10,000 записей, ~1-2 мин)
make seed-quick      # Минимум (3 юзера, 3 трека, за секунды)
```

**`make seed-quick` создает:**
- 3 пользователя (testuser1, testuser2, testuser3)
- 3 трека (Rock, Pop, Jazz)
- 4 взаимодействия

**`make seed` создает:**
- 100 пользователей
- 500 треков
- 10,000 взаимодействий

---

## Логи и диагностика

### Просмотр логов

```bash
make logs            # Все сервисы (follow)
make logs-api        # Только API
make logs-clickhouse # Только ClickHouse
make logs-kafka      # Только Kafka
make logs-redis      # Только Redis
make logs-errors     # Только ошибки из API
```

### Диагностика

```bash
make diagnose        # Полная диагностика системы
make health          # Health check API
make check-services  # Проверить все сервисы
```

**`make diagnose` показывает:**
1. Статус контейнеров
2. Доступность API
3. Таблицы в БД
4. Количество данных
5. Последние ошибки

---

## Качество кода

```bash
make lint            # Проверить код (flake8 + black)
make lint-install    # Установить линтеры
make format          # Автоформатирование (black)
```

**Линтеры:**
- flake8 - проверка стиля кода
- black - форматирование
- Конфиг: `.flake8` и `pyproject.toml`

---

## Очистка

```bash
make clean           # Удалить кэши и __pycache__
make clean-all       # Полная очистка + volumes
```

**`make clean` удаляет:**
- `__pycache__/`
- `*.pyc`, `*.pyo`
- `.pytest_cache/`
- `*.egg-info/`
- `htmlcov/`, `.coverage`

**`make clean-all` дополнительно:**
- Останавливает контейнеры
- Удаляет volumes (данные БД!)

---

## Локальная разработка

```bash
make install         # Установить зависимости Python
make run-api         # Запустить API локально (не в Docker)
make stop-api        # Остановить локальный API
```

**Сценарий локальной разработки:**
```bash
# 1. Установить зависимости
make install

# 2. Запустить только инфраструктуру
make up-clickhouse
make up-kafka
make up-redis

# 3. Инициализировать БД
make db-init

# 4. Запустить API локально
make run-api

# 5. Запустить Frontend
make ui
```

---

## Примеры сценариев

### Сценарий 1: Первый запуск

```bash
make quickstart      # Запустить всё
make seed-quick      # Создать тестовые данные
make ui-open         # Открыть UI в браузере
```

### Сценарий 2: Перезапуск после изменений

```bash
# Изменили код backend
make restart         # Перезапустить контейнеры

# Изменили frontend
make ui-stop
make ui
```

### Сценарий 3: Отладка проблем

```bash
make diagnose        # Диагностика
make logs-errors     # Смотреть ошибки
make db-stats        # Проверить данные
```

### Сценарий 4: Полная очистка и перезапуск

```bash
make clean-all       # Удалить всё
make quickstart      # Запустить заново
make seed-quick      # Создать данные
```

### Сценарий 5: Разработка с тестами

```bash
# Внести изменения в код
# ...

make format          # Отформатировать
make lint            # Проверить стиль
make test            # Запустить тесты
```

---

## Таблица всех команд

### 🐳 Docker

| Команда | Описание |
|---------|----------|
| `make up` | Запустить все сервисы |
| `make down` | Остановить все сервисы |
| `make restart` | Перезапустить все |
| `make ps` | Статус контейнеров |
| `make build` | Собрать образы |
| `make up-api` | Запустить API |
| `make up-clickhouse` | Запустить ClickHouse |
| `make up-kafka` | Запустить Kafka |
| `make up-redis` | Запустить Redis |

### 🗄️ База данных

| Команда | Описание |
|---------|----------|
| `make db-init` | Создать таблицы |
| `make db-reset` | Пересоздать ClickHouse |
| `make db-shell` | Открыть clickhouse-client |
| `make db-tables` | Показать таблицы |
| `make db-stats` | Статистика таблиц |

### 🎨 Frontend UI

| Команда | Описание |
|---------|----------|
| `make ui` | Запустить UI на порту 8080 |
| `make ui-open` | Открыть в браузере |
| `make ui-stop` | Остановить UI |

### 🧪 Тестирование

| Команда | Описание |
|---------|----------|
| `make test` | Запустить все тесты |
| `make test-clickhouse` | Только ClickHouse тесты |
| `make test-watch` | Режим watch |

### 📊 Данные

| Команда | Описание |
|---------|----------|
| `make seed` | 10,000 записей (~1-2 мин) |
| `make seed-quick` | Минимальные данные (~1 сек) |

### 📋 Логи

| Команда | Описание |
|---------|----------|
| `make logs` | Все сервисы |
| `make logs-api` | Только API |
| `make logs-clickhouse` | Только ClickHouse |
| `make logs-kafka` | Только Kafka |
| `make logs-redis` | Только Redis |
| `make logs-errors` | Только ошибки |

### 🔍 Диагностика

| Команда | Описание |
|---------|----------|
| `make diagnose` | Полная диагностика |
| `make health` | Health check API |
| `make check-services` | Проверить сервисы |

### 🎨 Качество кода

| Команда | Описание |
|---------|----------|
| `make lint` | Проверка кода |
| `make lint-install` | Установить линтеры |
| `make format` | Автоформатирование |

### 🧹 Очистка

| Команда | Описание |
|---------|----------|
| `make clean` | Кэши и __pycache__ |
| `make clean-all` | Полная очистка + volumes |

### 💻 Разработка

| Команда | Описание |
|---------|----------|
| `make install` | Установить зависимости |
| `make run-api` | Запустить API локально |
| `make stop-api` | Остановить локальный API |

### 📖 Информация

| Команда | Описание |
|---------|----------|
| `make help` | Справка по командам |
| `make info` | Информация о проекте |

---

## Часто используемые комбинации

### Разработка backend

```bash
make up-clickhouse up-kafka up-redis  # Инфраструктура
make db-init                          # Инициализация
make run-api                          # API локально
make test                             # Тесты
```

### Разработка frontend

```bash
make quickstart      # Backend в Docker
make ui              # Frontend локально
# Работать с UI...
make ui-stop         # Остановить UI
```

### Отладка

```bash
make diagnose        # Что не так?
make logs-errors     # Ошибки
make db-stats        # Есть ли данные?
make seed-quick      # Создать данные
```

### Чистый перезапуск

```bash
make clean-all       # Удалить всё
make quickstart      # Запустить заново
make seed-quick      # Данные
```

---

## Troubleshooting

### Команда не работает

```bash
# Проверить что Makefile существует
ls -la Makefile

# Проверить синтаксис
make -n quickstart
```

### Docker команды не работают

```bash
# Проверить что Docker запущен
docker ps

# Проверить docker-compose
docker compose version
```

### UI не запускается

```bash
# Проверить что порт свободен
lsof -i :8080           # Linux/Mac
netstat -ano | find "8080"  # Windows

# Остановить старый процесс
make ui-stop

# Запустить снова
make ui
```

### API недоступен

```bash
# Диагностика
make diagnose

# Проверить логи
make logs-api

# Перезапустить
make restart
```

---

## Советы и рекомендации

### ✅ Best Practices

1. **Используйте `make quickstart`** для первого запуска
2. **Используйте `make diagnose`** при проблемах
3. **Используйте `make seed-quick`** для быстрых тестов
4. **Используйте `make logs-errors`** для поиска проблем
5. **Используйте `make clean`** перед коммитом

### 💡 Полезные алиасы

Добавьте в `~/.bashrc` или `~/.zshrc`:

```bash
alias mq='make quickstart'
alias ml='make logs-api'
alias md='make diagnose'
alias mt='make test'
```

### 🎯 Workflow разработки

```bash
# Утро: запуск
make quickstart

# Разработка
# ... изменения кода ...
make format          # Форматирование
make lint            # Проверка
make test            # Тесты

# Коммит
git add .
git commit -m "Feature added"

# Вечер: остановка
make down
```

---

## Порты

| Сервис | Порт | URL |
|--------|------|-----|
| Frontend UI | 8080 | http://localhost:8080 |
| API | 8000 | http://localhost:8000 |
| Swagger | 8000 | http://localhost:8000/docs |
| ClickHouse HTTP | 8123 | http://localhost:8123 |
| ClickHouse Native | 9000 | - |
| Kafka | 9092 | - |
| Redis | 6379 | - |
| Zookeeper | 2181 | - |

---

## Связанные документы

- [README.md](../README.md) - Главная документация
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Быстрая справка
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Решение проблем
- [RUN_TESTS.md](RUN_TESTS.md) - Запуск тестов

---

**Обновлено:** 2025-11-04  
**Версия:** 2.0 (объединенная)

