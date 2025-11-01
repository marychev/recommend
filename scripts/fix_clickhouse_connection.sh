#!/bin/bash
# Быстрое исправление проблем с подключением к ClickHouse

echo "🔧 Исправление проблем с ClickHouse"
echo "=================================================="

# 1. Проверка что ClickHouse запущен
echo ""
echo "1️⃣  Проверка что ClickHouse запущен..."
if docker ps | grep -q music_recommend_clickhouse; then
    echo "   ✅ Контейнер запущен"
else
    echo "   ❌ Контейнер НЕ запущен"
    echo "   🚀 Запускаем..."
    docker-compose up -d clickhouse
    echo "   ⏳ Ждем 15 секунд..."
    sleep 15
fi

# 2. Проверка HTTP порта
echo ""
echo "2️⃣  Проверка HTTP порта 8123..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8123/)
if [ "$RESPONSE" = "200" ]; then
    echo "   ✅ Порт 8123 доступен"
    curl -s http://localhost:8123/ && echo ""
else
    echo "   ❌ Порт 8123 НЕ доступен (HTTP $RESPONSE)"
    echo "   💡 Пересоздайте контейнер:"
    echo "      bash scripts/docker-reset-clickhouse.sh"
    exit 1
fi

# 3. Проверка что таблицы созданы
echo ""
echo "3️⃣  Проверка таблиц в БД..."
TABLES=$(docker exec music_recommend_clickhouse clickhouse-client -q "SHOW TABLES FROM music_recommend" 2>&1)
if echo "$TABLES" | grep -q "users"; then
    echo "   ✅ Таблицы существуют"
    echo "$TABLES" | sed 's/^/      /'
else
    echo "   ⚠️  Таблицы не созданы"
    echo "   🔧 Создаем таблицы..."
    docker exec -i music_recommend_clickhouse clickhouse-client < app/db/clickhouse_schemas.sql
    echo "   ✅ Таблицы созданы!"
fi

# 4. Проверка подключения из Python
echo ""
echo "4️⃣  Проверка подключения из Python..."
python3 - << 'EOF'
try:
    import clickhouse_connect
    client = clickhouse_connect.get_client(
        host='localhost',
        port=8123,
        username='default',
        password='',
        database='music_recommend'
    )
    result = client.command("SELECT 1")
    print("   ✅ Python может подключиться к ClickHouse")
except Exception as e:
    print(f"   ❌ Ошибка Python подключения: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "   💡 Проверьте что в .env указан правильный порт:"
    echo "      CLICKHOUSE_PORT=8123"
    exit 1
fi

# 5. Проверка health endpoint
echo ""
echo "5️⃣  Проверка API health check..."
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:8000/api/v1/health)
    echo "   Ответ API:"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
    
    if echo "$HEALTH" | grep -q '"clickhouse":"connected"'; then
        echo ""
        echo "   ✅ ClickHouse подключен через API!"
    else
        echo ""
        echo "   ⚠️  API показывает ClickHouse как disconnected"
        echo "   💡 Перезапустите приложение:"
        echo "      pkill -f 'uvicorn app.main' || pkill -f 'python.*app.main'"
        echo "      python -m app.main"
    fi
else
    echo "   ⚠️  API не запущен"
    echo "   💡 Запустите: python -m app.main"
fi

echo ""
echo "=================================================="
echo "✨ Проверка завершена!"
echo ""
echo "Если API показывает 'disconnected':"
echo "1. Остановите приложение (Ctrl+C)"
echo "2. Запустите заново: python -m app.main"
echo "3. Проверьте: curl http://localhost:8000/api/v1/health"
echo "=================================================="

