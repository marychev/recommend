.PHONY: help up down restart logs logs-api logs-clickhouse status clean test seed health check-services build rebuild ps stop-api run-api shell db-init db-reset install lint lint-install format ui ui-open ui-stop quickstart-full

# Цвета для вывода
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Показать справку по доступным командам
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  🎵 Music Recommendation System - Makefile$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"

# ═══════════════════════════════════════════════
# 🐳 Docker Compose команды
# ═══════════════════════════════════════════════

up: ## Запустить все сервисы (включая API)
	@echo "$(GREEN)🚀 Запуск всех сервисов...$(NC)"
	docker compose up -d
	@sleep 3
	@echo "$(GREEN)✅ Сервисы запущены!$(NC)"
	@echo ""
	@echo "$(BLUE)🌐 API доступен на: http://localhost:8000$(NC)"
	@echo "$(BLUE)📚 Swagger документация: http://localhost:8000/docs$(NC)"
	@echo "$(BLUE)📖 ReDoc документация: http://localhost:8000/redoc$(NC)"
	@echo ""
	@echo "$(YELLOW)💡 Проверьте статус: make ps$(NC)"
	@echo "$(YELLOW)💡 Посмотрите логи: make logs-api$(NC)"

down: ## Остановить все сервисы
	@echo "$(RED)🛑 Остановка всех сервисов...$(NC)"
	docker compose down
	@echo "$(GREEN)✅ Сервисы остановлены$(NC)"

restart: down up ## Перезапустить все сервисы

logs: ## Показать логи всех сервисов
	docker compose logs -f

logs-api: ## Показать логи API
	docker compose logs -f api

logs-clickhouse: ## Показать логи ClickHouse
	docker compose logs -f clickhouse

logs-kafka: ## Показать логи Kafka
	docker compose logs -f kafka

logs-redis: ## Показать логи Redis
	docker compose logs -f redis

logs-errors: ## Показать только ошибки из логов API [[memory:7077763]]
	@echo "$(RED)🔍 Поиск ошибок в логах API...$(NC)"
	@docker compose logs api 2>&1 | grep -i -E "(error|exception|traceback|failed)" --color=always | tail -50

ps: ## Показать статус контейнеров
	@echo "$(BLUE)🐳 Статус контейнеров:$(NC)"
	@docker compose ps

build: ## Собрать Docker образы
	@echo "$(BLUE)🔨 Сборка Docker образов...$(NC)"
	docker compose build
	@echo "$(GREEN)✅ Образы собраны$(NC)"

# ═══════════════════════════════════════════════
# 🔧 Управление отдельными сервисами
# ═══════════════════════════════════════════════

up-clickhouse: ## Запустить только ClickHouse
	docker compose up -d clickhouse

up-kafka: ## Запустить только Kafka и Zookeeper
	docker compose up -d zookeeper kafka

up-redis: ## Запустить только Redis
	docker compose up -d redis

up-api: ## Запустить только API контейнер
	@echo "$(GREEN)🚀 Запуск API контейнера...$(NC)"
	docker compose up -d api
	@sleep 3
	@echo "$(GREEN)✅ API контейнер запущен!$(NC)"
	@echo "$(BLUE)🌐 API: http://localhost:8000$(NC)"
	@echo "$(BLUE)📚 Docs: http://localhost:8000/docs$(NC)"

# ═══════════════════════════════════════════════
# 💻 Локальная разработка
# ═══════════════════════════════════════════════

install: ## Установить зависимости Python
	@echo "$(BLUE)📦 Установка зависимостей...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✅ Зависимости установлены$(NC)"

run-api: ## Запустить API локально (не в Docker)
	@echo "$(GREEN)🚀 Запуск API локально...$(NC)"
	fuser -k 8000/tcp
	python -m app.main

stop-api: ## Остановить локально запущенный API
	@echo "$(RED)🛑 Остановка API...$(NC)"
	pkill -f "python -m app.main" || pkill -f "uvicorn app.main" || echo "API не запущен"

# ═══════════════════════════════════════════════
# 🗄️ База данных
# ═══════════════════════════════════════════════

db-init: ## Создать таблицы в ClickHouse (безопасно, идемпотентно)
	@bash scripts/safe_db_init.sh

db-reset: ## Пересоздать ClickHouse контейнер и таблицы
	@echo "$(YELLOW)⚠️  Пересоздание ClickHouse (данные будут удалены)...$(NC)"
	bash scripts/docker-reset-clickhouse.sh

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
	pytest -v

test-clickhouse: ## Запустить только тесты ClickHouse
	pytest tests/clickhouse/ -v

test-watch: ## Запустить тесты в режиме watch
	pytest-watch

# ═══════════════════════════════════════════════
# 📊 Данные и проверки
# ═══════════════════════════════════════════════

seed: ## Сгенерировать тестовые данные (10,000 записей)
	@echo "$(BLUE)🌱 Генерация тестовых данных...$(NC)"
	@echo "$(YELLOW)Это может занять ~1-2 минуты...$(NC)"
	python scripts/seed_data.py
	@echo "$(GREEN)✅ Данные созданы!$(NC)"
	@echo "$(BLUE)💡 Проверьте: make db-stats$(NC)"

seed-quick: ## Быстрая генерация минимальных тестовых данных
	@echo "$(BLUE)🌱 Генерация минимальных тестовых данных...$(NC)"
	@docker exec music_recommend_clickhouse clickhouse-client -q "\
		INSERT INTO music_recommend.users (user_id, username, email, age, country) VALUES \
		(1, 'testuser1', 'test1@example.com', 25, 'US'), \
		(2, 'testuser2', 'test2@example.com', 30, 'UK'), \
		(3, 'testuser3', 'test3@example.com', 22, 'CA');"
	@docker exec music_recommend_clickhouse clickhouse-client -q "\
		INSERT INTO music_recommend.tracks (track_id, title, artist, album, genre, duration_seconds, release_year) VALUES \
		(1, 'Test Song 1', 'Test Artist', 'Test Album', 'Rock', 180, 2023), \
		(2, 'Test Song 2', 'Test Artist', 'Test Album', 'Pop', 200, 2023), \
		(3, 'Test Song 3', 'Test Artist 2', 'Album 2', 'Jazz', 240, 2023);"
	@docker exec music_recommend_clickhouse clickhouse-client -q "\
		INSERT INTO music_recommend.user_track_interactions (user_id, track_id, action_type, listen_duration_seconds, timestamp) VALUES \
		(1, 1, 'play', 180, now()), \
		(1, 2, 'like', 200, now()), \
		(2, 1, 'play', 180, now()), \
		(2, 3, 'play', 240, now());"
	@echo "$(GREEN)✅ Минимальные тестовые данные созданы!$(NC)"
	@echo "$(BLUE)📊 Создано: 3 пользователя, 3 трека, 4 взаимодействия$(NC)"

health: ## Проверить health check API
	@echo "$(BLUE)🏥 Проверка health check...$(NC)"
	@curl -s http://localhost:8000/api/v1/health | python -m json.tool 2>/dev/null || echo "$(RED)❌ API недоступен. Проверьте: make ps$(NC)"


check-services: ## Проверить доступность всех сервисов
	@bash scripts/check_services.sh

diagnose: ## Полная диагностика системы (API, БД, данные)
	@echo "$(BLUE)🔍 Диагностика системы...$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)1️⃣  Статус контейнеров:$(NC)"
	@docker compose ps
	@echo ""
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
	@docker compose logs api 2>&1 | grep -i -E "(error|exception)" | tail -10 || echo "   $(GREEN)Нет ошибок$(NC)"
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"

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
	docker compose down -v
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

format: ## Отформатировать код с помощью black
	@echo "$(BLUE)🎨 Форматирование кода...$(NC)"
	@if command -v black > /dev/null 2>&1; then \
		black app/ tests/; \
		echo "$(GREEN)✅ Код отформатирован$(NC)"; \
	else \
		echo "$(RED)❌ black не установлен$(NC)"; \
		echo "$(YELLOW)Установите: make lint-install$(NC)"; \
	fi

# ═══════════════════════════════════════════════
# 🎨 Frontend / UI
# ═══════════════════════════════════════════════

ui: ## Запустить Frontend UI на порту 8080
	@echo "$(GREEN)🎨 Запуск Frontend UI...$(NC)"
	@echo ""
	@echo "$(BLUE)📡 Проверка доступности API...$(NC)"
	@if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then \
		echo "$(GREEN)✅ API доступен на http://localhost:8000$(NC)"; \
	else \
		echo "$(RED)⚠️  API недоступен!$(NC)"; \
		echo "$(YELLOW)   Запустите API: make up-api$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)🌐 Запуск HTTP сервера на порту 8080...$(NC)"
	@cd frontend && python -m http.server 8080 &
	@sleep 2
	@echo ""
	@echo "$(GREEN)✅ Frontend UI запущен!$(NC)"
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)🎨 Откройте в браузере:$(NC)"
	@echo "$(BLUE)   http://localhost:8080$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)💡 Остановить: make ui-stop$(NC)"

ui-open: ## Открыть Frontend UI в браузере
	@echo "$(BLUE)🌐 Открытие Frontend UI...$(NC)"
	@python -m webbrowser http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null || open http://localhost:8080 2>/dev/null || echo "Откройте: http://localhost:8080"

ui-stop: ## Остановить Frontend HTTP сервер
	@echo "$(RED)🛑 Остановка Frontend UI...$(NC)"
	@pkill -f "python -m http.server 8080" || echo "Frontend UI не запущен"
	@echo "$(GREEN)✅ Frontend UI остановлен$(NC)"

# ═══════════════════════════════════════════════
# 📖 Документация и информация
# ═══════════════════════════════════════════════

info: ## Показать информацию о проекте
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  🎵 Music Recommendation System$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)📍 URLs:$(NC)"
	@echo "   Frontend:   http://localhost:8080"
	@echo "   API:        http://localhost:8000"
	@echo "   Swagger:    http://localhost:8000/docs"
	@echo "   ReDoc:      http://localhost:8000/redoc"
	@echo "   ClickHouse: http://localhost:8123"
	@echo "   Redis:      localhost:6379"
	@echo "   Kafka:      localhost:9092"
	@echo ""
	@echo "$(YELLOW)🐳 Статус контейнеров:$(NC)"
	@docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null | grep -E "(NAME|music_recommend)" || echo "   Контейнеры не запущены. Запустите: make up"
	@echo ""
	@echo "$(YELLOW)📂 Важные файлы:$(NC)"
	@echo "   .env              - Переменные окружения"
	@echo "   Makefile          - Команды управления"
	@echo "   docker-compose.yml - Docker конфигурация"
	@echo "   app/config.py     - Настройки приложения"
	@echo ""
	@echo "$(YELLOW)🔧 Быстрые команды:$(NC)"
	@echo "   make quickstart      - Запустить всё (backend + UI)"
	@echo "   make ui              - Запустить только Frontend"
	@echo "   make diagnose        - Диагностика проблем"
	@echo "   make logs-errors     - Показать ошибки"
	@echo "   make seed-quick      - Создать тестовые данные"
	@echo "   make health          - Проверить API"
	@echo "   make help            - Все команды"
	@echo ""
	@echo "$(YELLOW)🆘 Если API возвращает ошибку 500:$(NC)"
	@echo "   1. make diagnose       # Диагностика"
	@echo "   2. make logs-errors    # Смотреть ошибки"
	@echo "   3. make seed-quick     # Создать тестовые данные"
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"

# ═══════════════════════════════════════════════
# 🚀 Быстрый старт
# ═══════════════════════════════════════════════

quickstart: ## Быстрый старт проекта (только backend)
	@echo "$(GREEN)🚀 Быстрый старт Music Recommendation System$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)1️⃣  Остановка старых контейнеров...$(NC)"
	@make down 2>/dev/null || true
	@echo ""
	@echo "$(YELLOW)2️⃣  Проверка/сборка Docker образов...$(NC)"
	@docker compose build 2>&1 | grep -E "(Building|CACHED|FINISHED)" || true
	@echo "$(GREEN)   ✅ Образы готовы$(NC)"
	@echo ""
	@echo "$(YELLOW)3️⃣  Запуск сервисов...$(NC)"
	@make up
	@echo ""
	@echo "$(YELLOW)4️⃣  Ожидание запуска ClickHouse (15 сек)...$(NC)"
	@sleep 15
	@echo ""
	@echo "$(YELLOW)5️⃣  Инициализация базы данных...$(NC)"
	@make db-init
	@echo ""
	@echo "$(YELLOW)6️⃣  Проверка health check...$(NC)"
	@make health
	@echo ""
	@echo "$(GREEN)✅ Готово! Backend запущен!$(NC)"
	@echo ""
	@echo "$(YELLOW)7️⃣  Запуск Frontend UI...$(NC)"
	@make ui
	@sleep 2
	@echo ""
	@echo "$(GREEN)✅ Система полностью запущена!$(NC)"
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)🌐 API:        http://localhost:8000$(NC)"
	@echo "$(BLUE)📚 Swagger:    http://localhost:8000/docs$(NC)"
	@echo "$(BLUE)🎨 Frontend:   http://localhost:8080$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)💡 Остановить UI:      make ui-stop$(NC)"
	@echo "$(YELLOW)💡 Остановить все:     make down$(NC)"

# По умолчанию показываем help
.DEFAULT_GOAL := help

