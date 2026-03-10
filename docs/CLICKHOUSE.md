# ClickHouse — оптимизация и настройка

## Оптимизация SQL запросов

### Замена `NOT IN` на `LEFT JOIN`

```sql
-- Было (медленно):
WHERE t.track_id NOT IN (SELECT DISTINCT track_id FROM user_track_interactions WHERE user_id = {user_id})

-- Стало (быстро, ускорение 3-5x):
LEFT JOIN (
    SELECT DISTINCT track_id FROM user_track_interactions PREWHERE user_id = {user_id}
) excluded ON t.track_id = excluded.track_id
WHERE excluded.track_id IS NULL
```

### Использование `PREWHERE`

`PREWHERE` фильтрует данные **до** чтения всех колонок — ускорение 2-3x для больших таблиц.

```sql
-- Вместо WHERE:
PREWHERE user_id = {user_id} AND implicit_rating > 0
```

### Оптимизированные запросы

**Поиск похожих пользователей:**
```sql
WITH user_tracks AS (
    SELECT track_id, implicit_rating
    FROM user_track_matrix
    PREWHERE user_id = {user_id} AND implicit_rating > 0
    LIMIT 1000
)
SELECT m2.user_id, ...
FROM user_track_matrix m2
INNER JOIN user_tracks ut ON m2.track_id = ut.track_id
PREWHERE m2.user_id != {user_id} AND m2.implicit_rating > 0
```

**Популярные треки:**
```sql
SELECT ...
FROM user_track_interactions i
INNER JOIN tracks t ON i.track_id = t.track_id
PREWHERE i.action_type = 'play' AND i.timestamp >= now() - INTERVAL 30 DAY
```

---

## Индексы

### Текущие индексы

**user_track_interactions:**
- `idx_track_id` — фильтрация по track_id
- `idx_action_type` — фильтрация по типу действия
- `idx_timestamp` — фильтрация по дате
- `idx_action_timestamp` — комбинированный (action_type + timestamp)

**user_track_matrix:**
- `idx_implicit_rating` — фильтрация `WHERE implicit_rating > 0`
- `idx_track_id` — JOIN по track_id
- `idx_rating_track` — комбинированный (implicit_rating, track_id)

**user_recommendations:**
- `idx_score` — сортировка по score

### Управление индексами

```bash
# Добавить индексы (идемпотентно)
make db-indexes

# Применить к существующим данным
make db-optimize

# Диагностика производительности
make diagnose-performance
```

### Проверка индексов

```bash
docker exec music_recommend_clickhouse clickhouse-client --query "
    SELECT table, name as index_name, type, expr, granularity
    FROM system.data_skipping_indices
    WHERE database = 'music_recommend'
    ORDER BY table, name
"
```

> **Важно:** Используйте `system` (не `sys`) — это схема системных таблиц в ClickHouse.

### Анализ плана выполнения

```sql
EXPLAIN indexes = 1
SELECT ... FROM user_track_matrix WHERE user_id = ? AND implicit_rating > 0;
```

---

## Партиционирование

### Текущая схема

**user_track_interactions** — уже партиционирована:
```sql
PARTITION BY toYYYYMM(timestamp)
ORDER BY (user_id, timestamp, track_id)
```

**users и tracks** — партиционированы по `created_at`:
```sql
PARTITION BY toYYYYMM(created_at)
ORDER BY (user_id, created_at)  -- или (track_id, created_at)
```

### Преимущества

- Записи с близкими `created_at` попадают в одну партицию
- Меньше операций merge в ClickHouse
- Быстрее запросы по диапазону дат
- Эффективное удаление старых данных (`DROP PARTITION`)

### Миграция (для существующих таблиц)

```bash
bash scripts/migrate_partition_by_created_at.sh
```

### Проверка партиций

```sql
SELECT partition, rows, formatReadableSize(bytes_on_disk) as size
FROM system.parts
WHERE database = 'music_recommend' AND table = 'users'
ORDER BY partition DESC;
```

### Когда партиционирование полезно

- Большие таблицы (> 10M записей)
- Запросы по диапазону дат
- Необходимость удаления старых данных

---

## Настройка для слабых ПК

### Конфигурационные файлы

- `clickhouse-config/users.xml` — настройки пользователей и профилей
- `clickhouse-config/performance.xml` — оптимизация производительности

### Ключевые параметры

```xml
<!-- Память -->
<max_memory_usage>2000000000</max_memory_usage>           <!-- 2GB на запрос -->
<max_bytes_before_external_group_by>1000000000</max_bytes_before_external_group_by>  <!-- Спилл на диск -->

<!-- Потоки -->
<max_threads>4</max_threads>

<!-- Кэш -->
<uncompressed_cache_size>536870912</uncompressed_cache_size>  <!-- 512MB -->
<use_uncompressed_cache>1</use_uncompressed_cache>

<!-- Сжатие -->
<compression><method>lz4</method></compression>
```

### Проверка настроек

```bash
docker exec music_recommend_clickhouse clickhouse-client --query "
SELECT name, value FROM system.settings
WHERE name LIKE '%memory%' OR name LIKE '%thread%'
ORDER BY name
"
```

### Мониторинг ресурсов

```bash
docker stats                          # Статистика контейнеров
make logs-clickhouse                  # Логи ClickHouse
```

### Медленные запросы

```sql
SELECT query, query_duration_ms, read_rows, read_bytes
FROM system.query_log
WHERE type = 'QueryFinish' AND query_duration_ms > 1000
ORDER BY query_duration_ms DESC
LIMIT 10;
```

---

## Best Practices

1. **Батчинг INSERT** — вставляйте данные батчами, не по одной записи
2. **LIMIT** — всегда добавляйте LIMIT в SELECT
3. **Индексы** — на часто используемых полях (minmax, GRANULARITY 4)
4. **Партиционирование** — для больших таблиц: `PARTITION BY toYYYYMM(timestamp)`
5. **Кэширование** — тяжелые запросы кэшировать в Redis

## Troubleshooting

```bash
make fix-clickhouse         # Автоматическое восстановление
make db-reset               # Полный сброс БД
make diagnose-performance   # Диагностика производительности
```

## Связанные документы

- [DB_INIT.md](DB_INIT.md) — Инициализация БД
- [PORTS.md](PORTS.md) — Порты (HTTP 8123, Native 9000)
- [TESTING.md](TESTING.md) — Тестирование
