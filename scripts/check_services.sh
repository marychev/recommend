#!/bin/bash
# Скрипт для проверки доступности всех сервисов

echo "=================================================="
echo "🔍 Проверка доступности сервисов"
echo "=================================================="

# ClickHouse
echo ""
echo "📊 ClickHouse (порт 8123):"
if curl -s http://localhost:8123/ > /dev/null 2>&1; then
    echo "   ✅ Доступен"
    curl -s http://localhost:8123/
else
    echo "   ❌ НЕ доступен"
    echo "   💡 Запустите: docker-compose up -d clickhouse"
fi

# Redis
echo ""
echo "🔴 Redis (порт 6379):"
if command -v redis-cli &> /dev/null; then
    if redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
        echo "   ✅ Доступен"
    else
        echo "   ❌ НЕ доступен"
        echo "   💡 Запустите: docker-compose up -d redis"
    fi
else
    echo "   ⚠️  redis-cli не установлен"
    echo "   Проверьте через Docker:"
    docker exec music_recommend_redis redis-cli ping 2>&1 | grep -q PONG && \
        echo "   ✅ Redis работает в Docker" || \
        echo "   ❌ Redis не работает"
fi

# FastAPI
echo ""
echo "🌐 FastAPI (порт 8000):"
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "   ✅ Доступен"
    echo "   📚 Swagger UI: http://localhost:8000/docs"
else
    echo "   ❌ НЕ доступен"
    echo "   💡 Запустите: python -m app.main"
fi

# Docker containers
echo ""
echo "🐳 Docker контейнеры:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep music_recommend || \
    echo "   ⚠️  Нет запущенных контейнеров"

echo ""
echo "=================================================="
echo "📋 Итоги:"
echo "=================================================="

# Проверяем все сервисы
ALL_OK=true

curl -s http://localhost:8123/ > /dev/null 2>&1 || ALL_OK=false
curl -s http://localhost:8000/ > /dev/null 2>&1 || ALL_OK=false

if [ "$ALL_OK" = true ]; then
    echo "✅ Все сервисы работают!"
    echo ""
    echo "Попробуйте:"
    echo "  curl http://localhost:8000/api/v1/health"
else
    echo "❌ Некоторые сервисы недоступны"
    echo ""
    echo "Для запуска всех сервисов:"
    echo "  docker-compose up -d"
fi

echo "=================================================="

