#!/bin/bash
# Создание Kafka Table Engine таблиц и Materialized Views в ClickHouse

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Настройка Kafka Table Engine в ClickHouse${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

# Ожидание готовности ClickHouse
echo -e "${YELLOW}Ожидание готовности ClickHouse...${NC}"
MAX_WAIT=60
WAITED=0
while ! docker exec music_recommend_clickhouse clickhouse-client -q "SELECT 1" > /dev/null 2>&1; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo -e "${RED}ClickHouse не запустился за ${MAX_WAIT} секунд${NC}"
        exit 1
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done
echo -e "${GREEN}ClickHouse готов!${NC}"

# Выполнение SQL
echo -e "${YELLOW}Создание Kafka Engine таблиц и Materialized Views...${NC}"
docker exec -i music_recommend_clickhouse clickhouse-client --multiquery < engine/clickhouse_kafka_tables.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Kafka Table Engine настроен!${NC}"
else
    echo -e "${RED}Ошибка при создании таблиц${NC}"
    exit 1
fi

# Проверка
echo ""
echo -e "${YELLOW}Созданные таблицы:${NC}"
docker exec music_recommend_clickhouse clickhouse-client -q \
    "SELECT name, engine FROM system.tables WHERE database = 'music_recommend' AND name LIKE 'kafka_%' FORMAT Pretty"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Kafka Table Engine готов к работе!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${YELLOW}ClickHouse читает напрямую из Kafka (consumer group: clickhouse_engine)${NC}"
echo ""
