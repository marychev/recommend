# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Music Recommendation System — рекомендательная система музыкальных треков. Python/FastAPI API + ClickHouse (OLAP) + Kafka (event streaming) + Redis (cache). Collaborative Filtering алгоритм с fallback на популярные треки.

## Commands

### Run & Build
```bash
make up                    # запустить все сервисы (Docker)
make down                  # остановить
make rebuild               # пересобрать и перезапустить
make setup                 # полная настройка: сервисы + БД + данные + тесты + диагностика
```

### Testing
```bash
make test                  # все тесты (pytest -v)
pytest tests/kafka/ -s     # тесты одного модуля
pytest tests/kafka/test_kafka_producer.py -s         # один файл
pytest tests/kafka/test_kafka_producer.py::test_name -s  # один тест
make test-clickhouse       # только ClickHouse тесты
make test-kafka            # только Kafka тесты
make test-api              # только API тесты
make test-cache            # только cache тесты
```

### Linting & Formatting
```bash
make lint                  # flake8 + black --check
make format                # black + trailing whitespace cleanup
make lint-install           # установить flake8, black, mypy, pylint
```

### Load Testing (k6)
```bash
make load-test-post-quick  # быстрый POST тест (1 мин, 10 VUs)
make load-test-post        # полный POST тест (11 мин, 100 VUs)
make measure-insert-lag    # измерение лага вставки Kafka→ClickHouse
make load-test-spike       # spike test 200 VUs
```

### Database
```bash
make db-init               # создать таблицы (идемпотентно)
make db-shell              # clickhouse-client интерактивный
make db-stats              # статистика таблиц (размер, строки)
make db-reset              # пересоздать ClickHouse (данные удалятся!)
```

### Pipeline Benchmark (ROADMAP.md)
```bash
make up                        # решение A: Python Consumer (текущее)
make up-pipeline-connect       # решение B: Kafka Connect Sink
make up-pipeline-engine        # решение C: Kafka Table Engine
make connect-status            # статус коннекторов
make pipeline-verify           # сравнение row count
```

### Diagnostics
```bash
make diagnose              # полная диагностика (контейнеры, API, БД, ошибки)
make logs-api              # логи API
make logs-errors           # только ошибки из логов
make health                # health check API
```

## Architecture

### Data Flow
```
Client → FastAPI API → Kafka Producer → Kafka Broker
                                            ↓
ClickHouse ← BatchBuffer ← DataHandler ← Multi-Consumer (aiokafka)
                                            ↓
                                        Redis (metrics update)
```

### Key Layers

**API Layer** (`app/routers/`): FastAPI endpoints. Роутеры: health, users, tracks, events, recommendations, cache_debug. Все под префиксом `/api/v1`.

**Kafka Pipeline** (`app/kafka/`):
- `producer.py` — сериализация в JSON, GZIP, partition by user_id
- `multi_consumer.py` — 3 параллельных консьюмера (users, tracks, events) с exponential backoff
- `data_handler.py` — обработка сообщений + **Redis side-effects** при events (update_analytics_metrics)
- `event_queue.py` → `EventQueue` — батчинг 100 событий / 1.5s перед Kafka

**ClickHouse** (`app/db/`):
- `clickhouse.py` — async HTTP клиент (aiochclient), встроенный `BatchBuffer` (1000 записей / 5s flush)
- `clickhouse_schemas.sql` — DDL таблиц, MV, индексы. Монтируется как init.sql
- SQL injection protection через whitelist валидацию table/field names

**Batching** (`app/utils/batch_buffer.py`): Универсальный async буфер. Используется и для Kafka→ClickHouse, и для прямых вставок. Error recovery — возврат записей в буфер при ошибке.

**ML** (`app/services/recommendation_service.py`): Collaborative Filtering через ClickHouse — user_track_matrix (MV), cosine similarity. Fallback: популярные треки (cold start).

**Cache** (`app/services/cache.py`, `cache_redis_client.py`): Redis кэш рекомендаций. TTL 1-4 часа. Прогрев при старте в lifespan.

### Startup (`app/utils/lifespan.py`)
Порядок: ClickHouse → Redis → Kafka Producer → CH periodic flush → EventQueue → Multi-Consumer → Cache warmup. Флаг `KAFKA_CONSUMER_ENABLED` отключает consumer (для pipeline benchmark).

### Configuration
Все настройки через `app/config.py` (Pydantic Settings, env file `.env`, case insensitive). Docker-compose передаёт env vars в api сервис.

### Testing Patterns
- `asyncio_mode = auto` в pytest.ini — все async тесты автоматически
- Тесты организованы по модулям: `tests/api/`, `tests/kafka/`, `tests/clickhouse/`, `tests/cache/`
- Kafka и ClickHouse тесты требуют запущенных сервисов (`make up`)
- Fixtures в `conftest.py` каждого модуля

### Docker Services
ClickHouse (:8123/:9000), Kafka (:9092, internal :29092), Zookeeper (:2181), Redis (:6379), API (:8000). Все в сети `music_recommend_network`.

## Language

Проект на русском языке (комментарии, документация, логи). Код и переменные на английском.
