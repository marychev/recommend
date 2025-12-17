# 🔄 Миграция: Партиционирование по `created_at`

## 📋 Что было сделано

### Обновлены схемы таблиц:

1. **Таблица `users`:**
   - ✅ Добавлено партиционирование: `PARTITION BY toYYYYMM(created_at)`
   - ✅ Обновлен ORDER BY: `ORDER BY (user_id, created_at)`

2. **Таблица `tracks`:**
   - ✅ Добавлено партиционирование: `PARTITION BY toYYYYMM(created_at)`
   - ✅ Обновлен ORDER BY: `ORDER BY (track_id, created_at)`

### Обновленные файлы:

- ✅ `app/db/clickhouse_schemas.sql` - основная схема
- ✅ `scripts/safe_db_init.sh` - скрипт инициализации
- ✅ `tests/clickhouse/conftest.py` - тестовые схемы
- ✅ `scripts/migrate_partition_by_created_at.sh` - скрипт миграции

---

## 🚀 Преимущества

### Для батч INSERT:

1. **Группировка записей:**
   - Записи с близкими `created_at` попадают в одну партицию
   - Меньше операций merge в ClickHouse
   - Более эффективное использование дискового пространства

2. **Производительность:**
   - Быстрее запросы по диапазону дат
   - Оптимизация удаления старых данных (drop partition)
   - Улучшение производительности при росте таблиц

3. **ORDER BY оптимизация:**
   - Новые записи группируются вместе
   - Батч INSERT более эффективен

---

## 📝 Миграция существующих таблиц

### Автоматическая миграция:

```bash
# Запуск скрипта миграции
bash scripts/migrate_partition_by_created_at.sh
```

### Что делает скрипт:

1. Создает новые таблицы с партиционированием
2. Копирует данные из старых таблиц
3. Проверяет количество записей
4. Переименовывает таблицы
5. Сохраняет старые таблицы для проверки

### Ручная миграция:

```sql
USE music_recommend;

-- 1. Создать новую таблицу users
CREATE TABLE users_new (
    user_id UInt32,
    username String,
    email String,
    age UInt8,
    country String,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (user_id, created_at)
SETTINGS index_granularity = 8192;

-- 2. Скопировать данные
INSERT INTO users_new SELECT * FROM users;

-- 3. Проверить количество
SELECT 
    (SELECT count() FROM users) as old_count,
    (SELECT count() FROM users_new) as new_count;

-- 4. Переименовать
RENAME TABLE users TO users_old, users_new TO users;

-- 5. Аналогично для tracks
CREATE TABLE tracks_new (
    track_id UInt32,
    title String,
    artist String,
    album String,
    genre String,
    duration_seconds UInt16,
    release_year UInt16,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (track_id, created_at)
SETTINGS index_granularity = 8192;

INSERT INTO tracks_new SELECT * FROM tracks;
RENAME TABLE tracks TO tracks_old, tracks_new TO tracks;

-- 6. После проверки удалить старые таблицы
-- DROP TABLE users_old;
-- DROP TABLE tracks_old;
```

---

## ⚠️ Важные замечания

### Для новых установок:

- ✅ Схемы уже обновлены
- ✅ При создании новых таблиц партиционирование будет применено автоматически
- ✅ Никаких дополнительных действий не требуется

### Для существующих установок:

1. **Перед миграцией:**
   - Сделайте backup базы данных
   - Проверьте, что есть поле `created_at` во всех записях

2. **Во время миграции:**
   - Приложение должно быть остановлено
   - Миграция может занять время для больших таблиц

3. **После миграции:**
   - Проверьте количество записей
   - Проверьте работу приложения
   - Удалите старые таблицы после проверки

---

## 🔍 Проверка миграции

### Проверить структуру таблиц:

```sql
SELECT 
    name,
    partition_key,
    sorting_key
FROM system.tables 
WHERE database = 'music_recommend' 
  AND name IN ('users', 'tracks');
```

### Проверить партиции:

```sql
-- Партиции users
SELECT 
    partition,
    rows,
    formatReadableSize(bytes_on_disk) as size
FROM system.parts 
WHERE database = 'music_recommend' 
  AND table = 'users'
ORDER BY partition DESC;

-- Партиции tracks
SELECT 
    partition,
    rows,
    formatReadableSize(bytes_on_disk) as size
FROM system.parts 
WHERE database = 'music_recommend' 
  AND table = 'tracks'
ORDER BY partition DESC;
```

---

## 📊 Ожидаемые результаты

### Производительность батч INSERT:

- ✅ **До:** Записи могут попадать в разные партиции
- ✅ **После:** Записи с близкими `created_at` попадают в одну партицию
- ✅ **Результат:** Меньше операций merge, быстрее INSERT

### Производительность запросов:

- ✅ **Запросы по диапазону дат:** Быстрее благодаря партиционированию
- ✅ **Удаление старых данных:** Можно удалить целую партицию
- ✅ **Аналитика:** Быстрее запросы по времени создания

---

## 🎯 Итоги

✅ **Реализовано:**
- Партиционирование по `created_at` для `users` и `tracks`
- Обновлен ORDER BY для оптимизации
- Создан скрипт миграции
- Обновлены тестовые схемы

✅ **Готово к использованию:**
- Новые установки: автоматически применяется
- Существующие: можно мигрировать через скрипт

✅ **Преимущества:**
- Улучшение производительности батч INSERT
- Оптимизация запросов по дате
- Эффективное использование дискового пространства

---

**Дата:** 17 декабря 2025  
**Версия:** 1.0

