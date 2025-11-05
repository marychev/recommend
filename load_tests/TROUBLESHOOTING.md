# 🔧 Устранение неполадок при нагрузочном тестировании

Решения типичных проблем при генерации данных и запуске k6 тестов.

## Проблема: "ClickHouse client not connected"

**Ошибка:**
```
RuntimeError: ClickHouse client not connected
```

**Причина:** Сервисы не запущены или ClickHouse недоступен.

**Решение:**

```bash
# 1. Проверьте статус контейнеров
make ps

# 2. Запустите сервисы, если не запущены
make up

# 3. Подождите ~10 секунд для инициализации ClickHouse
sleep 10

# 4. Попробуйте снова
make load-test-data-generate
```

## Проблема: "Таблицы не созданы"

**Ошибка:**
```
❌ ОШИБКА: Таблицы не созданы!
DB::Exception: Table music_recommend.users doesn't exist
```

**Причина:** База данных не инициализирована.

**Решение:**

```bash
# Создайте таблицы в ClickHouse
make db-init

# Проверьте, что таблицы созданы
make db-tables

# Теперь запускайте генерацию
make load-test-data-generate
```

## Проблема: Медленная генерация данных

**Симптом:** Генерация 1M записей занимает > 15 минут.

**Причины и решения:**

### 1. Недостаточно ресурсов Docker

```bash
# Увеличьте ресурсы в Docker Desktop:
# Settings → Resources
# - CPU: минимум 4 ядра
# - Memory: минимум 8GB
```

### 2. Высокая нагрузка на систему

```bash
# Закройте другие приложения
# Проверьте нагрузку
docker stats

# Если нагрузка высокая, уменьшите размер батчей в скрипте
# Измените в generate_test_data.py:
# batch_size = 5000  # вместо 10000
```

### 3. Медленный диск

```bash
# Используйте SSD вместо HDD
# Или уменьшите количество записей:
python -c "
from load_tests.generate_test_data import DataGenerator
import asyncio

async def main():
    gen = DataGenerator()
    await gen.generate_all(
        users_count=10000,    # вместо 100k
        tracks_count=5000,     # вместо 50k
        interactions_count=85000  # вместо 850k
    )
asyncio.run(main())
"
```

## Проблема: "k6 command not found"

**Ошибка:**
```
k6: command not found
```

**Решение:**

**macOS:**
```bash
brew install k6
```

**Linux (Ubuntu/Debian):**
```bash
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 \
  --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

**Windows:**
```powershell
choco install k6
```

**Проверка:**
```bash
k6 version
```

## Проблема: Высокий процент ошибок в k6 тестах

**Симптом:** 
```
http_req_failed................: 15.00%
```

**Причины и решения:**

### 1. Недостаточно данных в БД

```bash
# Проверьте количество записей
make db-stats

# Если мало данных, сгенерируйте больше
make load-test-data-generate
```

### 2. API возвращает 500 ошибок

```bash
# Проверьте логи API
make logs-errors

# Часто помогает перезапуск
make restart
```

### 3. Слишком высокая нагрузка

```bash
# Уменьшите количество виртуальных пользователей в k6 скрипте
# Измените в k6_basic_load_test.js:
export const options = {
  stages: [
    { duration: '1m', target: 25 },   // вместо 50
    { duration: '3m', target: 50 },   // вместо 100
    // ...
  ],
};
```

## Проблема: "Connection refused" в k6 тестах

**Ошибка:**
```
ERRO[0000] Get "http://localhost:8000/api/v1/users": dial tcp [::1]:8000: connect: connection refused
```

**Причина:** API не запущен или недоступен.

**Решение:**

```bash
# 1. Проверьте, что API запущен
make ps

# 2. Проверьте доступность
curl http://localhost:8000

# 3. Если не работает, перезапустите
make restart

# 4. Проверьте логи
make logs-api

# 5. Если API в Docker не запускается
docker-compose logs api
```

## Проблема: Faker не установлен

**Ошибка:**
```
ModuleNotFoundError: No module named 'faker'
```

**Решение:**

```bash
# Установите зависимости
pip install -r requirements.txt

# Или только Faker
pip install faker
```

## Проблема: Низкое RPS в k6 тестах

**Симптом:** RPS (запросов в секунду) очень низкий (< 10).

**Причины и решения:**

### 1. Кэширование не работает

```bash
# Проверьте Redis
docker-compose logs redis

# Перезапустите Redis
docker-compose restart redis
```

### 2. Медленные запросы к ClickHouse

```bash
# Проверьте производительность
make db-stats

# Оптимизируйте таблицы
docker exec music_recommend_clickhouse clickhouse-client -q "OPTIMIZE TABLE users"
docker exec music_recommend_clickhouse clickhouse-client -q "OPTIMIZE TABLE tracks"
docker exec music_recommend_clickhouse clickhouse-client -q "OPTIMIZE TABLE user_track_interactions"
```

### 3. API работает в одном потоке

```bash
# Увеличьте количество workers в docker-compose.yml
# Измените:
# command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Проблема: Тесты зависают

**Симптом:** k6 тест запускается, но прогресс останавливается.

**Решение:**

```bash
# 1. Проверьте логи API
make logs-api

# 2. Проверьте ресурсы
docker stats

# 3. Если памяти недостаточно, увеличьте лимиты в docker-compose.yml
# В секции services.clickhouse:
# mem_limit: 4g

# 4. Перезапустите все
make down
make up
```

## Проблема: "Table already exists"

**Ошибка при генерации:**
```
Duplicate entry for user_id
```

**Причина:** Данные уже существуют в БД.

**Решения:**

### Вариант 1: Очистить таблицы
```bash
# Очистить все данные (осторожно!)
docker exec music_recommend_clickhouse clickhouse-client -q "TRUNCATE TABLE users"
docker exec music_recommend_clickhouse clickhouse-client -q "TRUNCATE TABLE tracks"
docker exec music_recommend_clickhouse clickhouse-client -q "TRUNCATE TABLE user_track_interactions"

# Или пересоздать БД полностью
make db-reset
```

### Вариант 2: Продолжить с существующими данными
```bash
# Просто запустите тесты с текущими данными
make load-test-quick
```

## Полная диагностика

Если проблема не решается, выполните полную диагностику:

```bash
# 1. Проверка системы
make diagnose

# 2. Статус сервисов
make ps

# 3. Проверка API
make health

# 4. Проверка данных
make db-stats

# 5. Логи с ошибками
make logs-errors

# 6. Проверка k6
k6 version

# 7. Проверка Python зависимостей
pip list | grep -E "(faker|fastapi|aiochclient)"
```

## Получение помощи

Если проблема не решена:

1. **Соберите информацию:**
   ```bash
   make diagnose > diagnostic.txt
   make logs-errors >> diagnostic.txt
   ```

2. **Проверьте документацию:**
   - [load_tests/README.md](README.md)
   - [load_tests/QUICKSTART.md](QUICKSTART.md)

3. **Создайте issue** с описанием проблемы и diagnostic.txt

---

**Большинство проблем решаются командами:**
```bash
make down && make up && make db-init && make load-test-data-generate
```

