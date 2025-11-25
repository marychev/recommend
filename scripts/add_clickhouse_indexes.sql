-- ============================================================================
-- Скрипт для добавления индексов в ClickHouse для оптимизации запросов
-- Использование: clickhouse-client < scripts/add_clickhouse_indexes.sql
-- ============================================================================

USE music_recommend;

-- ============================================================================
-- 1. Индексы для user_track_matrix (критически важно для рекомендаций)
-- ============================================================================

-- Индекс на implicit_rating для ускорения фильтрации WHERE implicit_rating > 0
-- Это один из самых частых фильтров в запросах рекомендаций
ALTER TABLE user_track_matrix 
ADD INDEX IF NOT EXISTS idx_implicit_rating implicit_rating TYPE minmax GRANULARITY 4;

-- Индекс на track_id для ускорения JOIN операций
-- Используется при поиске похожих пользователей (JOIN по track_id)
ALTER TABLE user_track_matrix 
ADD INDEX IF NOT EXISTS idx_track_id track_id TYPE minmax GRANULARITY 4;

-- Комбинированный индекс на (implicit_rating, track_id) для оптимизации
-- запросов, где одновременно фильтруются по rating и делается JOIN
ALTER TABLE user_track_matrix 
ADD INDEX IF NOT EXISTS idx_rating_track (implicit_rating, track_id) TYPE minmax GRANULARITY 4;

-- ============================================================================
-- 2. Оптимизация ORDER BY для user_track_matrix
-- Текущий ORDER BY (user_id, track_id) хорош, но можно улучшить
-- для запросов, которые часто сортируют по implicit_rating
-- ============================================================================

-- Примечание: ORDER BY нельзя изменить без пересоздания таблицы,
-- но мы добавили индексы выше, которые помогут

-- ============================================================================
-- 3. Индексы для user_track_interactions (для популярных треков)
-- ============================================================================

-- Индекс на timestamp для ускорения фильтрации по дате
-- Используется в запросах популярных треков (WHERE timestamp >= now() - INTERVAL 30 DAY)
-- ORDER BY уже содержит timestamp, но дополнительный индекс поможет
ALTER TABLE user_track_interactions 
ADD INDEX IF NOT EXISTS idx_timestamp timestamp TYPE minmax GRANULARITY 4;

-- Комбинированный индекс для популярных треков
-- Оптимизирует запросы: WHERE action_type = 'play' AND timestamp >= ...
-- ORDER BY уже содержит (user_id, timestamp, track_id), но этот индекс поможет
ALTER TABLE user_track_interactions 
ADD INDEX IF NOT EXISTS idx_action_timestamp (action_type, timestamp) TYPE minmax GRANULARITY 4;

-- ============================================================================
-- 4. Индексы для user_recommendations (если используется)
-- ============================================================================

-- Индекс на score для быстрой сортировки рекомендаций
ALTER TABLE user_recommendations 
ADD INDEX IF NOT EXISTS idx_score score TYPE minmax GRANULARITY 4;

-- ============================================================================
-- Проверка индексов
-- ============================================================================

-- Выводим информацию о созданных индексах
SELECT 
    table,
    name as index_name,
    type,
    expr as index_expression,
    granularity
FROM system.data_skipping_indices
WHERE database = 'music_recommend'
ORDER BY table, name;

