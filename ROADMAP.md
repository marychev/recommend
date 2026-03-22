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

- [x] Прогнать `load-test-post-quick` — записать результаты
- [x] Прогнать `measure-insert-lag` — записать лаг
- [x] Прогнать `load-test-spike` — записать поведение
- [x] Записать потребление ресурсов (`docker stats`)

### Фаза 2: Kafka Connect Sink (решение B)

- [x] Переключиться: `make down && make up-pipeline-connect`
- [x] Прогнать те же тесты
- [x] Записать результаты

### Фаза 3: Kafka Table Engine (решение C)

- [x] Переключиться: `make down && make up-pipeline-engine`
- [x] Прогнать те же тесты
- [x] Записать результаты

### Фаза 4: Анализ и выводы

- [x] Сводная таблица результатов
- [x] Выводы — что лучше и для каких сценариев

---

## Результаты

### Решение A: Python Consumer

**Прогон 22.03.2026:**

| Тест | Результат | Заметки |
|------|-----------|---------|
| post-quick 10 VUs (1 мин) | **90 RPS**, 0% 5xx, users/tracks avg 35ms, events avg 191ms p95 409ms, recs avg 180ms p95 330ms | Стабильно, 1400 итераций |
| insert-lag (50 запросов) | avg **-453ms**, p95 -42ms, max 3ms, 100% записей дошли | Отрицательный лаг = вставка быстрее ответа API |
| spike 50 VUs (1.5 мин) | 1241 запросов, avg 1822ms, **p95 10793ms**, 0% реальных ошибок | Деградация на пике, но без падений |
| CPU пик (spike) | API 77%, CH **311%**, Kafka 122% | CH — основной потребитель CPU |
| RAM пик (spike) | API 113MB (1.9%), CH **3.0GB (52%)**, Kafka 561MB (9.5%) | CH до 52% от 5.8GB лимита |

Baseline из `load_tests_investigation/general_report_k6_post_11032026.md` (11.03.2026):

| Тест | Результат | Заметки |
|------|-----------|---------|
| post 10 VUs (4.5 мин) | 37 RPS, 0% 5xx, events avg 208ms p95 746ms | Стабильно |
| post 30 VUs (5.5 мин) | 30 RPS, 0% 5xx, events avg 701ms p95 1541ms | Стабильно |
| insert-lag | avg -378ms, p95 -8ms, max 164ms | Отрицательные значения = вставка быстрее ответа API |
| stress 100 VUs | Падение при ~70-75 VUs (EOF/timeout) | Ограничение: 1 worker uvicorn, 5.8GB RAM |

### Решение B: Kafka Connect Sink

**Прогон 22.03.2026:**

| Тест | Результат | Заметки |
|------|-----------|---------|
| post-quick 10 VUs (1 мин) | **58 RPS**, 0% 5xx, users avg 30ms, tracks avg 26ms, events avg 290ms p95 537ms, recs avg 334ms p95 473ms | 925 итераций (vs 1400 у A) |
| insert-lag (50 запросов) | **FAIL — 0% записей дошли за 60с** | Ошибка парсинга `created_at` — Connect не может вставить timestamp в CH |
| spike 50 VUs (1.5 мин) | 568 запросов, avg **4278ms**, p95 **26323ms**, 0% реальных ошибок | Вдвое медленнее решения A, threshold p95<15s crossed |
| CPU пик (spike) | API 117%, CH **461%**, Kafka 120%, Connect 35% | CH ещё больше нагружен |
| RAM пик (spike) | API 91MB (1.5%), CH **3.3GB (57%)**, Kafka 490MB, Connect 570MB (9.4%) | Connect добавляет ~570MB JVM overhead |
| Потеря данных | Данные **не доходят** до CH через Connect из-за ошибки формата `created_at` | `errors.tolerance=all` маскирует проблему |

### Решение C: Kafka Table Engine

**Прогон 22.03.2026:**

| Тест | Результат | Заметки |
|------|-----------|---------|
| post-quick 10 VUs (1 мин) | **96 RPS**, 0% 5xx, users avg 25ms, tracks avg 28ms, events avg 179ms p95 319ms, recs avg 184ms p95 267ms | 1518 итераций — лучший результат |
| insert-lag (50 запросов) | avg **-485ms**, p95 -49ms, max -16ms, 100% записей дошли | Лучший лаг из всех решений |
| spike 50 VUs (1.5 мин) | **CRASH** — 429 запросов, avg **78128ms**, p95 1263035ms, 50 interrupted VUs | CH упал (OOM при ~60% RAM), тест длился 21 мин вместо 1.5 |
| CPU пик (spike) | API 64%, CH **343%**, Kafka 114% | До краша CH |
| RAM пик (spike) | API 138MB (2.3%), CH **3.5GB (60%)** → crash, Kafka 425MB | CH вылетает при достижении ~60% RAM |
| Потеря данных | При нормальной нагрузке 100%, **при spike — потеря из-за краша CH** | Kafka Table Engine добавляет нагрузку на CH, который и так bottleneck |

---

## Сводная таблица результатов (22.03.2026)

| Метрика | A: Python Consumer | B: Kafka Connect | C: Kafka Table Engine |
|---------|-------------------|-------------------|----------------------|
| **RPS (10 VUs)** | 90 req/s | 58 req/s | **96 req/s** |
| **Events avg** | 191ms | 290ms | **179ms** |
| **Recs avg** | 180ms | 334ms | **184ms** |
| **Insert lag avg** | -453ms | **FAIL** (не пишет) | **-485ms** |
| **Insert lag 100%** | 100% | 0% | **100%** |
| **Spike avg** | **1822ms** | 4278ms | 78128ms (crash) |
| **Spike p95** | **10793ms** | 26323ms | 1263035ms |
| **Spike ошибки** | **0%** | 0% | crash + timeouts |
| **CPU пик CH** | 311% | 461% | 343% → crash |
| **RAM пик CH** | 3.0GB (52%) | 3.3GB (57%) | 3.5GB (60%) → crash |
| **Доп. RAM** | 0 | +570MB (JVM) | 0 |
| **Redis side-effects** | да | нет | нет |
| **Надёжность** | стабильно | данные теряются | crash под нагрузкой |

## Выводы

### Победитель: Решение A — Python Consumer

**Python Consumer остаётся лучшим выбором** для текущего проекта:

1. **Стабильность** — единственное решение, которое выдержало spike test без падений и потерь данных
2. **Функциональность** — поддержка Redis side-effects (обновление метрик при событиях), fallback, кастомная логика обработки
3. **Ресурсы** — не требует дополнительных JVM-процессов, минимальный overhead

### Решение B (Kafka Connect) — не рекомендуется

- **Несовместимость форматов** — Connect не может правильно вставить `created_at` timestamp в ClickHouse, данные теряются молча (`errors.tolerance=all`)
- **Ниже RPS** (58 vs 90) — JVM overhead + дополнительный слой абстракции
- **+570MB RAM** за JVM-процесс Connect
- Требует значительной доработки конфигурации для production-ready состояния

### Решение C (Kafka Table Engine) — ограниченно применимо

- **Лучший RPS при низкой нагрузке** (96 req/s) — ClickHouse читает напрямую, минимум overhead
- **Лучший insert lag** (-485ms) — данные появляются в CH быстрее всех
- **Crash при spike** — ClickHouse и так является bottleneck (CPU 311%), а Table Engine добавляет ему ещё работу по чтению из Kafka, что приводит к OOM при нагрузке
- **Вывод**: подходит для сценариев с предсказуемой нагрузкой без пиков, но опасен в production с переменным трафиком

### Главный bottleneck

Во всех решениях **ClickHouse является узким местом** — CPU до 461%, RAM до 60%. Дальнейшая оптимизация должна быть направлена на:
- Увеличение ресурсов для ClickHouse (RAM limit, CPU)
- Оптимизацию запросов (MV, индексы)
- Масштабирование API (больше uvicorn workers)

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
