.PHONY: help setup up down build rebuild ps shell \
	logs logs-api logs-clickhouse logs-kafka logs-errors logs-redis \
	load-test-install load-test-data-generate load-test-diagnostics \
	load-test-spike-extreme load-test-results \
	load-test-quick load-test-smoke load-test-basic load-test-spike load-test-stress load-test-soak \
	load-test-recommendations load-test-recommendations-quick load-test-post load-test-post-quick \
	status check-services health diagnose diagnose-system diagnose-cache test-ttl-optimization test-cache-warmup test-api-health urls \
	clean clean-all \
	test test-api test-cache test-clickhouse test-kafka   \
	db-init db-indexes db-optimize db-reset db-shell db-tables db-stats fix-clickhouse diagnose-performance \
	lint lint-install format \
	up-clickhouse up-kafka up-redis up-api restart-api \
	up-pipeline-connect down-pipeline-connect up-pipeline-engine down-pipeline-engine \
	connect-status connect-lag logs-connect pipeline-verify

# Цвета для вывода
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Docker Compose команда
DOCKER_COMPOSE := docker compose

help: ## Показать справку по доступным командам
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  🎵 Music Recommendation System - Makefile$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"

# ═══════════════════════════════════════════════
# 🔧 Отдельные сервисы
# ═══════════════════════════════════════════════

up-clickhouse: ## Запустить только ClickHouse
	@echo "$(GREEN)🚀 Запуск ClickHouse...$(NC)"
	$(DOCKER_COMPOSE) up -d clickhouse

up-kafka: ## Запустить только Kafka + Zookeeper
	@echo "$(GREEN)🚀 Запуск Kafka + Zookeeper...$(NC)"
	$(DOCKER_COMPOSE) up -d zookeeper kafka

up-redis: ## Запустить только Redis
	@echo "$(GREEN)🚀 Запуск Redis...$(NC)"
	$(DOCKER_COMPOSE) up -d redis

up-api: ## Запустить только API
	@echo "$(GREEN)🚀 Запуск API...$(NC)"
	$(DOCKER_COMPOSE) up -d api

restart-api: ## Перезапустить API контейнер
	@echo "$(YELLOW)🔄 Перезапуск API...$(NC)"
	$(DOCKER_COMPOSE) restart api
	@echo "$(GREEN)✅ API перезапущен$(NC)"

# ═══════════════════════════════════════════════
# 🔬 Pipeline Benchmark — переключение решений
# ═══════════════════════════════════════════════
# Решение A (Python Consumer) = обычный make up
# Решение B (Kafka Connect Sink) = make up-pipeline-connect
# Решение C (Kafka Table Engine) = make up-pipeline-engine
# Подробности: ROADMAP.md

DOCKER_COMPOSE_CONNECT := docker compose -f docker-compose.yml -f docker-compose.connect.yml

up-pipeline-connect: ## [Benchmark] Запустить решение B: Kafka Connect Sink
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  Pipeline B: Kafka Connect Sink$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(YELLOW)Останавливаем текущие сервисы...$(NC)"
	$(DOCKER_COMPOSE) down 2>/dev/null || true
	$(DOCKER_COMPOSE_CONNECT) down 2>/dev/null || true
	@echo "$(YELLOW)Запускаем инфраструктуру + Kafka Connect (Python consumer ОТКЛЮЧЁН)...$(NC)"
	KAFKA_CONSUMER_ENABLED=false $(DOCKER_COMPOSE_CONNECT) up -d --build
	@echo "$(YELLOW)Настраиваем коннекторы...$(NC)"
	@bash scripts/setup_connect.sh

down-pipeline-connect: ## [Benchmark] Остановить Kafka Connect
	@echo "$(YELLOW)Останавливаем Kafka Connect...$(NC)"
	$(DOCKER_COMPOSE_CONNECT) down
	@echo "$(GREEN)✅ Kafka Connect остановлен$(NC)"

up-pipeline-engine: ## [Benchmark] Запустить решение C: Kafka Table Engine
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  Pipeline C: Kafka Table Engine$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(YELLOW)Останавливаем текущие сервисы...$(NC)"
	$(DOCKER_COMPOSE) down 2>/dev/null || true
	@echo "$(YELLOW)Запускаем инфраструктуру (Python consumer ОТКЛЮЧЁН)...$(NC)"
	KAFKA_CONSUMER_ENABLED=false $(DOCKER_COMPOSE) up -d
	@sleep 5
	@echo "$(YELLOW)Создаём Kafka Engine таблицы в ClickHouse...$(NC)"
	@bash scripts/setup_engine.sh

down-pipeline-engine: ## [Benchmark] Остановить Kafka Table Engine
	@echo "$(YELLOW)Удаляем Kafka Engine таблицы...$(NC)"
	@bash scripts/teardown_engine.sh
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Kafka Table Engine остановлен$(NC)"

connect-status: ## [Benchmark] Статус коннекторов Kafka Connect
	@echo "$(BLUE)Статус коннекторов:$(NC)"
	@curl -sf http://localhost:8083/connectors | python3 -m json.tool 2>/dev/null || echo "$(RED)Kafka Connect недоступен$(NC)"
	@echo ""
	@for c in clickhouse-sink-users clickhouse-sink-tracks clickhouse-sink-events; do \
		echo "$(YELLOW)$$c:$(NC)"; \
		curl -sf "http://localhost:8083/connectors/$$c/status" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"  connector: {d['connector']['state']}\"); [print(f\"  task {t['id']}: {t['state']}\") for t in d.get('tasks',[])]" 2>/dev/null || echo "  $(RED)недоступен$(NC)"; \
	done

connect-lag: ## [Benchmark] Consumer lag для Kafka Connect
	@echo "$(BLUE)Consumer lag (connect-clickhouse):$(NC)"
	@docker exec music_recommend_kafka kafka-consumer-groups \
		--bootstrap-server localhost:29092 \
		--describe --group connect-clickhouse 2>/dev/null || echo "$(RED)Не удалось получить lag$(NC)"

logs-connect: ## [Benchmark] Логи Kafka Connect
	$(DOCKER_COMPOSE_CONNECT) logs -f kafka-connect

pipeline-verify: ## [Benchmark] Проверка количества записей в таблицах
	@echo "$(BLUE)Количество записей в таблицах:$(NC)"
	@docker exec music_recommend_clickhouse clickhouse-client -q "\
		SELECT 'users' AS tbl, count() AS rows FROM music_recommend.users \
		UNION ALL SELECT 'tracks', count() FROM music_recommend.tracks \
		UNION ALL SELECT 'interactions', count() FROM music_recommend.user_track_interactions \
		FORMAT Pretty"

# ═══════════════════════════════════════════════
# 🐳 Docker Compose команды
# ═══════════════════════════════════════════════

ps: ## Показать статус контейнеров
	@echo "$(BLUE)🐳 Статус контейнеров:$(NC)"
	@$(DOCKER_COMPOSE) ps

setup: ## Полная настройка проекта: сервисы + БД + данные + индексы + тесты + диагностика
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  🚀 Полная настройка проекта$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)Шаг 1/7: Запуск сервисов...$(NC)"
	$(MAKE) up
	@echo ""
	@echo "$(YELLOW)Шаг 2/7: Создание таблиц...$(NC)"
	$(MAKE) db-init
	@echo ""
	@echo "$(YELLOW)Шаг 3/7: Генерация тестовых данных (~10M записей)...$(NC)"
	$(MAKE) load-test-data-generate
	@echo ""
	@echo "$(YELLOW)Шаг 4/7: Добавление индексов...$(NC)"
	$(MAKE) db-indexes
	@echo ""
	@echo "$(YELLOW)Шаг 5/7: Оптимизация таблиц (применение индексов)...$(NC)"
	$(MAKE) db-optimize
	@echo ""
	@echo "$(YELLOW)Шаг 6/7: Запуск тестов...$(NC)"
	$(MAKE) test
	@echo ""
	@echo "$(YELLOW)Шаг 7/7: Диагностика системы...$(NC)"
	$(MAKE) diagnose
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  ✅ Проект готов к работе и тестированию!$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)Следующие шаги:$(NC)"
	@echo "  make load-test-post-quick    — быстрый нагрузочный тест (1 мин)"
	@echo "  make load-test-post          — полный нагрузочный тест (8 мин)"
	@echo "  make measure-insert-lag      — измерение лага вставки"
	@echo ""

up: ## Запустить все сервисы (включая API)
	@echo "$(GREEN)🚀 Запуск всех сервисов...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@sleep 3
	@echo "$(GREEN)✅ Сервисы запущены!$(NC)"
	@echo ""
	$(MAKE) urls

down: ## Остановить все сервисы
	@echo "$(RED)🛑 Остановка всех сервисов...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Сервисы остановлены$(NC)"


logs: ## Показать логи всех сервисов
	$(DOCKER_COMPOSE) logs -f

logs-api: ## Показать логи API
	$(DOCKER_COMPOSE) logs -f api

logs-clickhouse: ## Показать логи ClickHouse
	$(DOCKER_COMPOSE) logs -f clickhouse

logs-kafka: ## Показать логи Kafka
	$(DOCKER_COMPOSE) logs -f kafka

logs-redis: ## Показать логи Redis
	$(DOCKER_COMPOSE) logs -f redis

logs-errors: ## Показать только ошибки из логов API [[memory:7077763]]
	@echo "$(RED)🔍 Поиск ошибок в логах API...$(NC)"
	@$(DOCKER_COMPOSE) logs api 2>&1 | grep -i -E "(error|exception|traceback|failed)" --color=always | tail -50

build: ## Собрать Docker образы
	@echo "$(BLUE)🔨 Сборка Docker образов...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✅ Образы собраны$(NC)"

rebuild: ## Пересобрать и перезапустить все сервисы
	@echo "$(BLUE)🔄 Пересборка и перезапуск сервисов...$(NC)"
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) build
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Сервисы пересобраны и перезапущены$(NC)"

shell: ## Открыть shell в API контейнере
	@echo "$(BLUE)🐚 Открытие shell в API контейнере...$(NC)"
	docker exec -it music_recommend_api /bin/bash

status: ## Показать статус всех сервисов и базовую информацию
	@echo "$(BLUE)📊 Статус системы:$(NC)"
	make ps
	@echo "$(YELLOW)API Health:$(NC)"
	@make health 2>/dev/null || echo "$(RED)  ❌ API недоступен$(NC)"

# ═══════════════════════════════════════════════
# 🗄️ База данных
# ═══════════════════════════════════════════════

db-init: ## Создать таблицы в ClickHouse (безопасно, идемпотентно)
	# @bash scripts/safe_db_init.sh
	python scripts/seed_data.py

db-indexes: ## Добавить индексы для оптимизации запросов (безопасно)
	@echo "$(BLUE)📊 Добавление индексов для оптимизации...$(NC)"
	@bash scripts/safe_add_indexes.sh

db-optimize: ## Оптимизировать таблицы (применить индексы к существующим данным)
	@echo "$(BLUE)📊 Оптимизация таблиц...$(NC)"
	@docker exec music_recommend_clickhouse clickhouse-client --query "OPTIMIZE TABLE music_recommend.user_track_matrix FINAL" || true
	@docker exec music_recommend_clickhouse clickhouse-client --query "OPTIMIZE TABLE music_recommend.user_track_interactions FINAL" || true
	@docker exec music_recommend_clickhouse clickhouse-client --query "OPTIMIZE TABLE music_recommend.user_recommendations FINAL" || true
	@echo "$(GREEN)✅ Таблицы оптимизированы$(NC)"

db-reset: ## Пересоздать ClickHouse контейнер и таблицы
	@echo "$(YELLOW)⚠️ Пересоздание ClickHouse (данные будут удалены)...$(NC)"
	bash scripts/docker-reset-clickhouse.sh

fix-clickhouse: ## Восстановить ClickHouse после проблем с конфигурацией
	@echo "$(YELLOW)🔧 Восстановление ClickHouse...$(NC)"
	@bash scripts/fix_clickhouse.sh

diagnose-performance: ## Диагностика производительности (ClickHouse, индексы, медленные запросы)
	@echo "$(BLUE)🔍 Диагностика производительности...$(NC)"
	@bash scripts/diagnose_performance.sh

db-shell: ## Открыть clickhouse-client
	docker exec -it music_recommend_clickhouse clickhouse-client

db-tables: ## Показать таблицы в БД
	@echo "$(BLUE)📋 Таблицы в базе данных:$(NC)"
	@docker exec music_recommend_clickhouse clickhouse-client -q "SHOW TABLES FROM music_recommend"

db-stats: ## Показать статистику по таблицам
	@echo "$(BLUE)📊 Статистика таблиц:$(NC)"
	@docker exec music_recommend_clickhouse clickhouse-client -q "\
		SELECT \
			table, \
			formatReadableSize(total_bytes) AS size, \
			formatReadableQuantity(total_rows) AS rows \
		FROM system.tables \
		WHERE database = 'music_recommend' \
		FORMAT Pretty"

# ═══════════════════════════════════════════════
# 🧪 Тестирование
# ═══════════════════════════════════════════════

test: ## Запустить все тесты
	@echo "$(BLUE)🧪 Запуск тестов...$(NC)"
	pytest -v  # -s

test-clickhouse: ## Запустить только тесты ClickHouse
	pytest tests/clickhouse/ -s

test-kafka: ## Запустить все тесты Kafka (требует запущенный Kafka)
	pytest tests/kafka/ -s

test-api: 
	pytest tests/api/ -s

test-cache: 
	pytest tests/cache/ -s

test-ttl-optimization: ## Тест оптимизации TTL для повышения hit rate
	@echo "$(BLUE)🕐 Тест оптимизации TTL...$(NC)"
	@echo "$(YELLOW)Тестируем разные значения TTL (1ч, 2ч, 4ч)$(NC)"
	@python tests/simple_ttl_test.py

test-cache-warmup: ## Тест эффективности прогрева кэша
	@echo "$(BLUE)🔥 Тест прогрева кэша...$(NC)"
	@echo "$(YELLOW)Проверяем работу прогрева кэша$(NC)"
	@python tests/simple_warmup_test.py

test-api-health: ## Проверка здоровья API
	@echo "$(BLUE)🏥 Проверка API...$(NC)"
	@python tests/api/test_api_health.py

# ═══════════════════════════════════════════════
# ⚡ Нагрузочное тестирование (k6)
# ═══════════════════════════════════════════════

load-test-install: ## Проверка установки k6
	@echo "$(BLUE)🔍 Проверка k6...$(NC)"
	@if command -v k6 > /dev/null 2>&1; then \
		echo "$(GREEN)✅ k6 установлен: $$(k6 version | head -n1)$(NC)"; \
	else \
		echo "$(RED)❌ k6 не установлен$(NC)"; \
		echo "$(YELLOW)Установите k6:$(NC)"; \
		echo "  macOS:   brew install k6"; \
		echo "  Linux:   https://k6.io/docs/getting-started/installation/"; \
		exit 1; \
	fi

load-test-data-generate: ## Сгенерировать 1M записей для нагрузочного тестирования
	@echo "$(BLUE)🌱 Генерация N записей для нагрузочных тестов...$(NC)"
	@echo "$(YELLOW)⚠️ Это займет ~5 минут. Убедитесь, что сервисы запущены!$(NC)"
	@echo ""
	python load_tests/generate_test_data.py
	@echo ""
	@echo "$(GREEN)✅ Данные сгенерированы!$(NC)"
	@echo "$(BLUE)💡 Проверьте статистику: make db-stats$(NC)"

load-test-diagnostics: ## Диагностика производительности (1 минута, 10 VUs)
	@echo "$(BLUE)🔍 Диагностика производительности API...$(NC)"
	@echo "$(YELLOW)Длительность: 1 минута | Без thresholds - только метрики$(NC)"
	k6 run load_tests/k6_diagnostics_test.js

load-test-quick: ## Быстрая проверка API (30 секунд)
	@echo "$(BLUE)⚡ Быстрая проверка API...$(NC)"
	k6 run load_tests/quick_test.js

load-test-smoke: ## Smoke test - проверка работоспособности API (~2 минуты)
	@echo "$(BLUE)🔥 Запуск smoke теста...$(NC)"
	@echo "$(YELLOW)Длительность: ~2 минуты$(NC)"
	k6 run load_tests/k6_smoke_test.js

load-test-basic: ## Базовый нагрузочный тест (~15 минут)
	@echo "$(BLUE)📊 Запуск базового нагрузочного теста...$(NC)"
	@echo "$(YELLOW)Длительность: ~15 минут$(NC)"
	k6 run load_tests/k6_basic_load_test.js

load-test-spike: ## Тест пиковой нагрузки 200 VUs (~2 минуты)
	@echo "$(BLUE)⚡ Запуск теста пиковой нагрузки (200 VUs)...$(NC)"
	@echo "$(YELLOW)Длительность: ~2 минуты$(NC)"
	k6 run load_tests/k6_spike_test.js

load-test-spike-extreme: ## Экстремальный spike test 500 VUs (без thresholds)
	@echo "$(BLUE)💥 Запуск ЭКСТРЕМАЛЬНОГО spike теста (500 VUs)...$(NC)"
	@echo "$(YELLOW)Длительность: ~1 минута | БЕЗ строгих критериев прохождения$(NC)"
	k6 run load_tests/k6_spike_test_extreme.js

load-test-stress: ## Стресс-тест (~30 минут)
	@echo "$(BLUE)💪 Запуск стресс-теста...$(NC)"
	@echo "$(YELLOW)Длительность: ~30 минут$(NC)"
	k6 run load_tests/k6_stress_test.js

load-test-soak: ## Тест на выносливость (~70 минут)
	@echo "$(BLUE)🕐 Запуск теста на выносливость...$(NC)"
	@echo "$(YELLOW)Длительность: ~70 минут$(NC)"
	k6 run load_tests/k6_soak_test.js

load-test-recommendations: ## Детальный анализ производительности рекомендаций (~11 минут)
	@echo "$(BLUE)📊 Запуск детального анализа производительности рекомендаций...$(NC)"
	@echo "$(YELLOW)Длительность: ~11 минут | Детальные метрики: Redis, ClickHouse, Алгоритм$(NC)"
	@echo "$(GREEN)Этот тест собирает подробную статистику о времени выполнения каждого компонента$(NC)"
	k6 run load_tests/k6_recommendations_performance_test.js


load-test-post: ## Нагрузочный тест POST запросов (создание пользователей, треков, событий, рекомендации)
	@echo "$(BLUE)📝 Запуск нагрузочного теста POST запросов...$(NC)"
	@echo "$(YELLOW)Тестирует: POST /users, POST /tracks, POST /events, POST /recommendations$(NC)"
	@echo "$(YELLOW)Длительность: ~11 минут | VUs: 100 (можно изменить через VUS=50 DURATION=5m)$(NC)"
	@echo "$(GREEN)Пример: make load-test-post VUS=50 DURATION=5m$(NC)"
	k6 run load_tests/k6_post_load_test.js

load-test-post-quick: ## Быстрый тест POST запросов (1 минута, 10 VUs)
	@echo "$(BLUE)⚡ Быстрый тест POST запросов...$(NC)"
	@echo "$(YELLOW)Длительность: 1 минута | VUs: 10$(NC)"
	k6 run load_tests/k6_post_load_test.js --vus 10 --duration 1m

load-test-events-post: ## Тест POST /events (отдельный эндпоинт)
	@echo "$(BLUE)📝 Запуск теста POST /events...$(NC)"
	k6 run load_tests/k6_test_events_post.js

load-test-tracks-post: ## Тест POST /tracks (отдельный эндпоинт)
	@echo "$(BLUE)📝 Запуск теста POST /tracks...$(NC)"
	k6 run load_tests/k6_test_tracks_post.js

load-test-users-post: ## Тест POST /users (отдельный эндпоинт)
	@echo "$(BLUE)📝 Запуск теста POST /users...$(NC)"
	k6 run load_tests/k6_test_users_post.js

load-test-recommendations-post: ## Тест POST /recommendations (отдельный эндпоинт)
	@echo "$(BLUE)📝 Запуск теста POST /recommendations...$(NC)"
	k6 run load_tests/k6_test_recommendations_post.js

measure-insert-lag: ## Измерить лаг вставки в ClickHouse (от POST запроса до БД) - использует k6
	@echo "$(BLUE)⏱️  Измерение лага вставки в ClickHouse...$(NC)"
	@echo "$(YELLOW)Это измеряет время от создания записи через POST до фактической вставки в ClickHouse$(NC)"
	@echo "$(BLUE)================================================================================$(NC)"
	@echo "$(YELLOW)Используется k6 для более надежного измерения$(NC)"
	@echo ""
	@NUM_REQUESTS_VAL=$${NUM_REQUESTS:-50}; \
	CHECK_INTERVAL_VAL=$${CHECK_INTERVAL:-0.5}; \
	MAX_WAIT_TIME_VAL=$${MAX_WAIT_TIME:-60}; \
	k6 run \
		--env NUM_REQUESTS=$$NUM_REQUESTS_VAL \
		--env CHECK_INTERVAL=$$CHECK_INTERVAL_VAL \
		--env MAX_WAIT_TIME=$$MAX_WAIT_TIME_VAL \
		--env CLICKHOUSE_URL=http://localhost:8123 \
		--env CLICKHOUSE_DATABASE=music_recommend \
		load_tests/k6_measure_insert_lag.js

measure-insert-lag-python: ## Измерить лаг вставки в ClickHouse (старый Python скрипт)
	@echo "$(BLUE)⏱️  Измерение лага вставки в ClickHouse (Python)...$(NC)"
	@echo "$(YELLOW)Это измеряет время от создания записи в k6 до фактической вставки в ClickHouse$(NC)"
	@echo "$(BLUE)================================================================================$(NC)"
	python3 scripts/measure_insert_lag.py $(NUM_REQUESTS)

load-test-results: ## Показать результаты последних тестов
	@echo "$(BLUE)📊 Результаты последних нагрузочных тестов:$(NC)"
	@echo ""
	@if [ -d "load_tests/results" ]; then \
		ls -lht load_tests/results/*.json 2>/dev/null | head -5 || echo "$(YELLOW)Нет результатов. Запустите тесты!$(NC)"; \
	else \
		echo "$(YELLOW)Директория results не существует. Запустите тесты!$(NC)"; \
	fi

# ═══════════════════════════════════════════════
# 📊 Данные и проверки
# ═══════════════════════════════════════════════

health: ## Проверить health check API
	@echo "$(BLUE)🏥 Проверка health check...$(NC)"
	@curl -s http://localhost:8000/api/v1/health | python -m json.tool 2>/dev/null || echo "$(RED)❌ API недоступен. Проверьте: make ps$(NC)"

check-services: ## Проверить доступность всех сервисов
	@bash scripts/check_services.sh

diagnose-system: ## Комплексная диагностика системы (Docker, Kafka, ClickHouse, Redis, API, логи)
	@echo "$(BLUE)🔍 Запуск комплексной диагностики системы...$(NC)"
	@bash scripts/diagnose_system.sh

diagnose: ## Полная диагностика системы (API, БД, данные)
	@echo "$(BLUE)🔍 Диагностика системы...$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)1️⃣  Статус контейнеров:$(NC)"
	make ps
	@echo "$(YELLOW)2️⃣  Проверка API:$(NC)"
	@if curl -s http://localhost:8000/ > /dev/null 2>&1; then \
		echo "$(GREEN)✅ API доступен на http://localhost:8000$(NC)"; \
	else \
		echo "$(RED)❌ API недоступен!$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW)3️⃣  Проверка таблиц в БД:$(NC)"
	@make db-tables
	@echo ""
	@echo "$(YELLOW)4️⃣  Количество данных в таблицах:$(NC)"
	@docker exec music_recommend_clickhouse clickhouse-client -q "SELECT 'users', count() FROM music_recommend.users UNION ALL SELECT 'tracks', count() FROM music_recommend.tracks UNION ALL SELECT 'interactions', count() FROM music_recommend.user_track_interactions" 2>/dev/null || echo "   $(RED)Ошибка подключения к БД$(NC)"
	@echo ""
	@echo "$(YELLOW)5️⃣  Последние ошибки API (если есть):$(NC)"
	@$(DOCKER_COMPOSE) logs api 2>&1 | grep -i -E "(error|exception)" | tail -10 || echo "   $(GREEN)Нет ошибок$(NC)"
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"

diagnose-cache: ## Диагностика кэширования Redis
	@echo "$(BLUE)🔍 Диагностика кэширования...$(NC)"
	@python tests/cache/test_cache_api.py
	@python tests/cache/test_cache_simple.py
	@echo "$(BLUE)🎯 Тест реального hit rate...$(NC)"
	@echo "$(YELLOW)Проверяем производительность в реальных условиях$(NC)"
	@python tests/cache/test_real_hitrate.py

diagnose-cache-curl: ## Диагностика кэширования через curl
	@echo "$(BLUE)🔍 Диагностика кэширования (curl)...$(NC)"
	@echo ""
	@echo "$(YELLOW)1️⃣  Статус кэша:$(NC)"
	@curl -s http://localhost:8000/api/v1/debug/cache/status | python -m json.tool 2>/dev/null || curl -s http://localhost:8000/api/v1/debug/cache/status
	@echo ""
	@echo "$(YELLOW)2️⃣  Ключи кэша:$(NC)"
	@curl -s http://localhost:8000/api/v1/debug/cache/keys | python -m json.tool 2>/dev/null || curl -s http://localhost:8000/api/v1/debug/cache/keys
	@echo ""
	@echo "$(YELLOW)3️⃣  Тест операций:$(NC)"
	@curl -s -X POST http://localhost:8000/api/v1/debug/cache/test | python -m json.tool 2>/dev/null || curl -s -X POST http://localhost:8000/api/v1/debug/cache/test
	@echo ""
	@echo "$(YELLOW)4️⃣  Симуляция hit rate:$(NC)"
	@curl -s -X POST http://localhost:8000/api/v1/debug/cache/simulate-hitrate | python -m json.tool 2>/dev/null || curl -s -X POST http://localhost:8000/api/v1/debug/cache/simulate-hitrate


# ═══════════════════════════════════════════════
# 🧹 Очистка
# ═══════════════════════════════════════════════

clean: ## Очистить кэши и временные файлы
	@echo "$(BLUE)🧹 Очистка...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "$(GREEN)✅ Очистка завершена$(NC)"

clean-all: clean down ## Полная очистка (включая контейнеры и volumes)
	@echo "$(YELLOW)⚠️  Удаление volumes...$(NC)"
	$(DOCKER_COMPOSE) down -v
	docker volume rm music_recommend_clickhouse_data music_recommend_redis_data 2>/dev/null || true
	@echo "$(GREEN)✅ Полная очистка завершена$(NC)"

# ═══════════════════════════════════════════════
# 🎨 Качество кода
# ═══════════════════════════════════════════════

lint: ## Проверить код линтерами (flake8)
	@echo "$(BLUE)🔍 Проверка кода линтерами...$(NC)"
	@echo ""
	@if command -v flake8 > /dev/null 2>&1; then \
		echo "$(YELLOW)Запуск flake8...$(NC)"; \
		flake8 app/ tests/ || true; \
		echo ""; \
	else \
		echo "$(RED)❌ flake8 не установлен$(NC)"; \
		echo "$(YELLOW)Установите: make lint-install$(NC)"; \
		echo ""; \
	fi
	@if command -v black > /dev/null 2>&1; then \
		echo "$(YELLOW)Проверка форматирования (black)...$(NC)"; \
		black --check app/ tests/ 2>&1 | head -20 || true; \
		echo ""; \
	else \
		echo "$(RED)❌ black не установлен$(NC)"; \
		echo "$(YELLOW)Установите: make lint-install$(NC)"; \
		echo ""; \
	fi
	@echo "$(GREEN)✅ Проверка завершена$(NC)"
	@echo "$(YELLOW)💡 Исправить форматирование: make format$(NC)"

lint-install: ## Установить линтеры
	@echo "$(BLUE)📦 Установка линтеров...$(NC)"
	pip install flake8 black mypy pylint
	@echo "$(GREEN)✅ Линтеры установлены$(NC)"

format: ## Отформатировать код (black + удаление trailing whitespace)
	@echo "$(BLUE)🎨 Форматирование кода...$(NC)"
	@echo ""
	@echo "$(YELLOW)1️⃣  Удаление trailing whitespace...$(NC)"
	@find app/ tests/ -name "*.py" -type f -exec sed -i 's/[[:space:]]*$$//' {} + 2>/dev/null || \
		find app/ tests/ -name "*.py" -type f -exec sed -i '' 's/[[:space:]]*$$//' {} + 2>/dev/null || \
		echo "$(YELLOW)⚠️  sed недоступен, пропускаем удаление trailing whitespace$(NC)"
	@echo "$(GREEN)   ✅ Trailing whitespace удалён$(NC)"
	@echo ""
	@echo "$(YELLOW)2️⃣  Форматирование с black...$(NC)"
	@if command -v black > /dev/null 2>&1; then \
		black app/ tests/; \
		echo "$(GREEN)   ✅ Код отформатирован с black$(NC)"; \
	else \
		echo "$(RED)   ❌ black не установлен$(NC)"; \
		echo "$(YELLOW)   Установите: make lint-install$(NC)"; \
	fi
	@echo ""
	@echo "$(GREEN)✅ Форматирование завершено!$(NC)"

# ═══════════════════════════════════════════════
# 📖 Документация и информация
# ═══════════════════════════════════════════════

urls: ## Показать URLs
	@echo "$(YELLOW)📍 URLs:$(NC)"
	@echo "   API:        http://localhost:8000"
	@echo "   Swagger:    http://localhost:8000/docs"
	@echo "   ReDoc:      http://localhost:8000/redoc"
	@echo "   ClickHouse: http://localhost:8123"
	@echo "   Zookeeper:  localhost:2181"
	@echo "   Kafka:      localhost:9092"
	@echo "   Redis:      localhost:6379"
	@echo ""

info: ## Показать информацию о проекте
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  🎵 Music Recommendation System$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo ""
	make urls
	@echo "$(YELLOW)🐳 Статус контейнеров:$(NC)"
	@$(DOCKER_COMPOSE) ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null | grep -E "(NAME|music_recommend)" || echo "   Контейнеры не запущены. Запустите: make up"
	@echo ""
	@echo "$(YELLOW)📂 Важные файлы:$(NC)"
	@echo "   .env              - Переменные окружения"
	@echo "   Makefile          - Команды управления"
	@echo "   docker-compose.yml - Docker конфигурация"
	@echo "   app/config.py     - Настройки приложения"
	@echo ""
	@echo "$(YELLOW)🔧 Быстрые команды:$(NC)"
	@echo "   make quickstart      - Запустить всё (backend + UI)"
	@echo "   make diagnose        - Диагностика проблем"
	@echo "   make logs-errors     - Показать ошибки"
	@echo "   make health          - Проверить API"
	@echo "   make help            - Все команды"
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"

