# Pipeline Benchmark — сравнение Kafka→ClickHouse решений

## Цель

Сравнить 3 подхода доставки данных из Kafka в ClickHouse под разными нагрузками,
используя существующие k6-тесты. Одно решение за раз — прогнал, записал, переключился.

## Решения

| # | Решение | Команда запуска | Описание |
|---|---------|----------------|----------|
| A | **Python Consumer** (текущее) | `make up` | aiokafka + BatchBuffer + HTTP INSERT. Поддерживает Redis side-effects и fallback |
| B | **Kafka Connect Sink** | `make up-pipeline-connect` | ClickHouse Kafka Connect Sink. Отдельный JVM-процесс, exactly-once возможен |
| C | **Kafka Table Engine** | `make up-pipeline-engine` | Встроенный движок ClickHouse. SQL-only, без кода. Нет Redis side-effects |

## Что измеряем

- **Insert lag** — задержка от POST запроса до появления в ClickHouse (`make measure-insert-lag`)
- **Throughput** — сколько записей/сек проходит через пайплайн
- **Потеря данных** — все ли записи дошли (row count сравнение)
- **Ресурсы** — CPU/RAM потребление при нагрузке
- **Поведение под стрессом** — что происходит при spike 200-500 VUs

## Тесты для каждого решения

```
make load-test-post-quick       # быстрая проверка (1 мин, 10 VUs)
make load-test-post             # полный тест (11 мин, 100 VUs)
make measure-insert-lag         # замер лага вставки
make load-test-spike            # spike 200 VUs
make load-test-spike-extreme    # spike 500 VUs
```

---

## Прогресс

### Фаза 0: Подготовка инфраструктуры

- [x] **A. Python Consumer** — уже работает
- [x] **B. Kafka Connect Sink** — создано:
  - [x] `connect/Dockerfile` — образ с ClickHouse коннектором
  - [x] `connect/connectors/*.json` — конфиги 3 коннекторов (users, tracks, events)
  - [x] `docker-compose.connect.yml` — compose override
  - [x] `scripts/setup_connect.sh` — автонастройка
- [x] **C. Kafka Table Engine** — создано:
  - [x] `engine/clickhouse_kafka_tables.sql` — CREATE TABLE ... ENGINE = Kafka + MV
  - [x] `scripts/setup_engine.sh` — создание Kafka-таблиц в ClickHouse
  - [x] `scripts/teardown_engine.sh` — удаление Kafka-таблиц
- [x] **Makefile** — команды переключения добавлены
- [x] **Механизм переключения** — `KAFKA_CONSUMER_ENABLED` флаг в config/lifespan

### Фаза 1: Baseline — Python Consumer (решение A)

- [ ] Прогнать `load-test-post-quick` — записать результаты
- [ ] Прогнать `measure-insert-lag` — записать лаг
- [ ] Прогнать `load-test-spike` — записать поведение
- [ ] Записать потребление ресурсов (`docker stats`)

### Фаза 2: Kafka Connect Sink (решение B)

- [ ] Переключиться: `make down && make up-pipeline-connect`
- [ ] Прогнать те же тесты
- [ ] Записать результаты

### Фаза 3: Kafka Table Engine (решение C)

- [ ] Переключиться: `make down && make up-pipeline-engine`
- [ ] Прогнать те же тесты
- [ ] Записать результаты

### Фаза 4: Анализ и выводы

- [ ] Сводная таблица результатов
- [ ] Выводы — что лучше и для каких сценариев

---

## Результаты

### Решение A: Python Consumer

Baseline из `load_tests_investigation/general_report_k6_post_11032026.md` (11.03.2026):

| Тест | Результат | Заметки |
|------|-----------|---------|
| post 10 VUs (4.5 мин) | 37 RPS, 0% 5xx, events avg 208ms p95 746ms | Стабильно |
| post 30 VUs (5.5 мин) | 30 RPS, 0% 5xx, events avg 701ms p95 1541ms | Стабильно |
| insert-lag | avg -378ms, p95 -8ms, max 164ms | Отрицательные значения = вставка быстрее ответа API |
| stress 100 VUs | Падение при ~70-75 VUs (EOF/timeout) | Ограничение: 1 worker uvicorn, 5.8GB RAM |
| CPU/RAM | — | Нужно замерить при следующем прогоне |

### Решение B: Kafka Connect Sink

| Тест | Результат | Заметки |
|------|-----------|---------|
| post-quick (1 мин) | — | |
| insert-lag | — | |
| spike 200 VUs | — | |
| CPU/RAM | — | |

### Решение C: Kafka Table Engine

| Тест | Результат | Заметки |
|------|-----------|---------|
| post-quick (1 мин) | — | |
| insert-lag | — | |
| spike 200 VUs | — | |
| CPU/RAM | — | |

---

## Архитектура переключения

```
make up                      →  Базовая инфраструктура (CH, Kafka, Redis, API)
                                 + Python Consumer (текущее решение A)

make up-pipeline-connect     →  Базовая инфраструктура
                                 + Kafka Connect (решение B)
                                 API отправляет в Kafka, Connect пишет в CH
                                 Python consumer ОТКЛЮЧЁН

make up-pipeline-engine      →  Базовая инфраструктура
                                 + Kafka Table Engine (решение C)
                                 API отправляет в Kafka, CH сам читает из Kafka
                                 Python consumer ОТКЛЮЧЁН
```

Важно: API всегда работает и отправляет в Kafka. Меняется только **кто читает** из Kafka и пишет в ClickHouse.

## Ссылки

- Предыдущие результаты тестов (решение A): `load_tests_investigation/general_report_k6_post_11032026.md`
- Анализ альтернативных решений: `.claude/plans/streamed-bubbling-cookie.md`
