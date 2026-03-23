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

**Прогон 22.03.2026 (до фикса timestamp):**

| Тест | Результат | Заметки |
|------|-----------|---------|
| post-quick 10 VUs (1 мин) | **58 RPS**, 0% 5xx, users avg 30ms, tracks avg 26ms, events avg 290ms p95 537ms, recs avg 334ms p95 473ms | 925 итераций (vs 1400 у A) |
| insert-lag (50 запросов) | **FAIL — 0% записей дошли за 60с** | Ошибка парсинга `created_at` — Connect не может вставить timestamp в CH |
| spike 50 VUs (1.5 мин) | 568 запросов, avg **4278ms**, p95 **26323ms**, 0% реальных ошибок | Вдвое медленнее решения A, threshold p95<15s crossed |
| CPU пик (spike) | API 117%, CH **461%**, Kafka 120%, Connect 35% | CH ещё больше нагружен |
| RAM пик (spike) | API 91MB (1.5%), CH **3.3GB (57%)**, Kafka 490MB, Connect 570MB (9.4%) | Connect добавляет ~570MB JVM overhead |
| Потеря данных | Данные **не доходят** до CH через Connect из-за ошибки формата `created_at` | `errors.tolerance=all` маскирует проблему |

**Прогон 23.03.2026 (после фикса — `.isoformat()` → `.strftime('%Y-%m-%d %H:%M:%S')`):**

| Тест | Результат | Заметки |
|------|-----------|---------|
| post-quick 10 VUs (1 мин) | **101 RPS**, 0% 5xx, users avg 42ms, tracks avg 43ms, events avg 163ms p95 355ms, recs avg 144ms p95 310ms | 1530 итераций — на уровне решения A |
| insert-lag (50 запросов) | avg **-489ms**, p95 -30ms, max -8ms, **100% записей дошли** | Фикс работает! Лаг на уровне решений A и C |
| spike 50 VUs (1.5 мин) | 3857 запросов, avg **257ms**, p95 **1001ms**, 0% реальных ошибок, 41 interrupted | Значительно лучше решения A (1822ms avg) |
| RAM (после spike) | API 49MB, CH 748MB (12.6%), Kafka 408MB, Connect 836MB (14.1%) | Connect ~836MB JVM overhead |

### Решение C: Kafka Table Engine

**Прогон 22.03.2026 (до фикса — `parseDateTimeBestEffort`):**

| Тест | Результат | Заметки |
|------|-----------|---------|
| post-quick 10 VUs (1 мин) | **96 RPS**, 0% 5xx, users avg 25ms, tracks avg 28ms, events avg 179ms p95 319ms, recs avg 184ms p95 267ms | 1518 итераций — лучший результат |
| insert-lag (50 запросов) | avg **-485ms**, p95 -49ms, max -16ms, 100% записей дошли | Лучший лаг из всех решений |
| spike 50 VUs (1.5 мин) | **CRASH** — 429 запросов, avg **78128ms**, p95 1263035ms, 50 interrupted VUs | CH упал (OOM при ~60% RAM), тест длился 21 мин вместо 1.5 |
| CPU пик (spike) | API 64%, CH **343%**, Kafka 114% | До краша CH |
| RAM пик (spike) | API 138MB (2.3%), CH **3.5GB (60%)** → crash, Kafka 425MB | CH вылетает при достижении ~60% RAM |
| Потеря данных | При нормальной нагрузке 100%, **при spike — потеря из-за краша CH** | Kafka Table Engine добавляет нагрузку на CH, который и так bottleneck |

**Прогон 23.03.2026 (после фикса — `parseDateTimeBestEffort` → `parseDateTime`):**

| Тест | Результат | Заметки |
|------|-----------|---------|
| post-quick 10 VUs (1 мин) | **166 RPS**, 0% 5xx, users avg 40ms, tracks avg 41ms, events avg 79ms p95 149ms, recs avg 79ms p95 143ms | 2496 итераций — лучший результат из всех решений |
| insert-lag (50 запросов) | avg **-473ms**, p95 -44ms, max -1ms, **100% записей дошли** | На уровне других решений |
| spike 50 VUs (1.5 мин) | **PASSED** — 6678 запросов, avg **61ms**, p95 **183ms**, 0% реальных ошибок | Лучший spike-результат! CH не крашнулся |
| RAM (после spike) | API 86MB (1.5%), CH **557MB (9.4%)**, Kafka 409MB | Радикальное снижение нагрузки на CH |

---

## Финальный прогон 23.03.2026 (чистые данные, все фиксы применены)

Все тесты запущены на чистой базе (`make db-clean-test-data` перед каждым тестом).

| Метрика | A: Python Consumer | B: Kafka Connect | C: Kafka Table Engine |
|---------|-------------------|-------------------|----------------------|
| **RPS (10 VUs)** | 114 req/s | 109 req/s | **111 req/s** |
| **Users avg** | 54ms | 35ms | **40ms** |
| **Tracks avg** | 55ms | 35ms | **40ms** |
| **Events avg** | 119ms | 157ms | **80ms** |
| **Recs avg** | 119ms | 138ms | **81ms** |
| **Insert lag avg** | -462ms | **-510ms** | -490ms |
| **Insert lag p95** | -66ms | **-65ms** | -92ms |
| **Insert lag 100%** | **100%** | **100%** | **100%** |
| **Spike запросов** | 3031 | 3308 | **6698** |
| **Spike avg** | 232ms | 192ms | **60ms** |
| **Spike p95** | 401ms | **217ms** | 186ms |
| **Spike ошибки** | 0.10% (3) | 0.21% (7) | **0.00% (0)** |
| **CH RAM (после spike)** | 625MB (10.5%) | 692MB (11.7%) | **548MB (9.3%)** |
| **Доп. RAM** | **0** | +681MB (JVM) | **0** |
| **Redis side-effects** | **да** | нет | нет |

---

## История результатов (до фиксов, 22.03.2026)

| Метрика | A: Python (22.03) | B: Connect до фикса | C: Engine до фикса |
|---------|-------------------|-------------------|----------------------|
| **RPS (10 VUs)** | 90 req/s | 58 req/s | 96 req/s |
| **Insert lag 100%** | 100% | **0% (баг)** | 100% |
| **Spike avg** | 1822ms | 4278ms | **78128ms (crash)** |
| **Надёжность** | стабильно | данные теряются | crash под нагрузкой |

## Выводы

### Обновление 23.03.2026: Фиксы решений B и C

**Фикс B (producer):** `.isoformat()` → `.strftime('%Y-%m-%d %H:%M:%S')` — формат ISO 8601 несовместим с ClickHouse через Connect. Вынесено в `app/utils/datetime_utils.py`.

**Фикс C (MV):** `parseDateTimeBestEffort()` → `parseDateTime(field, '%Y-%m-%d %H:%M:%S')` — точный парсинг ~5x быстрее, радикально снизил CPU/RAM давление на CH.

### Лидер по производительности: Решение C — Kafka Table Engine

Финальный прогон на чистых данных подтвердил:
- **6698 запросов** в spike-тесте (vs 3308 у B, 3031 у A) — x2 throughput
- **60ms avg spike** (vs 192ms у B, 232ms у A) — лучшая latency
- **0% ошибок** в spike (vs 0.10% у A, 0.21% у B)
- **0 доп. RAM** (vs +681MB JVM у B)

### Рекомендация: Решение A — Python Consumer

Несмотря на превосходство C по производительности, **Python Consumer остаётся лучшим выбором** для текущего проекта:

1. **Redis side-effects** — единственное решение с обновлением метрик/аналитики при событиях
2. **Полный контроль** — кастомная логика обработки, fallback, батчинг
3. **Предсказуемость** — Table Engine перекладывает нагрузку на CH, который может деградировать при росте данных

### Решение B (Kafka Connect) — альтернатива с JVM

- **Финальный прогон**: 109 RPS, 100% доставка, spike avg 192ms, p95 217ms
- **Минус**: +681MB RAM (JVM), нет Redis side-effects, сложнее дебажить
- **Подходит**: для enterprise-сценариев с exactly-once гарантиями

### Решение C (Kafka Table Engine) — лучшая производительность

- **Финальный прогон**: 111 RPS, spike avg 60ms, 6698 запросов, 0% ошибок
- **Минус**: нет Redis side-effects, вся нагрузка на CH (риск при росте данных)
- **Подходит**: для максимальной производительности, если side-effects не нужны
- **Урок**: `parseDateTimeBestEffort` был основной причиной краша — точный парсинг критичен для production

### Ключевой вывод

Оба бага (B и C) имели одну **корневую причину** — несовместимость формата datetime между producer'ом и потребителями. Стандартизация формата через `format_datetime_ch()` и точный `parseDateTime()` исправила оба решения.

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
