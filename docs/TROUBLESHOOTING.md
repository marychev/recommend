# 🆘 Решение проблем (Troubleshooting)

Руководство по решению распространенных проблем.

## 🔍 Диагностика

### Проверка всех сервисов

```bash
bash scripts/check_services.sh
```

Этот скрипт проверит:
- ✅ ClickHouse (порт 8123)
- ✅ Redis (порт 6379)
- ✅ FastAPI (порт 8000)
- ✅ Docker контейнеры

---

## ❌ Ошибка: "ClickHouse client not connected"

### Симптомы
```json
{
  "detail": "Ошибка при получении списка пользователей: ClickHouse client not connected"
}
```

### Причина
ClickHouse не запущен или приложение не смогло подключиться.

### Решение

#### 1. Проверьте что ClickHouse запущен:

```bash
# Проверка через curl
curl http://localhost:8123/
# Должен вернуть: Ok.

# Проверка Docker контейнеров
docker ps | grep clickhouse

# Логи ClickHouse
docker logs music_recommend_clickhouse
```

#### 2. Запустите ClickHouse:

```bash
# Вариант A: Через docker-compose
docker-compose up -d clickhouse

# Вариант B: Пересоздать с правильной конфигурацией
bash scripts/docker-reset-clickhouse.sh
```

#### 3. Дождитесь запуска (10-15 секунд):

```bash
# Проверяйте каждые 2 секунды
while ! curl -s http://localhost:8123/ > /dev/null; do
    echo "Ждем ClickHouse..."
    sleep 2
done
echo "✅ ClickHouse запущен!"
```

#### 4. Перезапустите приложение:

```bash
# Остановите (Ctrl+C если запущено)
# Запустите заново
python -m app.main
```

#### 5. Проверьте подключение:

```bash
curl http://localhost:8000/api/v1/health
```

Должен вернуть:
```json
{
  "status": "healthy",
  "services": {
    "clickhouse": "connected",
    "redis": "connected"
  }
}
```

---

## ❌ Ошибка: "Authentication failed"

### Симптомы
```
Code: 194. DB::Exception: default: Authentication failed
```

### Причина
ClickHouse требует пароль (версии 25.x+).

### Решение

```bash
# Пересоздайте контейнер с правильной конфигурацией
bash scripts/docker-reset-clickhouse.sh

# При запросе удалить volume - ответьте Y (да)
```

Это применит конфигурацию из `clickhouse-config/users.xml` без пароля.

---

## ❌ Ошибка: "Port 9000 is for clickhouse-client program"

### Симптомы
```
Port 9000 is for clickhouse-client program
You must use port 8123 for HTTP
```

### Причина
Неправильный порт в конфигурации.

### Решение

Обновите `.env`:
```env
CLICKHOUSE_PORT=8123  # ← HTTP порт (не 9000!)
```

Перезапустите приложение.

> 💡 **Справка по портам**: [PORTS.md](PORTS.md)

---

## ❌ Ошибка: "Database does not exist"

### Симптомы
```
DB::Exception: Database music_recommend does not exist
```

### Причина
Таблицы не созданы в ClickHouse.

### Решение

```bash
# Создайте таблицы через Docker
docker exec -i music_recommend_clickhouse clickhouse-client < app/db/clickhouse_schemas.sql

# Или через локальный CLI
clickhouse-client < app/db/clickhouse_schemas.sql

# Проверьте что таблицы созданы
docker exec -it music_recommend_clickhouse clickhouse-client
# В clickhouse-client:
SHOW DATABASES;
USE music_recommend;
SHOW TABLES;
```

---

## ❌ Ошибка: "Connection refused"

### Симптомы
```
Connection refused on port 8123
```

### Причина
ClickHouse не запущен.

### Решение

```bash
# Запустите ClickHouse
docker-compose up -d clickhouse

# Проверьте статус
docker ps | grep clickhouse

# Подождите 10 секунд
sleep 10

# Проверьте подключение
curl http://localhost:8123/
```

---

## ❌ Тесты не проходят

### Симптомы
```
ERROR at setup of test_connection_success
```

### Решение

#### 1. Проверьте ClickHouse:
```bash
docker ps | grep clickhouse
curl http://localhost:8123/
```

#### 2. Пересоздайте контейнер:
```bash
bash scripts/docker-reset-clickhouse.sh
```

#### 3. Запустите тесты снова:
```bash
pytest tests/clickhouse/test_connection.py -v
```

---

## ❌ Docker контейнеры не запускаются

### Симптомы
```
ERROR: Cannot start service clickhouse
```

### Решение

```bash
# Очистите все
docker-compose down
docker volume prune -f

# Запустите заново
docker-compose up -d

# Проверьте логи
docker-compose logs
```

---

## ❌ "ModuleNotFoundError"

### Симптомы
```python
ModuleNotFoundError: No module named 'fastapi'
```

### Причина
Зависимости не установлены.

### Решение

```bash
# Активируйте virtual environment
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt

# Для тестов также нужно:
pip install pytest pytest-asyncio pytest-cov httpx
```

---

## ⚠️ Предупреждения Pydantic

### Симптомы
```
PydanticDeprecatedSince20: Using extra keyword arguments on Field is deprecated
```

### Причина
Уже исправлено в v1.0.0!

### Проверка

Убедитесь что используете актуальную версию:
```bash
git pull origin main
```

---

## 🔧 Общая диагностика

### 1. Проверка всех сервисов

```bash
bash scripts/check_services.sh
```

### 2. Проверка портов

```bash
# Linux/Mac
netstat -an | grep -E '8000|8123|6379|9092'

# Windows (PowerShell)
netstat -an | findstr "8000 8123 6379 9092"
```

### 3. Проверка Docker

```bash
# Статус всех контейнеров
docker-compose ps

# Логи всех сервисов
docker-compose logs

# Логи конкретного сервиса
docker logs music_recommend_clickhouse
```

### 4. Проверка приложения

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Root endpoint
curl http://localhost:8000/

# Swagger UI
http://localhost:8000/docs
```

---

## 🚨 Экстренное восстановление

Если ничего не помогает:

```bash
# 1. Остановите всё
docker-compose down
pkill -f "uvicorn app.main"

# 2. Очистите volumes
docker volume prune -f

# 3. Удалите __pycache__
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# 4. Переустановите зависимости
pip install --force-reinstall -r requirements.txt

# 5. Запустите заново
docker-compose up -d
sleep 15

# 6. Создайте таблицы
docker exec -i music_recommend_clickhouse clickhouse-client < app/db/clickhouse_schemas.sql

# 7. Запустите приложение
python -m app.main
```

---

## 📞 Нужна помощь?

1. Проверьте [docs/QUICK_REFERENCE.md](QUICK_REFERENCE.md)
2. Прочитайте [docs/PORTS.md](PORTS.md)
3. Посмотрите логи: `docker logs music_recommend_clickhouse`

---

## ✅ Контрольный чек-лист

Перед запуском проверьте:

- [ ] Docker запущен
- [ ] ClickHouse контейнер работает (`docker ps | grep clickhouse`)
- [ ] Порт 8123 доступен (`curl http://localhost:8123/`)
- [ ] Таблицы созданы (`SHOW TABLES` в clickhouse-client)
- [ ] `.env` файл существует
- [ ] Порт в `.env` = 8123 (не 9000!)
- [ ] Зависимости установлены (`pip list | grep fastapi`)

Если всё ✅, то команда должна работать:
```bash
curl http://localhost:8000/api/v1/health
```

---

**Проблема не решена?** Создайте issue с выводом команды:
```bash
bash scripts/check_services.sh
```

