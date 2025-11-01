-- Схемы таблиц для ClickHouse

-- Создание базы данных
CREATE DATABASE IF NOT EXISTS music_recommend;

USE music_recommend;

-- ==================== Таблица пользователей ====================
CREATE TABLE IF NOT EXISTS users (
    user_id UInt32,
    username String,
    email String,
    age UInt8,
    country String,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY user_id
SETTINGS index_granularity = 8192;

-- ==================== Таблица треков ====================
CREATE TABLE IF NOT EXISTS tracks (
    track_id UInt32,
    title String,
    artist String,
    album String,
    genre String,
    duration_seconds UInt16,
    release_year UInt16,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY track_id
SETTINGS index_granularity = 8192;

-- ==================== Таблица взаимодействий пользователей с треками ====================
-- Оптимизирована для OLAP-запросов и аналитики
CREATE TABLE IF NOT EXISTS user_track_interactions (
    user_id UInt32,
    track_id UInt32,
    action_type Enum8(
        'play' = 1, 
        'like' = 2, 
        'dislike' = 3, 
        'skip' = 4, 
        'add_to_playlist' = 5, 
        'share' = 6
    ),
    listen_duration_seconds Nullable(UInt16),
    timestamp DateTime,
    date Date MATERIALIZED toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (user_id, timestamp, track_id)
SETTINGS index_granularity = 8192;

-- Индексы для оптимизации запросов
ALTER TABLE user_track_interactions 
ADD INDEX idx_track_id track_id TYPE minmax GRANULARITY 4;

ALTER TABLE user_track_interactions 
ADD INDEX idx_action_type action_type TYPE set(0) GRANULARITY 4;

-- ==================== Материализованное представление для статистики треков ====================
CREATE MATERIALIZED VIEW IF NOT EXISTS track_statistics_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (track_id, date)
AS SELECT
    track_id,
    toDate(timestamp) as date,
    count() as total_plays,
    uniq(user_id) as unique_listeners,
    countIf(action_type = 'like') as total_likes,
    countIf(action_type = 'dislike') as total_dislikes,
    avg(listen_duration_seconds) as avg_listen_duration
FROM user_track_interactions
GROUP BY track_id, date;

-- ==================== Материализованное представление для статистики пользователей ====================
CREATE MATERIALIZED VIEW IF NOT EXISTS user_statistics_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (user_id, date)
AS SELECT
    user_id,
    toDate(timestamp) as date,
    count() as total_interactions,
    uniq(track_id) as unique_tracks,
    countIf(action_type = 'play') as total_plays,
    countIf(action_type = 'like') as total_likes,
    sum(listen_duration_seconds) as total_listen_time_seconds
FROM user_track_interactions
GROUP BY user_id, date;

-- ==================== Таблица для хранения предрассчитанных рекомендаций ====================
-- Используется для быстрой отдачи рекомендаций без пересчета
CREATE TABLE IF NOT EXISTS user_recommendations (
    user_id UInt32,
    track_id UInt32,
    score Float32,
    algorithm String,
    generated_at DateTime,
    date Date MATERIALIZED toDate(generated_at)
) ENGINE = ReplacingMergeTree(generated_at)
PARTITION BY toYYYYMM(generated_at)
ORDER BY (user_id, score, track_id)
SETTINGS index_granularity = 8192;

-- ==================== Таблица для user-item матрицы (для collaborative filtering) ====================
CREATE TABLE IF NOT EXISTS user_track_matrix (
    user_id UInt32,
    track_id UInt32,
    implicit_rating Float32, -- неявный рейтинг на основе взаимодействий
    last_interaction DateTime,
    interaction_count UInt16
) ENGINE = ReplacingMergeTree(last_interaction)
ORDER BY (user_id, track_id)
SETTINGS index_granularity = 8192;

-- Материализованное представление для автоматического обновления матрицы
CREATE MATERIALIZED VIEW IF NOT EXISTS user_track_matrix_mv
TO user_track_matrix
AS SELECT
    user_id,
    track_id,
    -- Расчет неявного рейтинга на основе действий
    sum(
        multiIf(
            action_type = 'play', 1.0,
            action_type = 'like', 3.0,
            action_type = 'dislike', -3.0,
            action_type = 'skip', -0.5,
            action_type = 'add_to_playlist', 2.0,
            action_type = 'share', 2.5,
            0
        )
    ) as implicit_rating,
    max(timestamp) as last_interaction,
    count() as interaction_count
FROM user_track_interactions
GROUP BY user_id, track_id;

-- ==================== Вспомогательные запросы для анализа ====================

-- Представление для получения популярных треков
CREATE VIEW IF NOT EXISTS popular_tracks AS
SELECT 
    t.track_id,
    t.title,
    t.artist,
    t.genre,
    count(*) as play_count,
    uniq(i.user_id) as unique_listeners,
    avg(i.listen_duration_seconds) as avg_listen_duration
FROM user_track_interactions i
JOIN tracks t ON i.track_id = t.track_id
WHERE i.action_type = 'play'
  AND i.timestamp >= now() - INTERVAL 30 DAY
GROUP BY t.track_id, t.title, t.artist, t.genre
ORDER BY play_count DESC;

-- Представление для получения похожих пользователей (на основе общих треков)
CREATE VIEW IF NOT EXISTS similar_users AS
SELECT 
    a.user_id as user_id_1,
    b.user_id as user_id_2,
    count(*) as common_tracks,
    sum(a.implicit_rating * b.implicit_rating) as similarity_score
FROM user_track_matrix a
JOIN user_track_matrix b ON a.track_id = b.track_id
WHERE a.user_id < b.user_id
  AND a.implicit_rating > 0
  AND b.implicit_rating > 0
GROUP BY a.user_id, b.user_id
HAVING common_tracks >= 5
ORDER BY similarity_score DESC;

