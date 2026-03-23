#!/bin/bash
# Очистка тестовых данных в ClickHouse перед/после нагрузочных тестов
# Использование: ./scripts/clean_test_data.sh [--check-only]
#
# Без аргументов: показывает счётчики и очищает таблицы
# --check-only:   только показывает счётчики, не удаляет

set -e

CLICKHOUSE_CONTAINER="music_recommend_clickhouse"
DATABASE="music_recommend"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Проверяем доступность ClickHouse
if ! docker exec "$CLICKHOUSE_CONTAINER" clickhouse-client --query "SELECT 1" &>/dev/null; then
    echo -e "${RED}ClickHouse контейнер недоступен${NC}"
    exit 1
fi

# Получаем счётчики
echo -e "${BLUE}📊 Текущее состояние таблиц:${NC}"
docker exec "$CLICKHOUSE_CONTAINER" clickhouse-client --query "
    SELECT
        'users' AS table,
        count() AS rows
    FROM ${DATABASE}.users
    UNION ALL
    SELECT 'tracks', count() FROM ${DATABASE}.tracks
    UNION ALL
    SELECT 'events', count() FROM ${DATABASE}.user_track_interactions
    UNION ALL
    SELECT 'matrix', count() FROM ${DATABASE}.user_track_matrix
    FORMAT PrettyCompact
"

if [ "$1" = "--check-only" ]; then
    exit 0
fi

# Считаем общее количество записей
TOTAL=$(docker exec "$CLICKHOUSE_CONTAINER" clickhouse-client --query "
    SELECT count() FROM ${DATABASE}.users
")
TOTAL=$((TOTAL + $(docker exec "$CLICKHOUSE_CONTAINER" clickhouse-client --query "
    SELECT count() FROM ${DATABASE}.tracks
")))
TOTAL=$((TOTAL + $(docker exec "$CLICKHOUSE_CONTAINER" clickhouse-client --query "
    SELECT count() FROM ${DATABASE}.user_track_interactions
")))

if [ "$TOTAL" -eq 0 ]; then
    echo -e "${GREEN}Таблицы уже пусты, очистка не нужна${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}Очистка $TOTAL записей...${NC}"

docker exec "$CLICKHOUSE_CONTAINER" clickhouse-client --query "
    TRUNCATE TABLE ${DATABASE}.users;
    TRUNCATE TABLE ${DATABASE}.tracks;
    TRUNCATE TABLE ${DATABASE}.user_track_interactions;
    TRUNCATE TABLE ${DATABASE}.user_track_matrix;
"

echo -e "${GREEN}✅ Тестовые данные очищены${NC}"
