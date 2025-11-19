#!/bin/bash

# ════════════════════════════════════════════════════════
# Скрипт для запуска k6 тестов
# ════════════════════════════════════════════════════════

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Конфигурация
API_URL=${API_URL:-http://localhost:8000}
K6_VERSION="k6 v0.45.0"

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  K6 Load Testing Suite${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}API URL: ${API_URL}${NC}"
echo ""

# Проверка наличия k6
if ! command -v k6 &> /dev/null; then
    echo -e "${RED}❌ k6 не установлен!${NC}"
    echo ""
    echo "Установите k6:"
    echo "  Linux/Mac: brew install k6 или snap install k6"
    echo "  Windows: choco install k6 или скачайте с https://k6.io/docs/getting-started/installation/"
    exit 1
fi

echo -e "${GREEN}✅ k6 установлен${NC}"
echo ""

# Функция для запуска теста
run_test() {
    local test_name=$1
    local test_file=$2
    local description=$3
    
    echo -e "${YELLOW}────────────────────────────────────────────────────────────${NC}"
    echo -e "${YELLOW}▶ Запуск: ${test_name}${NC}"
    echo -e "${YELLOW}  ${description}${NC}"
    echo -e "${YELLOW}────────────────────────────────────────────────────────────${NC}"
    echo ""
    
    k6 run --env API_URL=${API_URL} ${test_file}
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ${test_name} завершен успешно${NC}"
    else
        echo -e "${RED}❌ ${test_name} завершен с ошибками${NC}"
    fi
    echo ""
}

# Меню выбора теста
echo "Выберите тест для запуска:"
echo ""
echo "  1) Быстрый тест (5 минут)"
echo "  2) Полный пользовательский сценарий (51 минута)"
echo "  3) Тест производительности рекомендаций"
echo "  4) Все тесты последовательно"
echo "  5) Выход"
echo ""
read -p "Ваш выбор (1-5): " choice

case $choice in
    1)
        run_test \
            "Быстрый тест" \
            "load_tests/k6_quick_test.js" \
            "Проверка базовой функциональности (авторизация, пользователь, рекомендации)"
        ;;
    2)
        echo -e "${YELLOW}⚠️  Внимание! Этот тест займет ~51 минуту${NC}"
        read -p "Продолжить? (y/n): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            run_test \
                "Полный сценарий" \
                "load_tests/k6_full_user_scenario_test.js" \
                "Комплексный тест с определением оптимальной и максимальной нагрузки"
        fi
        ;;
    3)
        run_test \
            "Тест производительности рекомендаций" \
            "load_tests/k6_recommendations_performance_test.js" \
            "Детальный анализ производительности компонентов (Redis, ClickHouse, алгоритм)"
        ;;
    4)
        echo -e "${YELLOW}⚠️  Внимание! Все тесты займут больше часа${NC}"
        read -p "Продолжить? (y/n): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            run_test \
                "Быстрый тест" \
                "load_tests/k6_quick_test.js" \
                "Проверка базовой функциональности"
            
            run_test \
                "Тест производительности рекомендаций" \
                "load_tests/k6_recommendations_performance_test.js" \
                "Детальный анализ производительности"
            
            run_test \
                "Полный сценарий" \
                "load_tests/k6_full_user_scenario_test.js" \
                "Комплексный тест нагрузки"
        fi
        ;;
    5)
        echo "Выход..."
        exit 0
        ;;
    *)
        echo -e "${RED}Неверный выбор${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Готово!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Результаты сохранены в файлах summary_*.json и summary_*.html"
echo ""

