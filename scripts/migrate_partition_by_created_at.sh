#!/bin/bash
# ============================================================================
# Скрипт миграции: добавление партиционирования по created_at
# для таблиц users и tracks
# ============================================================================

set -e

CONTAINER_NAME="${CLICKHOUSE_CONTAINER:-clickhouse}"
DB_NAME="music_recommend"

echo "🚀 Начало миграции: добавление партиционирования по created_at"
echo "============================================================================"

# Проверяем, что контейнер запущен
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Ошибка: контейнер $CONTAINER_NAME не запущен"
    exit 1
fi

echo "✅ Контейнер $CONTAINER_NAME найден"

echo "📊 Начало миграции таблиц..."

# Выполняем миграцию
docker exec -i "$CONTAINER_NAME" clickhouse-client << EOF
USE $DB_NAME;

-- ============================================================================
-- Миграция таблицы users
-- ============================================================================

-- Создаем новую таблицу с партиционированием
CREATE TABLE IF NOT EXISTS users_new (
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

-- Копируем данные из старой таблицы в новую
INSERT INTO users_new SELECT * FROM users;

-- Проверяем количество записей
SELECT 
    (SELECT count() FROM users) as old_count,
    (SELECT count() FROM users_new) as new_count
FORMAT TabSeparated;

-- Переименовываем таблицы
RENAME TABLE users TO users_old, users_new TO users;

-- ============================================================================
-- Миграция таблицы tracks
-- ============================================================================

-- Создаем новую таблицу с партиционированием
CREATE TABLE IF NOT EXISTS tracks_new (
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

-- Копируем данные из старой таблицы в новую
INSERT INTO tracks_new SELECT * FROM tracks;

-- Проверяем количество записей
SELECT 
    (SELECT count() FROM tracks) as old_count,
    (SELECT count() FROM tracks_new) as new_count
FORMAT TabSeparated;

-- Переименовываем таблицы
RENAME TABLE tracks TO tracks_old, tracks_new TO tracks;

-- ============================================================================
-- Проверка результата
-- ============================================================================

-- Проверяем структуру таблиц
SELECT 
    name,
    partition_key,
    sorting_key
FROM system.tables 
WHERE database = '$DB_NAME' AND name IN ('users', 'tracks')
FORMAT Pretty;

EOF

echo "✅ Миграция SQL завершена!"

echo ""
echo "============================================================================"
echo "✅ Миграция успешно завершена!"
echo ""
echo "⚠️  ВАЖНО: Старые таблицы users_old и tracks_old сохранены для проверки."
echo "   После проверки данных можно удалить их командой:"
echo "   docker exec -i $CONTAINER_NAME clickhouse-client -d $DB_NAME -q 'DROP TABLE users_old; DROP TABLE tracks_old;'"
echo "============================================================================"

