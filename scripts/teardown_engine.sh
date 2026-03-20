#!/bin/bash
# Удаление Kafka Table Engine таблиц и Materialized Views

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${YELLOW}Удаление Kafka Table Engine таблиц...${NC}"

# Сначала удаляем MV (они зависят от Kafka-таблиц)
docker exec music_recommend_clickhouse clickhouse-client --multiquery -q "
    DROP VIEW IF EXISTS music_recommend.kafka_users_mv;
    DROP VIEW IF EXISTS music_recommend.kafka_tracks_mv;
    DROP VIEW IF EXISTS music_recommend.kafka_events_mv;
"

# Затем удаляем Kafka-таблицы
docker exec music_recommend_clickhouse clickhouse-client --multiquery -q "
    DROP TABLE IF EXISTS music_recommend.kafka_users;
    DROP TABLE IF EXISTS music_recommend.kafka_tracks;
    DROP TABLE IF EXISTS music_recommend.kafka_events;
"

echo -e "${GREEN}Kafka Table Engine таблицы удалены${NC}"
