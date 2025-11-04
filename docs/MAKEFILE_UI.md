# 🎨 Makefile команды для Frontend UI

## Быстрая справка

### Запуск всей системы

```bash
# Запустить ВСЁ сразу (backend + frontend)
make quickstart-full

# Что происходит:
# 1. Останавливает старые контейнеры
# 2. Собирает Docker образы
# 3. Запускает все сервисы (ClickHouse, Kafka, Redis, API)
# 4. Инициализирует базу данных
# 5. Запускает Frontend UI на порту 8080
```

### Только Frontend

```bash
# Запустить Frontend UI
make ui

# Открыть в браузере
make ui-open

# Остановить Frontend
make ui-stop
```

### Только Backend

```bash
# Запустить только backend (без UI)
make quickstart

# Что происходит:
# 1. Запускает Docker контейнеры
# 2. Инициализирует базу данных
# 3. Проверяет health check
# API доступен на http://localhost:8000
```

## Подробное описание команд

### `make ui`

**Что делает:**
- Проверяет доступность API
- Запускает Python HTTP сервер на порту 8080
- Выводит ссылку для открытия

**Использование:**
```bash
make ui
```

**Вывод:**
```
🎨 Запуск Frontend UI...

📡 Проверка доступности API...
✅ API доступен на http://localhost:8000

🌐 Запуск HTTP сервера на порту 8080...

✅ Frontend UI запущен!

════════════════════════════════════════════════
🎨 Откройте в браузере:
   http://localhost:8080
════════════════════════════════════════════════

💡 Остановить: make ui-stop
```

**Требования:**
- Python установлен (для http.server)
- Порт 8080 свободен
- API запущено (опционально, но рекомендуется)

### `make ui-open`

**Что делает:**
- Открывает http://localhost:8080 в браузере по умолчанию

**Использование:**
```bash
make ui-open
```

**Поддерживаемые ОС:**
- ✅ Windows (через `python -m webbrowser`)
- ✅ Linux (через `xdg-open`)
- ✅ macOS (через `open`)

### `make ui-stop`

**Что делает:**
- Останавливает Python HTTP сервер на порту 8080
- Убивает процесс `python -m http.server 8080`

**Использование:**
```bash
make ui-stop
```

**Вывод:**
```
🛑 Остановка Frontend UI...
✅ Frontend UI остановлен
```

### `make quickstart-full`

**Что делает:**
1. Вызывает `make quickstart` (backend)
2. Вызывает `make ui` (frontend)

**Использование:**
```bash
make quickstart-full
```

**Это полный запуск системы:**
- ClickHouse (порт 8123)
- Kafka (порт 9092)
- Redis (порт 6379)
- API (порт 8000)
- Frontend UI (порт 8080)

**Время запуска:** ~30 секунд

### `make quickstart`

**Что делает:**
Только backend (без UI):
1. Останавливает старые контейнеры
2. Собирает Docker образы
3. Запускает сервисы
4. Ждет 15 секунд (для ClickHouse)
5. Инициализирует базу данных
6. Проверяет API и health check

**Использование:**
```bash
make quickstart
```

**В конце напоминает:**
```
💡 Запустить Frontend UI: make ui
```

## Примеры использования

### Сценарий 1: Полный запуск с нуля

```bash
# Запустить всё сразу
make quickstart-full

# Подождать ~30 секунд
# Frontend автоматически откроется на http://localhost:8080
```

### Сценарий 2: Запуск только UI (backend уже работает)

```bash
# Если backend уже запущен
make ui

# Или сразу открыть в браузере
make ui && make ui-open
```

### Сценарий 3: Перезапуск только UI

```bash
# Остановить UI
make ui-stop

# Запустить снова
make ui
```

### Сценарий 4: Работа без UI

```bash
# Запустить только backend
make quickstart

# API доступен на http://localhost:8000/docs
# Frontend не запущен
```

### Сценарий 5: Полная остановка

```bash
# Остановить UI
make ui-stop

# Остановить все Docker контейнеры
make down
```

## Проверка статуса

### Проверить что работает

```bash
# Проверить Docker контейнеры
make ps

# Проверить API
make health

# Проверить есть ли данные
make db-stats
```

### Проверить UI

```bash
# Проверить что UI запущен
ps aux | grep "http.server 8080"

# Или просто откройте в браузере
make ui-open
```

## Troubleshooting

### UI не запускается

**Проблема:** `make ui` выдает ошибку

**Причины:**
1. Порт 8080 занят
2. Python не установлен
3. Папка `frontend/` не найдена

**Решение:**
```bash
# Проверить что порт свободен
lsof -i :8080           # Linux/Mac
netstat -ano | find "8080"  # Windows

# Если занят - убить процесс
make ui-stop

# Проверить что Python установлен
python --version

# Проверить что папка frontend существует
ls -la frontend/
```

### API недоступен

**Проблема:** UI запущен, но показывает "API недоступен"

**Решение:**
```bash
# Проверить что API запущено
make api-status

# Если нет - запустить
make up-api

# Проверить health check
make health
```

### Браузер не открывается

**Проблема:** `make ui-open` не открывает браузер

**Решение:**
```bash
# Открыть вручную
# В браузере: http://localhost:8080
```

## Полезные комбинации

### Полный цикл разработки

```bash
# 1. Запустить систему
make quickstart-full

# 2. Создать тестовые данные
make seed-quick

# 3. Работать с UI на http://localhost:8080

# 4. При изменении backend
make restart        # Перезапустить Docker

# 5. При изменении frontend
make ui-stop && make ui  # Перезапустить UI

# 6. Остановить всё
make ui-stop && make down
```

### Быстрая проверка

```bash
# Проверить всё за раз
make diagnose

# Показывает:
# - Статус контейнеров
# - Доступность API
# - Таблицы в БД
# - Количество данных
# - Последние ошибки
```

### Логи и отладка

```bash
# Логи API
make logs-api

# Только ошибки
make logs-errors

# Логи всех сервисов
make logs
```

## Порты

| Сервис | Порт | Команда Makefile |
|--------|------|------------------|
| Frontend UI | 8080 | `make ui` |
| API | 8000 | `make up-api` |
| Swagger | 8000 | http://localhost:8000/docs |
| ClickHouse | 8123 | `make up-clickhouse` |
| Kafka | 9092 | `make up-kafka` |
| Redis | 6379 | `make up-redis` |

## Дополнительные команды

```bash
# Показать все команды
make help

# Информация о системе
make info

# Открыть Swagger документацию
make docs

# Создать тестовые данные
make seed-quick     # Быстро (минимум)
make seed           # Полный набор (10,000 записей)
```

## Связанные документы

- [README.md](../README.md) - Главная документация
- [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) - Полное руководство по Makefile
- [frontend/README.md](../frontend/README.md) - Документация Frontend
- [QUICKSTART_UI.md](../QUICKSTART_UI.md) - Быстрый старт UI

---

**Обновлено:** 2025-11-04  
**Версия:** 1.0

