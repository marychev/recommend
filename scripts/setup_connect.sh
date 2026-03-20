#!/bin/bash
# Настройка Kafka Connect: ожидание готовности и регистрация коннекторов

set -e

CONNECT_URL="http://localhost:8083"
CONNECTORS_DIR="connect/connectors"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Настройка Kafka Connect ClickHouse Sink${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"

# 1. Ожидание готовности REST API
echo -e "${YELLOW}Ожидание готовности Kafka Connect REST API...${NC}"
MAX_WAIT=120
WAITED=0
while ! curl -sf "$CONNECT_URL/" > /dev/null 2>&1; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo -e "${RED}Kafka Connect не запустился за ${MAX_WAIT} секунд${NC}"
        exit 1
    fi
    sleep 2
    WAITED=$((WAITED + 2))
    echo -e "  Ожидание... (${WAITED}s / ${MAX_WAIT}s)"
done
echo -e "${GREEN}Kafka Connect готов!${NC}"

# 2. Регистрация коннекторов
for config_file in "$CONNECTORS_DIR"/*.json; do
    connector_name=$(basename "$config_file" .json)
    echo -e "${YELLOW}Регистрация коннектора: ${connector_name}${NC}"

    # Удаляем если уже существует (для идемпотентности)
    curl -sf -X DELETE "$CONNECT_URL/connectors/$connector_name" > /dev/null 2>&1 || true

    # Создаём коннектор
    response=$(curl -sf -X POST "$CONNECT_URL/connectors" \
        -H "Content-Type: application/json" \
        -d @"$config_file" 2>&1)

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  $connector_name — зарегистрирован${NC}"
    else
        echo -e "${RED}  $connector_name — ошибка: $response${NC}"
    fi
done

# 3. Проверка статуса
echo ""
echo -e "${YELLOW}Статус коннекторов:${NC}"
sleep 3  # даём время на запуск tasks

for config_file in "$CONNECTORS_DIR"/*.json; do
    connector_name=$(basename "$config_file" .json)
    status=$(curl -sf "$CONNECT_URL/connectors/$connector_name/status" 2>/dev/null)
    if [ $? -eq 0 ]; then
        state=$(echo "$status" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['connector']['state'])" 2>/dev/null || echo "UNKNOWN")
        task_state=$(echo "$status" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tasks'][0]['state'] if d.get('tasks') else 'NO_TASKS')" 2>/dev/null || echo "UNKNOWN")
        echo -e "  ${connector_name}: connector=${state}, task=${task_state}"
    else
        echo -e "  ${RED}${connector_name}: не удалось получить статус${NC}"
    fi
done

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Kafka Connect настроен!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Полезные команды:${NC}"
echo "  make connect-status    — статус коннекторов"
echo "  make connect-lag       — consumer lag"
echo "  make logs-connect      — логи Kafka Connect"
echo ""
