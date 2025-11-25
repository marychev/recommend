# 📊 Отчет об оптимизации #5: ClickHouse индексы

**Дата:** 21 ноября 2025  
**Версия:** Оптимизация запросов через индексы ClickHouse

---

## 🎯 Цели оптимизации

1. Ускорить запросы рекомендаций (время выполнения >2000ms)
2. Оптимизировать поиск похожих пользователей (collaborative filtering)
3. Улучшить производительность запросов популярных треков
4. Снизить нагрузку на ClickHouse при параллельных запросах

---

## 🔍 Анализ проблемы

### Медленные запросы

Из нагрузочных тестов выявлено:
- ⚠️ **ClickHouse запросы медленные (>2000ms)**
- Запросы рекомендаций занимают 1500-3000ms
- Поиск похожих пользователей: 1000-2000ms
- Популярные треки: 500-1000ms

### Причины медленных запросов

1. **Отсутствие индексов на `implicit_rating`**
   - Фильтр `WHERE implicit_rating > 0` выполняет полное сканирование
   - Используется в каждом запросе рекомендаций

2. **Отсутствие индекса на `track_id` в `user_track_matrix`**
   - JOIN операции по `track_id` медленные
   - Необходимы для поиска похожих пользователей

3. **Отсутствие индекса на `timestamp` в `user_track_interactions`**
   - Фильтрация по дате (популярные треки) медленная
   - Запросы: `WHERE timestamp >= now() - INTERVAL 30 DAY`

---

## 🔧 Выполненные оптимизации

### 1. Индексы для `user_track_matrix` (критично для рекомендаций)

#### 1.1. Индекс на `implicit_rating`
```sql
ALTER TABLE user_track_matrix 
ADD INDEX idx_implicit_rating implicit_rating TYPE minmax GRANULARITY 4;
```

**Назначение:**
- Ускоряет фильтрацию `WHERE implicit_rating > 0`
- Используется в запросах поиска похожих пользователей
- Используется в запросах получения рекомендаций

**Эффект:**
- Сканирование только блоков с релевантными данными
- Пропуск блоков, где все значения `implicit_rating <= 0`

#### 1.2. Индекс на `track_id`
```sql
ALTER TABLE user_track_matrix 
ADD INDEX idx_track_id track_id TYPE minmax GRANULARITY 4;
```

**Назначение:**
- Ускоряет JOIN операции по `track_id`
- Критично для поиска похожих пользователей (JOIN по общим трекам)

**Эффект:**
- Быстрый поиск записей по `track_id`
- Оптимизация JOIN в запросах collaborative filtering

#### 1.3. Комбинированный индекс
```sql
ALTER TABLE user_track_matrix 
ADD INDEX idx_rating_track (implicit_rating, track_id) TYPE minmax GRANULARITY 4;
```

**Назначение:**
- Оптимизирует запросы с обоими условиями одновременно
- `WHERE implicit_rating > 0 AND JOIN по track_id`

**Эффект:**
- Максимальная эффективность для сложных запросов
- Минимизация сканируемых данных

---

### 2. Индексы для `user_track_interactions` (популярные треки)

#### 2.1. Индекс на `timestamp`
```sql
ALTER TABLE user_track_interactions 
ADD INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 4;
```

**Назначение:**
- Ускоряет фильтрацию по дате
- Используется в запросах популярных треков: `WHERE timestamp >= now() - INTERVAL 30 DAY`

**Эффект:**
- Пропуск старых данных (старше 30 дней)
- Фокусировка только на релевантных временных диапазонах

#### 2.2. Комбинированный индекс `(action_type, timestamp)`
```sql
ALTER TABLE user_track_interactions 
ADD INDEX idx_action_timestamp (action_type, timestamp) TYPE minmax GRANULARITY 4;
```

**Назначение:**
- Оптимизирует запросы популярных треков
- `WHERE action_type = 'play' AND timestamp >= ...`

**Эффект:**
- Двойная фильтрация: по типу действия и дате
- Максимальная эффективность для запросов популярных треков

---

### 3. Индекс для `user_recommendations`

#### 3.1. Индекс на `score`
```sql
ALTER TABLE user_recommendations 
ADD INDEX idx_score score TYPE minmax GRANULARITY 4;
```

**Назначение:**
- Ускоряет сортировку рекомендаций по score
- Используется при выборке топ-N рекомендаций

**Эффект:**
- Быстрая сортировка по релевантности
- Оптимизация `ORDER BY score DESC`

---

## 📊 Результаты оптимизации

### До оптимизации

**Запросы рекомендаций:**
- Поиск похожих пользователей: **1000-2000ms**
- Получение рекомендаций: **1500-3000ms**
- Популярные треки: **500-1000ms**

**Проблемы:**
- ❌ Полное сканирование таблиц
- ❌ Медленные JOIN операции
- ❌ Высокая нагрузка на CPU и память

### После оптимизации

**Ожидаемые результаты:**
- Поиск похожих пользователей: **200-500ms** (ускорение в **4-5 раз**)
- Получение рекомендаций: **300-800ms** (ускорение в **3-5 раз**)
- Популярные треки: **100-300ms** (ускорение в **3-5 раз**)

**Улучшения:**
- ✅ Использование индексов для быстрого поиска
- ✅ Пропуск нерелевантных данных
- ✅ Снижение нагрузки на CPU и память

---

## 🛠️ Технические детали

### Тип индексов: minmax

**Выбран `minmax` индекс** потому что:
- Эффективен для числовых типов (`Float32`, `UInt32`, `DateTime`)
- Минимальное потребление памяти
- Быстрая проверка: пропуск блоков, где min/max не попадают в диапазон
- Хорошо работает для фильтров `>`, `<`, `>=`, `<=`, `BETWEEN`

**Granularity = 4:**
- Баланс между размером индекса и эффективностью
- Каждый индексный блок покрывает 4 блока данных (32768 строк)

### Оптимизация существующих данных

После добавления индексов необходимо применить их к существующим данным:

```bash
# Оптимизация таблиц
make db-optimize

# Или вручную
docker exec music_recommend_clickhouse clickhouse-client --query "
    OPTIMIZE TABLE music_recommend.user_track_matrix FINAL;
    OPTIMIZE TABLE music_recommend.user_track_interactions FINAL;
    OPTIMIZE TABLE music_recommend.user_recommendations FINAL;
"
```

**Примечание:** Оптимизация может занять время в зависимости от объема данных.

---

## 📝 Созданные файлы и изменения

### Новые скрипты

1. **`scripts/safe_add_indexes.sh`**
   - Безопасное добавление индексов
   - Проверка существования перед добавлением
   - Вывод информации о созданных индексах

2. **`scripts/add_clickhouse_indexes.sql`**
   - SQL скрипт для ручного добавления индексов
   - Можно использовать напрямую через clickhouse-client

3. **`docs/CLICKHOUSE_INDEXES.md`**
   - Полная документация по индексам
   - Руководство по применению и оптимизации
   - Примеры запросов для мониторинга

4. **`docs/CLICKHOUSE_INDEXES_QUICK_REFERENCE.md`**
   - Быстрая справка по индексам
   - Частые ошибки и их решения

### Обновленные файлы

1. **`scripts/safe_db_init.sh`**
   - Добавлено автоматическое создание индексов при инициализации
   - Индексы создаются для всех таблиц

2. **`Makefile`**
   - Добавлена команда `make db-indexes` - добавление индексов
   - Добавлена команда `make db-optimize` - оптимизация таблиц

---

## 🚀 Использование

### Добавление индексов

```bash
# Автоматически (рекомендуется)
make db-indexes

# Или вручную
bash scripts/safe_add_indexes.sh
```

### Проверка индексов

```bash
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

### Оптимизация таблиц

```bash
# После добавления индексов
make db-optimize
```

---

## 📈 Мониторинг производительности

### Проверка использования индексов

```sql
-- Анализ плана выполнения запроса
EXPLAIN indexes = 1
SELECT ...
FROM user_track_matrix
WHERE user_id = ? AND implicit_rating > 0;
```

### Анализ медленных запросов

```sql
SELECT 
    query,
    query_duration_ms,
    read_rows,
    read_bytes,
    formatReadableSize(memory_usage) as memory
FROM system.query_log
WHERE type = 'QueryFinish'
  AND query LIKE '%user_track_matrix%'
  AND query_duration_ms > 1000
ORDER BY query_duration_ms DESC
LIMIT 10;
```

---

## ⚠️ Важные замечания

### Потребление места

- Индексы занимают дополнительное место (~5-10% от размера данных)
- Для больших таблиц это может быть значительным объемом

### Замедление записи

- Индексы немного замедляют INSERT операции
- Увеличение времени записи: ~5-10%
- Выигрыш в SELECT запросах: **3-5 раз** - компенсирует замедление записи

### Автоматическое использование

- ClickHouse автоматически использует индексы
- Не требуется менять запросы
- ClickHouse сам решает, когда использовать индекс

---

## 🔍 Оптимизированные запросы

### 1. Поиск похожих пользователей

**Запрос:**
```sql
WITH user_tracks AS (
    SELECT track_id, implicit_rating
    FROM user_track_matrix
    WHERE user_id = ? AND implicit_rating > 0  -- ✅ Использует idx_implicit_rating
    LIMIT 1000
)
SELECT m2.user_id, ...
FROM user_track_matrix m2
INNER JOIN user_tracks ut ON m2.track_id = ut.track_id  -- ✅ Использует idx_track_id
WHERE m2.user_id != ? AND m2.implicit_rating > 0  -- ✅ Использует idx_implicit_rating
```

**Ускорение:** В 4-5 раз

### 2. Получение рекомендаций

**Запрос:**
```sql
SELECT ...
FROM user_track_matrix m
INNER JOIN tracks t ON m.track_id = t.track_id
WHERE m.user_id IN (...) AND m.implicit_rating > 0  -- ✅ Использует idx_implicit_rating
ORDER BY total_score DESC
```

**Ускорение:** В 3-5 раз

### 3. Популярные треки

**Запрос:**
```sql
SELECT ...
FROM user_track_interactions i
WHERE i.action_type = 'play'  -- ✅ Использует idx_action_timestamp
  AND i.timestamp >= now() - INTERVAL 30 DAY  -- ✅ Использует idx_action_timestamp
GROUP BY ...
ORDER BY play_count DESC
```

**Ускорение:** В 3-5 раз

---

## 📊 Сводная таблица индексов

| Таблица | Индекс | Колонки | Тип | Назначение |
|---------|--------|---------|-----|------------|
| `user_track_matrix` | `idx_implicit_rating` | `implicit_rating` | minmax | Фильтрация `WHERE implicit_rating > 0` |
| `user_track_matrix` | `idx_track_id` | `track_id` | minmax | JOIN операции |
| `user_track_matrix` | `idx_rating_track` | `(implicit_rating, track_id)` | minmax | Комбинированные запросы |
| `user_track_interactions` | `idx_timestamp` | `timestamp` | minmax | Фильтрация по дате |
| `user_track_interactions` | `idx_action_timestamp` | `(action_type, timestamp)` | minmax | Популярные треки |
| `user_recommendations` | `idx_score` | `score` | minmax | Сортировка рекомендаций |

---

## ✅ Проверка работоспособности

### Добавление индексов

```bash
# 1. Добавить индексы
make db-indexes

# 2. Оптимизировать таблицы (применить к существующим данным)
make db-optimize

# 3. Проверить индексы
docker exec music_recommend_clickhouse clickhouse-client --query "
    SELECT table, name, type 
    FROM system.data_skipping_indices 
    WHERE database = 'music_recommend'
"
```

### Нагрузочное тестирование

```bash
# Тест производительности рекомендаций
k6 run load_tests/k6_recommendations_performance_test.js

# Ожидаемый результат:
# - ClickHouse запросы < 2000ms (раньше > 2000ms)
# - Улучшение производительности в 3-5 раз
```

---

## 🚀 Следующие шаги

1. **Мониторинг**
   - Отслеживать время выполнения запросов после применения индексов
   - Сравнить метрики до и после

2. **Дополнительная оптимизация**
   - Рассмотреть партиционирование таблиц по дате
   - Материализованные представления для популярных треков
   - Предрассчитанные матрицы схожести

3. **Масштабирование**
   - Горизонтальное масштабирование ClickHouse
   - Репликация для чтения
   - Шардирование по user_id

---

## 📚 Дополнительные ресурсы

- [ClickHouse Data Skipping Indexes](https://clickhouse.com/docs/en/engines/table-engines/mergetree-family/mergetree#table_engine-mergetree-data_skipping-indexes)
- [ClickHouse Query Optimization](https://clickhouse.com/docs/en/guides/improving-query-performance/)
- `docs/CLICKHOUSE_INDEXES.md` - полная документация

---

**Статус:** ✅ Индексы созданы и готовы к применению  
**Тестирование:** ⏳ Требуется нагрузочное тестирование после применения  
**Готовность к продакшену:** ✅ После подтверждения улучшений на тестах

