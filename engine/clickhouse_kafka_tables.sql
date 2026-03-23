-- Kafka Table Engine: ClickHouse читает напрямую из Kafka
-- Используется как альтернатива Python consumer для бенчмарка
--
-- Архитектура:
--   Kafka Topic → Kafka Engine Table (буфер) → Materialized View → Основная MergeTree таблица
--
-- Consumer group: clickhouse_engine (не конфликтует с Python consumer recommend_consumer_*)

USE music_recommend;

-- ==================== Users ====================

CREATE TABLE IF NOT EXISTS kafka_users (
    user_id UInt32,
    username String,
    email String,
    age UInt8,
    country String,
    created_at String
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:29092',
    kafka_topic_list = 'users',
    kafka_group_name = 'clickhouse_engine',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 1,
    kafka_max_block_size = 1000;

CREATE MATERIALIZED VIEW IF NOT EXISTS kafka_users_mv TO users AS
SELECT
    user_id,
    username,
    email,
    age,
    country,
    parseDateTime(created_at, '%Y-%m-%d %H:%M:%S') AS created_at
FROM kafka_users;

-- ==================== Tracks ====================

CREATE TABLE IF NOT EXISTS kafka_tracks (
    track_id UInt32,
    title String,
    artist String,
    album String,
    genre String,
    duration_seconds UInt16,
    release_year UInt16,
    created_at String
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:29092',
    kafka_topic_list = 'tracks',
    kafka_group_name = 'clickhouse_engine',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 1,
    kafka_max_block_size = 1000;

CREATE MATERIALIZED VIEW IF NOT EXISTS kafka_tracks_mv TO tracks AS
SELECT
    track_id,
    title,
    artist,
    album,
    genre,
    duration_seconds,
    release_year,
    parseDateTime(created_at, '%Y-%m-%d %H:%M:%S') AS created_at
FROM kafka_tracks;

-- ==================== Events (user_track_interactions) ====================

CREATE TABLE IF NOT EXISTS kafka_events (
    user_id UInt32,
    track_id UInt32,
    action_type String,
    listen_duration_seconds Nullable(UInt16),
    timestamp String
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:29092',
    kafka_topic_list = 'user_track_events',
    kafka_group_name = 'clickhouse_engine',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 1,
    kafka_max_block_size = 1000;

CREATE MATERIALIZED VIEW IF NOT EXISTS kafka_events_mv TO user_track_interactions AS
SELECT
    user_id,
    track_id,
    action_type,
    listen_duration_seconds,
    parseDateTime(timestamp, '%Y-%m-%d %H:%M:%S') AS timestamp
FROM kafka_events;
