# 🔧 Troubleshooting: Ошибка рекомендаций (Code: 241)

## ❌ Проблема

```
❌ Recommendations ERROR: 500 - {"detail":"Ошибка при генерации рекомендаций: Query execution failed: Code: 241. DB::Exception...
```

---

## 🔍 Что означает Code: 241

**ClickHouse Error Code 241** обычно означает одно из:
- `MEMORY_LIMIT_EXCEEDED` - превышен лимит памяти для запроса
- `TOO_MANY_ROWS` - слишком много строк в результате
- `TOO_MANY_COLUMNS` - слишком много столбцов

**Чаще всего:** Проблема с памятью при выполнении сложных запросов (collaborative filtering для рекомендаций)

---

## 🚨 Быстрая диагностика

### Шаг 1: Проверьте логи API

```bash
# Полный текст ошибки
docker-compose logs api | grep "Code: 241" -A 10

# Последние ошибки
docker-compose logs api --tail=50 | grep ERROR
```

### Шаг 2: Проверьте ClickHouse

```bash
# Проверьте использование памяти
docker stats music_recommend_clickhouse

# Проверьте настройки памяти
docker exec music_recommend_clickhouse clickhouse-client --query \
  "SELECT name, value FROM system.settings WHERE name LIKE '%memory%'"

# Проверьте текущие запросы
docker exec music_recommend_clickhouse clickhouse-client --query \
  "SELECT query, elapsed, memory_usage FROM system.processes"
```

### Шаг 3: Проверьте данные

```bash
# Количество данных
make db-stats

# Количество взаимодействий (могут быть слишком большими)
docker exec music_recommend_clickhouse clickhouse-client --query \
  "SELECT count() FROM music_recommend.user_track_interactions"
```

---

## 🛠️ Решения

### Решение 1: Увеличьте лимит памяти ClickHouse

**docker-compose.yml:**

```yaml
clickhouse:
  image: clickhouse/clickhouse-server:23.8-alpine
  environment:
    CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: 1
  ulimits:
    nofile:
      soft: 262144
      hard: 262144
  # Добавьте настройки памяти
  command: >
    /bin/bash -c "
    echo '<yandex>
      <max_memory_usage>4000000000</max_memory_usage>
      <max_memory_usage_for_all_queries>8000000000</max_memory_usage_for_all_queries>
      <max_bytes_before_external_group_by>2000000000</max_bytes_before_external_group_by>
      <max_bytes_before_external_sort>2000000000</max_bytes_before_external_sort>
    </yandex>' > /etc/clickhouse-server/config.d/memory.xml
    && /entrypoint.sh
    "
```

Или через отдельный конфиг файл:

**clickhouse/config.d/memory.xml:**
```xml
<yandex>
    <!-- 4GB на запрос -->
    <max_memory_usage>4000000000</max_memory_usage>
    
    <!-- 8GB для всех запросов -->
    <max_memory_usage_for_all_queries>8000000000</max_memory_usage_for_all_queries>
    
    <!-- Использовать диск при превышении памяти -->
    <max_bytes_before_external_group_by>2000000000</max_bytes_before_external_group_by>
    <max_bytes_before_external_sort>2000000000</max_bytes_before_external_sort>
</yandex>
```

**Перезапустите:**
```bash
make restart
```

---

### Решение 2: Оптимизируйте запрос рекомендаций

Найдите файл с логикой рекомендаций и оптимизируйте:

```python
# app/routers/recommendations.py или app/services/recommendations.py

# Плохо: Загружает все данные в память
query = "SELECT * FROM user_track_interactions"

# Хорошо: Ограничиваем выборку
query = """
SELECT user_id, track_id, interaction_type, interaction_value
FROM user_track_interactions
WHERE user_id IN (
    SELECT user_id 
    FROM user_track_interactions 
    WHERE track_id IN (
        SELECT track_id 
        FROM user_track_interactions 
        WHERE user_id = {user_id}
    )
    LIMIT 1000  -- Ограничиваем похожих пользователей
)
LIMIT 10000  -- Ограничиваем общее количество
"""
```

---

### Решение 3: Добавьте LIMIT в запросы

Проверьте все запросы к ClickHouse в коде:

```bash
# Найдите файлы с запросами
grep -r "FROM user_track_interactions" app/ --include="*.py"

# Проверьте, есть ли LIMIT
```

**Добавьте лимиты:**
```python
# До
query = f"SELECT * FROM user_track_interactions WHERE user_id = {user_id}"

# После
query = f"SELECT * FROM user_track_interactions WHERE user_id = {user_id} LIMIT 10000"
```

---

### Решение 4: Используйте сэмплирование

Для рекомендаций не нужны ВСЕ данные:

```python
# Используйте сэмплирование (10% данных)
query = """
SELECT user_id, track_id, interaction_value
FROM user_track_interactions SAMPLE 0.1
WHERE user_id IN (...)
LIMIT 5000
"""
```

---

### Решение 5: Увеличьте ресурсы Docker

**Docker Desktop Settings:**
1. Откройте Docker Desktop
2. Settings → Resources
3. Увеличьте:
   - **Memory:** минимум 8GB (рекомендуется 12-16GB)
   - **CPUs:** минимум 4 cores
   - **Swap:** 2GB
   - **Disk:** 50GB

**Перезапустите Docker Desktop**

---

### Решение 6: Кэшируйте результаты агрессивнее

**app/services/cache.py или app/routers/recommendations.py:**

```python
from app.services.cache import get_cached_recommendations, set_cached_recommendations

# Увеличьте TTL кэша
RECOMMENDATIONS_CACHE_TTL = 3600 * 24  # 24 часа вместо 1 часа

def get_recommendations(user_id: int):
    # Проверка кэша
    cached = get_cached_recommendations(user_id)
    if cached:
        return cached
    
    # Вычисление (тяжелое)
    recommendations = calculate_recommendations(user_id)
    
    # Сохранение в кэш на 24 часа
    set_cached_recommendations(user_id, recommendations, ttl=86400)
    
    return recommendations
```

---

### Решение 7: Упростите алгоритм

Если проблема не решается, используйте более простой алгоритм:

```python
# Вместо collaborative filtering используйте item-based
def get_simple_recommendations(user_id: int, limit: int = 10):
    """
    Простые рекомендации на основе популярности треков
    в жанрах, которые слушает пользователь
    """
    query = """
    SELECT t.track_id, t.title, COUNT(*) as popularity
    FROM user_track_interactions uti
    JOIN tracks t ON uti.track_id = t.track_id
    WHERE t.genre_id IN (
        SELECT DISTINCT t2.genre_id
        FROM user_track_interactions uti2
        JOIN tracks t2 ON uti2.track_id = t2.track_id
        WHERE uti2.user_id = {user_id}
    )
    AND uti.user_id != {user_id}
    GROUP BY t.track_id, t.title
    ORDER BY popularity DESC
    LIMIT {limit}
    """
    return execute_query(query)
```

---

## 🔍 Диагностические команды

### Проверка текущей ситуации

```bash
# 1. Статус контейнеров
docker ps | grep music_recommend

# 2. Использование ресурсов
docker stats --no-stream music_recommend_clickhouse

# 3. Логи ClickHouse
docker-compose logs clickhouse --tail=100 | grep -i "memory\|exception\|error"

# 4. Проверка подключения
docker exec music_recommend_clickhouse clickhouse-client --query "SELECT 1"

# 5. Количество данных
docker exec music_recommend_clickhouse clickhouse-client --query \
  "SELECT table, formatReadableSize(sum(bytes)) as size 
   FROM system.parts 
   WHERE database = 'music_recommend' 
   GROUP BY table"
```

### Проверка конкретного пользователя

```bash
# Проверьте рекомендации через curl
curl -v http://localhost:8000/api/v1/recommendations/1

# Проверьте, есть ли данные для пользователя
docker exec music_recommend_clickhouse clickhouse-client --query \
  "SELECT count() FROM music_recommend.user_track_interactions WHERE user_id = 1"
```

---

## 📊 Мониторинг

### Создайте скрипт мониторинга

**scripts/monitor_clickhouse.sh:**
```bash
#!/bin/bash

echo "🔍 ClickHouse Monitoring"
echo "======================="
echo ""

echo "📊 Memory Usage:"
docker exec music_recommend_clickhouse clickhouse-client --query \
  "SELECT formatReadableSize(memory_usage) as memory 
   FROM system.processes"
echo ""

echo "⚡ Current Queries:"
docker exec music_recommend_clickhouse clickhouse-client --query \
  "SELECT query_id, query, elapsed, formatReadableSize(memory_usage) as memory 
   FROM system.processes 
   FORMAT Pretty"
echo ""

echo "📈 Table Sizes:"
docker exec music_recommend_clickhouse clickhouse-client --query \
  "SELECT table, formatReadableSize(sum(bytes)) as size, count() as parts
   FROM system.parts 
   WHERE database = 'music_recommend' 
   GROUP BY table 
   FORMAT Pretty"
```

```bash
chmod +x scripts/monitor_clickhouse.sh
./scripts/monitor_clickhouse.sh
```

---

## ✅ Проверка после исправления

```bash
# 1. Перезапустите систему
make restart

# 2. Подождите запуска
sleep 30

# 3. Запустите диагностику
make load-test-diagnostics

# 4. Проверьте рекомендации вручную
curl http://localhost:8000/api/v1/recommendations/1
curl http://localhost:8000/api/v1/recommendations/100
curl http://localhost:8000/api/v1/recommendations/1000

# 5. Запустите smoke test
make load-test-smoke
```

---

## 🎯 Рекомендуемый план действий

### План A: Быстрое решение (10 минут)

```bash
# 1. Увеличьте память Docker (в настройках Docker Desktop)
#    Memory: 8GB → 12-16GB

# 2. Перезапустите
make restart

# 3. Проверьте
make load-test-diagnostics
```

### План B: Если Plan A не помог (30 минут)

1. Добавьте конфиг памяти для ClickHouse (см. Решение 1)
2. Оптимизируйте запросы (добавьте LIMIT)
3. Увеличьте TTL кэша
4. Перезапустите и протестируйте

### План C: Долгосрочное решение (2-3 часа)

1. Оптимизируйте алгоритм рекомендаций
2. Добавьте сэмплирование данных
3. Добавьте мониторинг ClickHouse
4. Настройте алерты на превышение памяти

---

## 📚 Дополнительные ресурсы

- [ClickHouse Memory Settings](https://clickhouse.com/docs/en/operations/settings/memory)
- [ClickHouse Performance](https://clickhouse.com/docs/en/operations/performance)
- [Troubleshooting ClickHouse](https://clickhouse.com/docs/en/operations/troubleshooting)

---

## 💡 Превентивные меры

### Добавьте мониторинг

```python
# app/middleware/monitoring.py
import time
from fastapi import Request

@app.middleware("http")
async def log_slow_queries(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    if duration > 5:  # Медленнее 5 секунд
        logger.warning(f"Slow request: {request.url} took {duration:.2f}s")
    
    return response
```

### Добавьте лимиты в код

```python
# app/config.py
MAX_RECOMMENDATIONS_LIMIT = 100
MAX_QUERY_MEMORY = 4_000_000_000  # 4GB
RECOMMENDATIONS_CACHE_TTL = 3600  # 1 час
```

---

**Создано:** 2025-11-10  
**Для:** Music Recommendation System  
**Ошибка:** ClickHouse Code 241 - Memory Limit Exceeded

