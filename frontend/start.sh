#!/bin/bash

# Скрипт для запуска frontend

echo "🚀 Запуск Frontend - Music Recommendation System"
echo ""
echo "📡 API должно быть запущено на http://localhost:8000"
echo "   Если API не запущено, запустите его командой:"
echo "   python -m app.main"
echo ""
echo "🌐 Запуск HTTP сервера на порту 8080..."
echo "   Откройте браузер: http://localhost:8080"
echo ""
echo "Нажмите Ctrl+C для остановки"
echo ""

# Проверяем доступность API
if command -v curl &> /dev/null; then
    if curl -s http://localhost:8000/api/v1/health &> /dev/null; then
        echo "✅ API доступно"
    else
        echo "⚠️  Внимание: API недоступно на http://localhost:8000"
        echo "   Убедитесь, что backend запущен"
    fi
fi

echo ""

# Запускаем HTTP сервер
if command -v python3 &> /dev/null; then
    python3 -m http.server 8080
elif command -v python &> /dev/null; then
    python -m http.server 8080
else
    echo "❌ Python не найден. Установите Python или откройте index.html напрямую в браузере."
    exit 1
fi

