#!/bin/bash
# Скрипт для восстановления ClickHouse после оптимизаций

set -e

echo "🔧 Восстановление ClickHouse..."

# Остановка контейнера
echo "1. Остановка ClickHouse..."
docker compose stop clickhouse 2>/dev/null || true

# Удаление контейнера (данные сохраняются в volume)
echo "2. Удаление контейнера..."
docker compose rm -f clickhouse 2>/dev/null || true

# Запуск заново
echo "3. Запуск ClickHouse..."
docker compose up -d clickhouse

# Ожидание запуска
echo "4. Ожидание запуска (15 секунд)..."
sleep 15

# Проверка подключения
echo "5. Проверка подключения..."
for i in {1..10}; do
    if curl -s http://localhost:8123/ > /dev/null 2>&1; then
        echo "✅ ClickHouse запущен успешно!"
        curl http://localhost:8123/
        exit 0
    fi
    echo "   Попытка $i/10..."
    sleep 2
done

echo "❌ ClickHouse не запустился. Проверьте логи:"
echo "   docker compose logs clickhouse"
exit 1

