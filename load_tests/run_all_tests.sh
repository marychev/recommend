#!/bin/bash

###############################################################################
# Скрипт для последовательного запуска всех нагрузочных тестов k6
# 
# Использование: ./load_tests/run_all_tests.sh
###############################################################################

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
API_URL=${API_URL:-"http://localhost:8000"}
RESULTS_DIR="load_tests/results"

# Создаем директорию для результатов
mkdir -p "$RESULTS_DIR"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     🚀 ЗАПУСК НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ k6              ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}⚙️  Конфигурация:${NC}"
echo -e "   • API URL: ${GREEN}${API_URL}${NC}"
echo -e "   • Результаты: ${GREEN}${RESULTS_DIR}${NC}\n"

# Проверка доступности API
echo -e "${YELLOW}🔍 Проверка доступности API...${NC}"
if curl -s -o /dev/null -w "%{http_code}" "${API_URL}" | grep -q "200\|404"; then
    echo -e "${GREEN}✓ API доступен${NC}\n"
else
    echo -e "${RED}✗ API недоступен. Запустите сервисы: docker-compose up -d${NC}"
    exit 1
fi

# Проверка k6
echo -e "${YELLOW}🔍 Проверка k6...${NC}"
if command -v k6 &> /dev/null; then
    K6_VERSION=$(k6 version | head -n 1)
    echo -e "${GREEN}✓ k6 установлен: ${K6_VERSION}${NC}\n"
else
    echo -e "${RED}✗ k6 не установлен. Установите: https://k6.io/docs/getting-started/installation/${NC}"
    exit 1
fi

# Функция для запуска теста
run_test() {
    local test_name=$1
    local test_file=$2
    local duration=$3
    
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Тест: ${test_name}${NC}"
    echo -e "${BLUE}║  Ожидаемая длительность: ${duration}${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}\n"
    
    local start_time=$(date +%s)
    
    # Запускаем тест
    if API_URL="${API_URL}" k6 run "${test_file}" --out json="${RESULTS_DIR}/${test_name}_$(date +%Y%m%d_%H%M%S).json"; then
        local end_time=$(date +%s)
        local elapsed=$((end_time - start_time))
        echo -e "\n${GREEN}✓ ${test_name} завершен успешно (${elapsed}s)${NC}\n"
        return 0
    else
        echo -e "\n${RED}✗ ${test_name} завершен с ошибками${NC}\n"
        return 1
    fi
}

# Запуск тестов
echo -e "${YELLOW}📊 Начало тестирования...${NC}\n"

TOTAL_TESTS=4
PASSED_TESTS=0
FAILED_TESTS=0

# 1. Basic Load Test
if run_test "basic_load_test" "load_tests/k6_basic_load_test.js" "~15 минут"; then
    ((PASSED_TESTS++))
else
    ((FAILED_TESTS++))
fi

# Пауза между тестами
echo -e "${YELLOW}⏸️  Пауза 30 секунд перед следующим тестом...${NC}"
sleep 30

# 2. Spike Test
if run_test "spike_test" "load_tests/k6_spike_test.js" "~3 минуты"; then
    ((PASSED_TESTS++))
else
    ((FAILED_TESTS++))
fi

# Пауза между тестами
echo -e "${YELLOW}⏸️  Пауза 30 секунд перед следующим тестом...${NC}"
sleep 30

# 3. Stress Test
if run_test "stress_test" "load_tests/k6_stress_test.js" "~30 минут"; then
    ((PASSED_TESTS++))
else
    ((FAILED_TESTS++))
fi

# Пауза перед длительным тестом
echo -e "${YELLOW}⏸️  Пауза 60 секунд перед следующим тестом...${NC}"
sleep 60

# 4. Soak Test (только если предыдущие прошли успешно)
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Запуск длительного теста (soak test). Длительность: ~70 минут${NC}"
    echo -e "${YELLOW}   Нажмите Ctrl+C в течение 10 секунд, чтобы пропустить...${NC}"
    
    if sleep 10; then
        if run_test "soak_test" "load_tests/k6_soak_test.js" "~70 минут"; then
            ((PASSED_TESTS++))
        else
            ((FAILED_TESTS++))
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Soak test пропущен из-за ошибок в предыдущих тестах${NC}\n"
fi

# Итоговый отчет
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              📊 ИТОГОВЫЙ ОТЧЕТ                          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}\n"

echo -e "   • Всего тестов: ${TOTAL_TESTS}"
echo -e "   • Успешных: ${GREEN}${PASSED_TESTS}${NC}"
echo -e "   • Неудачных: ${RED}${FAILED_TESTS}${NC}"
echo -e "   • Результаты: ${RESULTS_DIR}\n"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Все тесты успешно пройдены!${NC}\n"
    exit 0
else
    echo -e "${RED}✗ Некоторые тесты завершились с ошибками${NC}\n"
    exit 1
fi

