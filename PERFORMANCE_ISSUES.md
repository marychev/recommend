# 🐌 Проблемы производительности POST /recommendations

## ❌ Критическая проблема

**POST /recommendations: p95 = 19039ms (19 секунд!)**

Это недопустимо медленно для production.

## 🔍 Анализ проблемы

### Что происходит в эндпоинте:

1. **Проверка кэша Redis** ✅ (быстро, ~10ms)
2. **Поиск похожих пользователей** ❌ (медленно)
   ```sql
   -- Сложный JOIN с GROUP BY и HAVING
   SELECT m2.user_id, sum(...) as similarity
   FROM user_track_matrix m1
   INNER JOIN user_track_matrix m2 ON ...
   WHERE m2.user_id != {user_id}
   GROUP BY m2.user_id
   HAVING similarity > 0.1
   ORDER BY similarity DESC
   LIMIT 50
   ```

3. **Поиск рекомендаций** ❌ (очень медленно)
   ```sql
   -- JOIN с tracks + подзапрос NOT IN
   SELECT ... sum(m.implicit_rating) as total_score
   FROM user_track_matrix m
   INNER JOIN tracks t ON m.track_id = t.track_id
   WHERE m.user_id IN ({similar_user_ids})
     AND m.implicit_rating > 0
     AND t.track_id NOT IN (
       SELECT DISTINCT track_id
       FROM user_track_interactions
       WHERE user_id = {user_id}
     )
   GROUP BY ...
   ORDER BY total_score DESC
   LIMIT 10
   ```

## 🎯 Узкие места

### 1. Таблица `user_track_matrix`
- **Проблема:** Нет индексов для быстрого поиска по `user_id` и `track_id`
- **Текущий ORDER BY:** `(user_id, track_id)` - это хорошо, но может быть недостаточно

### 2. Сложные JOIN операции
- **Проблема:** JOIN между двумя большими таблицами (`user_track_matrix` и `tracks`)
- **Решение:** Использовать индексы или материализованные представления

### 3. Подзапрос `NOT IN`
- **Проблема:** `NOT IN (SELECT ...)` может быть очень медленным
- **Решение:** Использовать `LEFT JOIN ... WHERE ... IS NULL` или кэшировать прослушанные треки

### 4. Настройки памяти
- **Проблема:** Запросы используют много памяти (2GB на запрос)
- **Решение:** Оптимизировать запросы, чтобы использовать меньше памяти

## ✅ Рекомендации по оптимизации

### 1. Добавить индексы (КРИТИЧНО!)

```sql
-- Индекс для быстрого поиска по user_id
ALTER TABLE user_track_matrix 
ADD INDEX idx_user_id user_id TYPE minmax GRANULARITY 4;

-- Индекс для быстрого поиска по track_id
ALTER TABLE user_track_matrix 
ADD INDEX idx_track_id track_id TYPE minmax GRANULARITY 4;

-- Индекс для фильтрации по implicit_rating
ALTER TABLE user_track_matrix 
ADD INDEX idx_rating implicit_rating TYPE minmax GRANULARITY 4;
```

### 2. Оптимизировать подзапрос `NOT IN`

**Было:**
```sql
AND t.track_id NOT IN (
    SELECT DISTINCT track_id
    FROM user_track_interactions
    WHERE user_id = {user_id}
)
```

**Стало (использовать LEFT JOIN):**
```sql
LEFT JOIN (
    SELECT DISTINCT track_id
    FROM user_track_interactions
    WHERE user_id = {user_id}
) excluded ON t.track_id = excluded.track_id
WHERE excluded.track_id IS NULL
```

### 3. Кэшировать прослушанные треки

Вместо запроса к БД каждый раз, кэшировать список прослушанных треков в Redis:
```python
# Кэш на 1 час
cached_listened = await redis.get(f"user:{user_id}:listened_tracks")
if not cached_listened:
    # Запрос к БД только если нет в кэше
    listened = await get_listened_tracks(user_id)
    await redis.setex(f"user:{user_id}:listened_tracks", 3600, json.dumps(listened))
```

### 4. Упростить запрос похожих пользователей

Использовать более простой алгоритм или предрассчитывать похожесть:
- Создать таблицу `user_similarity` с предрассчитанными значениями
- Обновлять её периодически (например, раз в час)

### 5. Использовать материализованные представления

Создать материализованное представление для популярных рекомендаций:
```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS popular_recommendations_mv
ENGINE = SummingMergeTree()
ORDER BY (track_id, date)
AS SELECT
    track_id,
    toDate(timestamp) as date,
    sum(implicit_rating) as total_score
FROM user_track_matrix
GROUP BY track_id, date;
```

## 🚀 Быстрые исправления (можно сделать сейчас)

### 1. Запустить диагностику:
```bash
make diagnose-performance
```

### 2. Проверить индексы:
```bash
docker exec music_recommend_clickhouse clickhouse-client -q "
    SELECT name, type 
    FROM system.data_skipping_indices 
    WHERE database = 'music_recommend' 
    AND table = 'user_track_matrix'
"
```

### 3. Проверить размер таблицы:
```bash
docker exec music_recommend_clickhouse clickhouse-client -q "
    SELECT 
        formatReadableSize(sum(bytes)) as size,
        sum(rows) as rows
    FROM system.parts 
    WHERE database = 'music_recommend' 
    AND table = 'user_track_matrix' 
    AND active
"
```

### 4. Проверить медленные запросы:
```bash
docker exec music_recommend_clickhouse clickhouse-client -q "
    SELECT 
        query,
        query_duration_ms,
        read_rows
    FROM system.query_log 
    WHERE type = 'QueryFinish' 
    AND query_duration_ms > 1000
    ORDER BY query_duration_ms DESC 
    LIMIT 5
"
```

## 📊 Ожидаемые улучшения

После оптимизаций:
- **Текущий p95:** 19039ms
- **Целевой p95:** < 1000ms (19x улучшение)
- **Целевой средний:** < 500ms

## ⚠️ Важно

1. **Кэш работает** - 60% запросов идут из кэша (быстро)
2. **Проблема в холодных запросах** - когда кэша нет, запросы очень медленные
3. **Нужно оптимизировать запросы к ClickHouse** - это основное узкое место

---

**Следующий шаг:** Запустите `make diagnose-performance` для детального анализа.

