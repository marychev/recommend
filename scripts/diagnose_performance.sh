#!/bin/bash
# Скрипт диагностики производительности

echo "🔍 Диагностика производительности..."
echo ""

# 1. Проверка статуса контейнеров
echo "1️⃣  Статус контейнеров:"
docker compose ps | grep -E "(clickhouse|api|redis|kafka)" || echo "   ⚠️  Контейнеры не запущены"
echo ""

# 2. Проверка ClickHouse
echo "2️⃣  Проверка ClickHouse:"
if curl -s http://localhost:8123/ > /dev/null 2>&1; then
    echo "   ✅ ClickHouse доступен"
    echo "   📊 Проверка медленных запросов:"
    docker exec music_recommend_clickhouse clickhouse-client -q "
        SELECT 
            query,
            query_duration_ms,
            read_rows,
            formatReadableSize(memory_usage) as memory
        FROM system.query_log 
        WHERE type = 'QueryFinish' 
        AND query_duration_ms > 1000
        ORDER BY query_duration_ms DESC 
        LIMIT 10
    " 2>/dev/null || echo "   ⚠️  Не удалось получить логи запросов"
else
    echo "   ❌ ClickHouse недоступен!"
fi
echo ""

# 3. Проверка последних ошибок ClickHouse
echo "3️⃣  Последние ошибки ClickHouse:"
docker compose logs clickhouse --tail 20 | grep -i error || echo "   ✅ Нет ошибок"
echo ""

# 4. Проверка использования ресурсов
echo "4️⃣  Использование ресурсов:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep -E "(CONTAINER|clickhouse|api)" || echo "   ⚠️  Не удалось получить статистику"
echo ""

# 5. Проверка индексов
echo "5️⃣  Проверка индексов в ClickHouse:"
docker exec music_recommend_clickhouse clickhouse-client -q "
    SELECT 
        database,
        table,
        name,
        type
    FROM system.data_skipping_indices 
    WHERE database = 'music_recommend'
    ORDER BY table, name
" 2>/dev/null || echo "   ⚠️  Не удалось проверить индексы"
echo ""

# 6. Проверка размера таблиц
echo "6️⃣  Размер таблиц:"
docker exec music_recommend_clickhouse clickhouse-client -q "
    SELECT 
        table,
        formatReadableSize(sum(bytes)) as size,
        sum(rows) as rows
    FROM system.parts 
    WHERE database = 'music_recommend' AND active
    GROUP BY table
    ORDER BY sum(bytes) DESC
" 2>/dev/null || echo "   ⚠️  Не удалось получить размер таблиц"
echo ""

echo "✅ Диагностика завершена"

