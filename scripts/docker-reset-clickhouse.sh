#!/bin/bash
# Скрипт для пересоздания ClickHouse контейнера с правильными настройками

echo "🔧 Скрипт пересоздания ClickHouse контейнера"
echo "=========================================="
echo ""

echo "🔄 Останавливаем и удаляем старый контейнер ClickHouse..."
docker-compose stop clickhouse
docker-compose rm -f clickhouse

echo ""
echo "🗑️ Удаление volume с данными..."
echo "⚠️  ВАЖНО: Для применения новой конфигурации нужно удалить старый volume!"
read -p "Удалить все данные ClickHouse? (Y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Nn]$ ]]
then
    docker volume rm recommend_clickhouse_data 2>/dev/null || true
    echo "✅ Volume удален"
else
    echo "⚠️  Volume НЕ удален - новая конфигурация может не примениться!"
fi

echo ""
echo "📁 Проверяем конфигурационный файл..."
if [ -f "clickhouse-config/users.xml" ]; then
    echo "✅ Файл clickhouse-config/users.xml найден"
else
    echo "❌ ОШИБКА: Файл clickhouse-config/users.xml не найден!"
    echo "   Убедитесь что файл существует"
    exit 1
fi

echo ""
echo "🚀 Запускаем новый контейнер ClickHouse..."
docker-compose up -d clickhouse

echo ""
echo "⏳ Ждем запуска ClickHouse (15 секунд)..."
for i in {15..1}; do
    echo -ne "   $i сек...\r"
    sleep 1
done
echo "   Готово!     "

echo ""
echo "🔍 Проверяем подключение..."
RESPONSE=$(curl -s -w "%{http_code}" http://localhost:8123/ -o /dev/null)
if [ "$RESPONSE" = "200" ]; then
    echo "✅ ClickHouse запущен и доступен! (HTTP 200)"
    echo ""
    curl -s http://localhost:8123/ && echo ""
else
    echo "❌ Ошибка подключения (HTTP $RESPONSE)"
fi

echo ""
echo "📊 Статус контейнера:"
docker ps | grep clickhouse

echo ""
echo "📝 Проверяем монтирование конфигурации..."
docker exec music_recommend_clickhouse test -f /etc/clickhouse-server/users.d/users.xml && \
    echo "✅ Конфигурационный файл смонтирован" || \
    echo "❌ Конфигурационный файл НЕ смонтирован"

echo ""
echo "=========================================="
echo "✨ Готово!"
echo ""
echo "Теперь можно запускать тесты:"
echo "   pytest tests/clickhouse/test_connection.py -v"
echo ""
echo "Или все тесты ClickHouse:"
echo "   pytest tests/clickhouse/ -v"
echo ""
echo "Если проблемы остались, см. docs/"
echo "=========================================="

