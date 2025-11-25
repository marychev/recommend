# 📊 Оптимизация ClickHouse индексов для рекомендаций

## 🎯 Цель

Оптимизация запросов рекомендаций через добавление индексов в ClickHouse для ускорения:
- Поиска похожих пользователей (collaborative filtering)
- Получения рекомендаций
- Запросов популярных треков

## 📋 Текущие индексы

### user_track_interactions
- ✅ `idx_track_id` - для фильтрации по track_id
- ✅ `idx_action_type` - для фильтрации по типу действия
- ✅ `idx_timestamp` - для фильтрации по дате (популярные треки)
- ✅ `idx_action_timestamp` - комбинированный индекс для `action_type + timestamp`

### user_track_matrix
- ✅ `idx_implicit_rating` - для фильтрации `WHERE implicit_rating > 0`
- ✅ `idx_track_id` - для JOIN операций по track_id
- ✅ `idx_rating_track` - комбинированный индекс для `(implicit_rating, track_id)`

### user_recommendations
- ✅ `idx_score` - для сортировки рекомендаций по score

## 🔍 Анализ медленных запросов

### 1. Запрос похожих пользователей
```sql
WITH user_tracks AS (
    SELECT track_id, implicit_rating
    FROM user_track_matrix
    WHERE user_id = ? AND implicit_rating > 0  -- ⚠️ Фильтр по implicit_rating
    LIMIT 1000
)
SELECT m2.user_id, ...
FROM user_track_matrix m2
INNER JOIN user_tracks ut ON m2.track_id = ut.track_id  -- ⚠️ JOIN по track_id
WHERE m2.user_id != ? AND m2.implicit_rating > 0  -- ⚠️ Фильтр по implicit_rating
```

**Оптимизация:**
- ✅ Индекс `idx_implicit_rating` ускоряет фильтрацию `WHERE implicit_rating > 0`
- ✅ Индекс `idx_track_id` ускоряет JOIN по track_id
- ✅ Индекс `idx_rating_track` оптимизирует комбинированные запросы

### 2. Запрос рекомендаций
```sql
SELECT ...
FROM user_track_matrix m
INNER JOIN tracks t ON m.track_id = t.track_id
WHERE m.user_id IN (...) AND m.implicit_rating > 0  -- ⚠️ Фильтры
```

**Оптимизация:**
- ✅ Индекс `idx_implicit_rating` ускоряет фильтрацию
- ✅ ORDER BY уже оптимизирован через (user_id, track_id)

### 3. Запрос популярных треков
```sql
SELECT ...
FROM user_track_interactions i
WHERE i.action_type = 'play'  -- ⚠️ Фильтр по action_type
  AND i.timestamp >= now() - INTERVAL 30 DAY  -- ⚠️ Фильтр по timestamp
```

**Оптимизация:**
- ✅ Индекс `idx_action_type` ускоряет фильтрацию по типу действия
- ✅ Индекс `idx_timestamp` ускоряет фильтрацию по дате
- ✅ Индекс `idx_action_timestamp` оптимизирует комбинированные запросы

## 🚀 Применение индексов

### Автоматически (при инициализации БД)
```bash
make db-init
# или
bash scripts/safe_db_init.sh
```

Индексы добавляются автоматически при инициализации БД.

### Вручную
```bash
# Добавить только индексы
bash scripts/safe_add_indexes.sh
```

### Проверка существующих индексов
```bash
# ⚠️ ВАЖНО: Используйте system (не sys!)
docker exec music_recommend_clickhouse clickhouse-client --query "
    SELECT 
        table,
        name as index_name,
        type,
        expr as index_expression,
        granularity
    FROM system.data_skipping_indices
    WHERE database = 'music_recommend'
    ORDER BY table, name
"
```

**Примечание:** Используйте `system` (не `sys`) - это схема системных таблиц в ClickHouse.

## ⚙️ Применение индексов к существующим данным

После добавления индексов рекомендуется оптимизировать таблицы:

```bash
# Оптимизация user_track_matrix
docker exec music_recommend_clickhouse clickhouse-client --query "
    OPTIMIZE TABLE music_recommend.user_track_matrix FINAL
"

# Оптимизация user_track_interactions
docker exec music_recommend_clickhouse clickhouse-client --query "
    OPTIMIZE TABLE music_recommend.user_track_interactions FINAL
"
```

**Примечание:** Оптимизация может занять время в зависимости от объема данных.

## 📈 Ожидаемые результаты

После добавления индексов ожидается:

1. **Поиск похожих пользователей:**
   - До: ~1000-2000ms
   - После: ~200-500ms (ускорение в 4-5 раз)

2. **Получение рекомендаций:**
   - До: ~1500-3000ms
   - После: ~300-800ms (ускорение в 3-5 раз)

3. **Популярные треки:**
   - До: ~500-1000ms
   - После: ~100-300ms (ускорение в 3-5 раз)

## 🔍 Мониторинг производительности

### Проверка использования индексов
```sql
SELECT 
    query,
    query_duration_ms,
    read_rows,
    read_bytes
FROM system.query_log
WHERE type = 'QueryFinish'
  AND query LIKE '%user_track_matrix%'
ORDER BY query_duration_ms DESC
LIMIT 10;
```

### Анализ плана выполнения
```sql
EXPLAIN indexes = 1
SELECT ...
FROM user_track_matrix
WHERE user_id = ? AND implicit_rating > 0;
```

## ⚠️ Важные замечания

1. **Индексы занимают место** - дополнительное место для хранения индексов (обычно 5-10% от размера данных)

2. **Замедление записи** - индексы немного замедляют INSERT операции, но значительно ускоряют SELECT

3. **Применение к существующим данным** - после добавления индексов нужно выполнить `OPTIMIZE TABLE FINAL` для применения к существующим данным

4. **ClickHouse автоматически использует индексы** - не требуется менять запросы, ClickHouse сам решит, когда использовать индекс

## 🛠️ Удаление индексов (если нужно)

```sql
-- Удаление индекса
ALTER TABLE music_recommend.user_track_matrix 
DROP INDEX idx_implicit_rating;
```

## 📚 Дополнительные ресурсы

- [ClickHouse Data Skipping Indexes](https://clickhouse.com/docs/en/engines/table-engines/mergetree-family/mergetree#table_engine-mergetree-data_skipping-indexes)
- [ClickHouse Query Optimization](https://clickhouse.com/docs/en/guides/improving-query-performance/)

