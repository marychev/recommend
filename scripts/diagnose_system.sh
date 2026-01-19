#!/bin/bash
# Скрипт комплексной диагностики системы рекомендаций
# Проверяет все компоненты: Docker, Kafka, ClickHouse, Redis, API

# Не останавливаемся на ошибках - продолжаем диагностику
set +e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Счетчики
PASSED=0
FAILED=0
WARNINGS=0

# Функция для вывода заголовка секции
section() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════${NC}"
}

# Функция для проверки с выводом результата
check() {
    local name="$1"
    local command="$2"
    local fix_hint="$3"
    
    echo -n "  ${name}... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        if [ -n "$fix_hint" ]; then
            echo -e "     ${YELLOW}💡 ${fix_hint}${NC}"
        fi
        ((FAILED++))
        return 1
    fi
}

# Функция для предупреждения
warn() {
    local name="$1"
    local message="$2"
    
    echo -e "  ${name}... ${YELLOW}⚠️  WARNING: ${message}${NC}"
    ((WARNINGS++))
}

# Функция для получения информации
info() {
    local name="$1"
    local command="$2"
    
    echo -n "  ${name}: "
    local result=$(eval "$command" 2>/dev/null || echo "N/A")
    echo -e "${CYAN}${result}${NC}"
}

section "🐳 Docker контейнеры"

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен${NC}"
    exit 1
fi

# Проверка запущенных контейнеров
echo "  Проверка контейнеров:"
check "ClickHouse контейнер" "docker ps --format '{{.Names}}' | grep -q music_recommend_clickhouse" \
    "Запустите: docker compose up -d clickhouse"

check "Kafka контейнер" "docker ps --format '{{.Names}}' | grep -q music_recommend_kafka" \
    "Запустите: docker compose up -d kafka"

check "Zookeeper контейнер" "docker ps --format '{{.Names}}' | grep -q music_recommend_zookeeper" \
    "Запустите: docker compose up -d zookeeper"

check "Redis контейнер" "docker ps --format '{{.Names}}' | grep -q music_recommend_redis" \
    "Запустите: docker compose up -d redis"

check "API контейнер" "docker ps --format '{{.Names}}' | grep -q music_recommend_api" \
    "Запустите: docker compose up -d api"

# Статус контейнеров
echo ""
echo "  Статус контейнеров:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep music_recommend || \
    echo -e "${YELLOW}  ⚠️  Нет запущенных контейнеров${NC}"

section "📊 ClickHouse"

# Проверка доступности ClickHouse
check "ClickHouse HTTP (8123)" "curl -s http://localhost:8123/ | grep -q 'Ok'" \
    "Проверьте: docker logs music_recommend_clickhouse"

# Проверка подключения через Docker
if docker ps --format '{{.Names}}' | grep -q music_recommend_clickhouse; then
    echo "  Проверка внутри контейнера:"
    if docker exec music_recommend_clickhouse clickhouse-client --query "SELECT 1" > /dev/null 2>&1; then
        echo -e "    ${GREEN}✅ ClickHouse клиент работает${NC}"
        ((PASSED++))
        
        # Проверка базы данных
        echo "  Проверка базы данных:"
        DB_EXISTS=$(docker exec music_recommend_clickhouse clickhouse-client --query "EXISTS DATABASE music_recommend" 2>/dev/null || echo "0")
        if [ "$DB_EXISTS" = "1" ]; then
            echo -e "    ${GREEN}✅ База данных 'music_recommend' существует${NC}"
            ((PASSED++))
            
            # Проверка таблиц
            echo "  Проверка таблиц:"
            TABLES=$(docker exec music_recommend_clickhouse clickhouse-client --query "SHOW TABLES FROM music_recommend" 2>/dev/null || echo "")
            if [ -n "$TABLES" ]; then
                echo -e "    ${GREEN}✅ Таблицы найдены:${NC}"
                echo "$TABLES" | while read table; do
                    echo -e "      ${CYAN}- ${table}${NC}"
                done
                ((PASSED++))
            else
                warn "Таблицы" "Таблицы не найдены. Запустите: make db-init"
            fi
        else
            warn "База данных" "База данных 'music_recommend' не существует. Запустите: make db-init"
        fi
    else
        warn "ClickHouse клиент" "Не удалось подключиться к ClickHouse внутри контейнера"
    fi
fi

section "🔴 Redis"

# Проверка доступности Redis
check "Redis (6379)" "docker exec music_recommend_redis redis-cli ping 2>/dev/null | grep -q PONG" \
    "Проверьте: docker logs music_recommend_redis"

if docker ps --format '{{.Names}}' | grep -q music_recommend_redis; then
    # Информация о Redis
    echo "  Информация о Redis:"
    INFO=$(docker exec music_recommend_redis redis-cli INFO server 2>/dev/null | grep -E "redis_version|uptime_in_days" || echo "")
    if [ -n "$INFO" ]; then
        echo "$INFO" | while read line; do
            echo -e "    ${CYAN}${line}${NC}"
        done
    fi
fi

section "📨 Kafka"

# Проверка доступности Kafka
if command -v timeout &> /dev/null; then
    check "Kafka (9092)" "timeout 2 bash -c '</dev/tcp/localhost/9092' 2>/dev/null || docker exec music_recommend_kafka kafka-broker-api-versions --bootstrap-server localhost:29092 > /dev/null 2>&1" \
        "Проверьте: docker logs music_recommend_kafka"
else
    check "Kafka (9092)" "docker exec music_recommend_kafka kafka-broker-api-versions --bootstrap-server localhost:29092 > /dev/null 2>&1" \
        "Проверьте: docker logs music_recommend_kafka"
fi

if docker ps --format '{{.Names}}' | grep -q music_recommend_kafka; then
    echo "  Проверка топиков Kafka:"
    
    # Список топиков
    TOPICS=$(docker exec music_recommend_kafka kafka-topics --list --bootstrap-server localhost:29092 2>/dev/null || echo "")
    
    if [ -n "$TOPICS" ]; then
        echo -e "    ${GREEN}✅ Найдены топики:${NC}"
        echo "$TOPICS" | while read topic; do
            echo -e "      ${CYAN}- ${topic}${NC}"
        done
        ((PASSED++))
        
        # Проверка конкретных топиков
        echo ""
        echo "  Проверка требуемых топиков:"
        check "Топик 'user_track_events'" "echo '$TOPICS' | grep -q 'user_track_events'" \
            "Создайте: docker exec music_recommend_kafka kafka-topics --create --topic user_track_events --bootstrap-server localhost:29092 --partitions 3 --replication-factor 1"
        
        check "Топик 'users'" "echo '$TOPICS' | grep -q '^users$'" \
            "Создайте: docker exec music_recommend_kafka kafka-topics --create --topic users --bootstrap-server localhost:29092 --partitions 3 --replication-factor 1"
        
        check "Топик 'tracks'" "echo '$TOPICS' | grep -q '^tracks$'" \
            "Создайте: docker exec music_recommend_kafka kafka-topics --create --topic tracks --bootstrap-server localhost:29092 --partitions 3 --replication-factor 1"
        
        # Информация о топиках
        echo ""
        echo "  Детальная информация о топиках:"
        for topic in user_track_events users tracks; do
            if echo "$TOPICS" | grep -q "^${topic}$"; then
                PARTITIONS=$(docker exec music_recommend_kafka kafka-topics --describe --topic "$topic" --bootstrap-server localhost:29092 2>/dev/null | grep -c "Partition:" || echo "0")
                echo -e "    ${CYAN}${topic}:${NC} ${PARTITIONS} партиций"
            fi
        done
    else
        warn "Топики Kafka" "Топики не найдены. Kafka может быть еще не готова или топики не созданы автоматически."
    fi
    
    # Проверка Zookeeper
    echo ""
    echo "  Проверка Zookeeper:"
    if command -v nc &> /dev/null; then
        check "Zookeeper (2181)" "docker exec music_recommend_zookeeper nc -z localhost 2181 2>/dev/null" \
            "Проверьте: docker logs music_recommend_zookeeper"
    else
        check "Zookeeper контейнер" "docker ps --format '{{.Names}}' | grep -q music_recommend_zookeeper" \
            "Проверьте: docker logs music_recommend_zookeeper"
    fi
fi

section "🌐 API (FastAPI)"

# Проверка доступности API
check "API (8000)" "curl -s http://localhost:8000/ > /dev/null" \
    "Проверьте: docker logs music_recommend_api или запустите: python -m app.main"

if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "  Проверка эндпоинтов:"
    
    # Health check
    HEALTH=$(curl -s http://localhost:8000/api/v1/health 2>/dev/null || echo "")
    if [ -n "$HEALTH" ]; then
        echo -e "    ${GREEN}✅ Health endpoint доступен${NC}"
        ((PASSED++))
        
        # Парсим статус
        STATUS=$(echo "$HEALTH" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
        echo -e "      ${CYAN}Статус: ${STATUS}${NC}"
        
        # Парсим статусы сервисов
        echo "      Сервисы:"
        echo "$HEALTH" | grep -o '"[^"]*":"[^"]*"' | while read service; do
            KEY=$(echo "$service" | cut -d'"' -f2)
            VALUE=$(echo "$service" | cut -d'"' -f4)
            if [ "$KEY" != "status" ] && [ "$KEY" != "timestamp" ]; then
                if [ "$VALUE" = "connected" ]; then
                    echo -e "        ${GREEN}${KEY}: ${VALUE}${NC}"
                else
                    echo -e "        ${RED}${KEY}: ${VALUE}${NC}"
                fi
            fi
        done
    else
        warn "Health endpoint" "Не удалось получить ответ от /api/v1/health"
    fi
    
    # Swagger
    check "Swagger UI" "curl -s http://localhost:8000/docs > /dev/null" \
        "Откройте: http://localhost:8000/docs"
fi

section "📋 Логи (последние ошибки)"

# Проверка логов на ошибки
echo "  Проверка логов контейнеров на ошибки:"

for container in music_recommend_api music_recommend_clickhouse music_recommend_kafka music_recommend_redis; do
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${container}$"; then
        ERRORS=$(docker logs "$container" --tail 50 2>&1 | grep -iE "error|exception|failed" | head -5 || echo "")
        if [ -n "$ERRORS" ]; then
            echo -e "    ${YELLOW}⚠️  ${container}:${NC}"
            echo "$ERRORS" | while IFS= read -r error || [ -n "$error" ]; do
                if [ -n "$error" ]; then
                    echo -e "      ${RED}${error}${NC}"
                fi
            done
            ((WARNINGS++))
        else
            echo -e "    ${GREEN}✅ ${container}: ошибок не найдено${NC}"
        fi
    fi
done

section "🔧 Конфигурация"

# Проверка переменных окружения
echo "  Проверка конфигурации:"
if [ -f ".env" ]; then
    echo -e "    ${GREEN}✅ Файл .env найден${NC}"
    ((PASSED++))
else
    warn ".env файл" "Файл .env не найден. Используются значения по умолчанию."
fi

# Проверка docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    echo -e "    ${GREEN}✅ docker-compose.yml найден${NC}"
    ((PASSED++))
else
    warn "docker-compose.yml" "Файл docker-compose.yml не найден"
fi

section "📊 Итоги диагностики"

echo ""
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}✅ Успешно: ${PASSED}${NC}"
echo -e "  ${RED}❌ Ошибок: ${FAILED}${NC}"
echo -e "  ${YELLOW}⚠️  Предупреждений: ${WARNINGS}${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"

# Рекомендации
if [ $FAILED -gt 0 ] || [ $WARNINGS -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}💡 Рекомендации:${NC}"
    
    if ! docker ps --format '{{.Names}}' | grep -q music_recommend_clickhouse; then
        echo "  - Запустите ClickHouse: docker compose up -d clickhouse"
    fi
    
    if ! docker ps --format '{{.Names}}' | grep -q music_recommend_kafka; then
        echo "  - Запустите Kafka: docker compose up -d kafka"
    fi
    
    if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "  - Запустите API: docker compose up -d api или python -m app.main"
    fi
    
    echo "  - Проверьте логи: docker logs <container_name>"
    echo "  - Полная перезагрузка: docker compose down && docker compose up -d"
fi

# Выход с кодом ошибки если есть проблемы
if [ $FAILED -gt 0 ]; then
    exit 1
else
    exit 0
fi

