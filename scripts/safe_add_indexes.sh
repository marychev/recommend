#!/bin/bash
# ============================================================================
# Безопасное добавление индексов в ClickHouse
# Проверяет существование индексов перед добавлением
# ============================================================================

set -e

CLICKHOUSE_HOST="${CLICKHOUSE_HOST:-localhost}"
CLICKHOUSE_PORT="${CLICKHOUSE_PORT:-9000}"

echo "🔍 Проверка подключения к ClickHouse..."
if ! docker exec music_recommend_clickhouse clickhouse-client --host localhost --query "SELECT 1" > /dev/null 2>&1; then
    echo "❌ Ошибка: ClickHouse недоступен"
    echo "💡 Убедитесь, что контейнер запущен: docker-compose ps"
    exit 1
fi

echo "✅ ClickHouse доступен"
echo ""

echo "📊 Добавление индексов для оптимизации запросов..."
echo ""

# Функция для проверки существования индекса
check_index_exists() {
    local table=$1
    local index_name=$2
    local result=$(docker exec music_recommend_clickhouse clickhouse-client --host localhost --query "
        SELECT count() > 0
        FROM system.data_skipping_indices
        WHERE database = 'music_recommend' 
          AND table = '$table' 
          AND name = '$index_name'
    " 2>/dev/null || echo "0")
    [ "$result" = "1" ]
}

# Функция для безопасного добавления индекса
add_index_safe() {
    local table=$1
    local index_name=$2
    local index_expr=$3
    local index_type=$4
    local granularity=${5:-4}
    
    if check_index_exists "$table" "$index_name"; then
        echo "  ⏭️  Индекс $table.$index_name уже существует, пропускаем"
        return 0
    fi
    
    echo "  ➕ Добавляем индекс $table.$index_name..."
    docker exec music_recommend_clickhouse clickhouse-client --host localhost --query "
        ALTER TABLE music_recommend.$table 
        ADD INDEX ${index_name} $index_expr TYPE $index_type GRANULARITY $granularity
    " 2>&1
    
    if [ $? -eq 0 ]; then
        echo "    ✅ Индекс $table.$index_name добавлен"
    else
        echo "    ❌ Ошибка при добавлении индекса $table.$index_name"
        return 1
    fi
}

echo "🔧 1. Индексы для user_track_matrix:"
add_index_safe "user_track_matrix" "idx_implicit_rating" "implicit_rating" "minmax" "4"
add_index_safe "user_track_matrix" "idx_track_id" "track_id" "minmax" "4"
add_index_safe "user_track_matrix" "idx_rating_track" "(implicit_rating, track_id)" "minmax" "4"

echo ""
echo "🔧 2. Индексы для user_track_interactions:"
add_index_safe "user_track_interactions" "idx_timestamp" "timestamp" "minmax" "4"
add_index_safe "user_track_interactions" "idx_action_timestamp" "(action_type, timestamp)" "minmax" "4"

echo ""
echo "🔧 3. Индексы для user_recommendations:"
add_index_safe "user_recommendations" "idx_score" "score" "minmax" "4"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "📊 ИНФОРМАЦИЯ О ВСЕХ ИНДЕКСАХ:"
echo "════════════════════════════════════════════════════════════"
if docker exec music_recommend_clickhouse clickhouse-client --host localhost --format Pretty --query "
    SELECT 
        table,
        name as index_name,
        type,
        expr as index_expression,
        granularity
    FROM system.data_skipping_indices
    WHERE database = 'music_recommend'
    ORDER BY table, name
" 2>&1; then
    echo ""
else
    echo "   ⚠️  Не удалось получить информацию об индексах"
    echo "   💡 Убедитесь, что используется правильное имя схемы: system (не sys)"
    echo ""
fi

echo ""
echo "✅ Готово! Индексы добавлены для оптимизации запросов."
echo ""
echo "💡 Для применения индексов к существующим данным:"
echo "   docker exec music_recommend_clickhouse clickhouse-client --host localhost --query 'OPTIMIZE TABLE music_recommend.user_track_matrix FINAL'"
echo "   docker exec music_recommend_clickhouse clickhouse-client --host localhost --query 'OPTIMIZE TABLE music_recommend.user_track_interactions FINAL'"

