# Pipeline Benchmark: Kafka→ClickHouse

**Дата:** 22-23.03.2026 | **Среда:** Docker, 5.8GB RAM, 1 worker uvicorn | **Инструмент:** k6

Сравнение 3 подходов доставки данных из Kafka в ClickHouse для рекомендательной системы музыкальных треков. Одна среда, одинаковые тесты, один результат.

---

## 1. Решения

| # | Решение | Команда запуска | Суть |
|---|---------|----------------|------|
| A | **Python Consumer** (текущее) | `make up` | aiokafka + BatchBuffer + HTTP INSERT. Redis side-effects, fallback, полный контроль |
| B | **Kafka Connect Sink** | `make up-pipeline-connect` | JVM-процесс с ClickHouse Sink Connector. Декларативная конфигурация, exactly-once возможен |
| C | **Kafka Table Engine** | `make up-pipeline-engine` | ClickHouse сам читает из Kafka через встроенный движок. SQL-only, ноль внешнего кода |

### Архитектура переключения

```
API → Kafka Producer → Kafka Broker
                           ↓
          ┌────────────────┼────────────────┐
          A                B                C
   Python Consumer    Kafka Connect    CH Table Engine
   (aiokafka)         (JVM Sink)       (ENGINE=Kafka)
          ↓                ↓                ↓
      ClickHouse       ClickHouse       ClickHouse
          ↓
        Redis
    (side-effects)
```

API всегда отправляет в Kafka. Меняется только **кто читает** из Kafka и пишет в ClickHouse.
Переключение: флаг `KAFKA_CONSUMER_ENABLED` в конфиге API.

---

## 2. Методология тестирования

### Что измеряем

- **Throughput (RPS)** — сколько запросов/сек обрабатывает система
- **Insert lag** — задержка от POST запроса до появления в ClickHouse
- **Потеря данных** — все ли записи дошли (100%?)
- **Ресурсы** — CPU/RAM потребление при нагрузке
- **Поведение под стрессом** — spike 50 VUs, ramp-up 30с

### Тесты

```
make load-test-post-quick       # нормальная нагрузка (1 мин, 10 VUs)
make measure-insert-lag         # замер лага вставки (50 запросов)
make load-test-spike            # spike test (50 VUs, ramp-up 30с)
```

### Методология финального прогона

- `make db-clean-test-data` (TRUNCATE всех таблиц) перед **каждым** тестом
- Полный `make down` + перезапуск между решениями
- Одна среда, одинаковые тесты, чистая база

---

## 3. Финальные результаты (23.03.2026)

Все фиксы применены, чистые данные.

### Нормальная нагрузка (10 VUs, 1 мин)

| | A: Python | B: Connect | C: Engine |
|---|---|---|---|
| RPS | **114** | 109 | 111 |
| Users avg | 54ms | **35ms** | 40ms |
| Tracks avg | 55ms | **35ms** | 40ms |
| Events avg | 119ms | 157ms | **80ms** |
| Recs avg | 119ms | 138ms | **81ms** |
| Ошибки | 0% | 0% | 0% |

Все три — сопоставимый RPS (~110). C лидирует по latency events/recs.

### Доставка данных (insert lag, 50 запросов)

| | A: Python | B: Connect | C: Engine |
|---|---|---|---|
| Avg lag | -462ms | -510ms | -490ms |
| p95 lag | -66ms | -65ms | -92ms |
| Доставлено | **100%** | **100%** | **100%** |

100% данных доставлено у всех. Отрицательный lag — clock skew между хостом k6 и Docker (см. раздел 5).

### Пиковая нагрузка (spike 50 VUs, ramp-up 30с)

| | A: Python | B: Connect | C: Engine |
|---|---|---|---|
| Запросов | 3031 | 3308 | **6698** |
| Avg время ответа | 232ms | 192ms | **60ms** |
| p95 | 401ms | 217ms | **186ms** |
| Ошибки | 0.10% (3) | 0.21% (7) | **0.00% (0)** |
| CH RAM после spike | 625MB (10.5%) | 692MB (11.7%) | **548MB (9.3%)** |
| Доп. RAM | **0** | +681MB (JVM) | **0** |

C обработал x2 запросов при x4 меньшей latency и нулевых ошибках.

### Сводная таблица

| Критерий | A: Python | B: Connect | C: Engine |
|----------|-----------|------------|-----------|
| RPS (норм.) | **114** | 109 | 111 |
| Доставка данных | **100%** | **100%** | **100%** |
| Spike throughput | 3031 | 3308 | **6698** |
| Spike latency | 232ms | 192ms | **60ms** |
| Redis side-effects | **да** | нет | нет |
| Доп. RAM | **0** | +681MB (JVM) | **0** |
| Сложность | Python (~500 строк) | конфигурация JSON | SQL (3 файла) |
| Production-ready | **да** | **да** | **да** |

---

## 4. Решение и обоснование

### Выбрано: A — Python Consumer

1. **Redis side-effects** — единственное решение с обновлением метрик/аналитики при событиях. Для рекомендательной системы это критично.
2. **Полный контроль** — кастомный батчинг (BatchBuffer 1000/5с), error recovery (возврат записей в буфер при ошибке), fallback на прямой INSERT.
3. **Изоляция процессов** — Kafka reader не конкурирует за память с ClickHouse. В решении C — всё в одном процессе CH.

### Альтернативы

**C (Table Engine)** — лидер по spike-производительности (60ms avg, 6698 запросов, 0% ошибок). Подходит для сценариев без side-effects и при умеренных объёмах данных.

**B (Kafka Connect)** — enterprise-вариант с exactly-once гарантиями. Подходит при JVM-экосистеме. Минус: +681MB RAM (JVM overhead).

---

## 5. Insert lag: почему отрицательный?

### Как измеряется

```
k6 (хост)                          API (Docker-контейнер)              ClickHouse
─────────                          ─────────────────────              ──────────
1. apiStartTime = Date.now()  →
                                   2. created_at = datetime.now()
                                   3. return 201 (сразу, не ждёт CH)
                                   4. background: send_to_kafka()
                                                                      5. Consumer → BatchBuffer → INSERT
6. poll CH: SELECT created_at  →                                      7. return created_at
8. lag = created_at − apiStartTime
```

### Почему отрицательный

**Clock skew** — рассинхронизация часов между хостом k6 (Windows/WSL) и Docker-контейнером. Часы контейнера отстают на ~460-510ms.

**Доказательство:** все 3 решения показывают одинаковый сдвиг. Если бы это было свойством pipeline — значения различались бы. Это постоянная дельта часов.

### Что важно

- **100% данных доставлено** — главная метрика
- **p95 lag** показывает **стабильность** — разброс минимален
- В production с NTP-синхронизацией ожидаемый lag: **0-6 секунд** (EventQueue 1.5с + BatchBuffer 5с)
- API отвечает клиенту **сразу**, запись идёт в фоне через Kafka

---

## 6. Баги и уроки

### Баг B: формат datetime (22.03.2026)

**Симптом:** 0% данных дошло до CH через Connect.
**Причина:** Python `datetime.isoformat()` → `2026-03-22T14:30:00`. Connect не может распарсить ISO 8601 для ClickHouse DateTime.
**Фикс:** `.isoformat()` → `.strftime('%Y-%m-%d %H:%M:%S')` в producer. Вынесено в `format_datetime_ch()` (`app/utils/datetime_utils.py`).

### Баг C: parseDateTimeBestEffort → OOM (22.03.2026)

**Симптом:** CH crash (OOM) при spike. 3.5GB RAM (60%), тест 21 мин вместо 1.5.
**Причина:** `parseDateTimeBestEffort()` в Materialized View перебирает десятки форматов — дорого по CPU/RAM. Под spike — двойной удар: API-запросы + MV-парсинг в одном процессе.
**Фикс:** `parseDateTimeBestEffort(field)` → `parseDateTime(field, '%Y-%m-%d %H:%M:%S')` — точный парсинг **~5x быстрее**. CH RAM при spike: 3.5GB → **548MB**.

### Общий вывод

Оба бага — **одна корневая причина**: несовместимость формата datetime между producer'ом и потребителями. Стандартизация через `format_datetime_ch()` (Python) и `parseDateTime()` (SQL) решила обе проблемы.

---

## 7. История тестов (до фиксов)

### Решение A: Python Consumer (22.03.2026)

| Тест | Результат | Заметки |
|------|-----------|---------|
| post-quick 10 VUs | **90 RPS**, events avg 191ms p95 409ms | Стабильно, 1400 итераций |
| insert-lag | avg **-453ms**, p95 -42ms, 100% дошли | Отрицательный лаг = clock skew |
| spike 50 VUs | 1241 запросов, avg 1822ms, **p95 10793ms** | Деградация на пике, но без падений |
| RAM пик | CH **3.0GB (52%)** | CH — основной bottleneck |

Baseline (11.03.2026): 37 RPS при 10 VUs, падение при ~70-75 VUs.

### Решение B: Kafka Connect (22.03.2026, до фикса)

| Тест | Результат | Заметки |
|------|-----------|---------|
| post-quick 10 VUs | **58 RPS**, events avg 290ms | 925 итераций |
| insert-lag | **FAIL — 0% записей за 60с** | Баг формата `created_at` |
| spike 50 VUs | 568 запросов, avg **4278ms**, p95 **26323ms** | Вдвое медленнее A |
| RAM пик | CH **3.3GB (57%)**, Connect 570MB JVM | Connect добавляет overhead |

### Решение C: Kafka Table Engine (22.03.2026, до фикса)

| Тест | Результат | Заметки |
|------|-----------|---------|
| post-quick 10 VUs | **96 RPS**, events avg 179ms | 1518 итераций |
| insert-lag | avg **-485ms**, 100% дошли | Лучший лаг |
| spike 50 VUs | **CRASH** — 429 запросов, avg **78128ms** | CH OOM при 60% RAM, тест 21 мин |
| RAM пик | CH **3.5GB (60%)** → crash | `parseDateTimeBestEffort` — причина |

### Сравнение до/после фиксов

| Метрика | A (без фикса) | B до фикса | B после | C до фикса | C после |
|---------|--------------|------------|---------|------------|---------|
| RPS | 90 | 58 | **109** | 96 | **111** |
| Insert lag 100% | 100% | **0%** | **100%** | 100% | **100%** |
| Spike avg | 1822ms | 4278ms | **192ms** | 78128ms (crash) | **60ms** |
| CH RAM spike | 3.0GB | 3.3GB | **692MB** | 3.5GB (crash) | **548MB** |

---

## 8. Инфраструктура бенчмарка

### Прогресс подготовки

- [x] **A. Python Consumer** — текущая реализация
- [x] **B. Kafka Connect Sink:**
  - `connect/Dockerfile` — образ с ClickHouse коннектором
  - `connect/connectors/*.json` — конфиги 3 коннекторов (users, tracks, events)
  - `docker-compose.connect.yml` — compose override
  - `scripts/setup_connect.sh` — автонастройка
- [x] **C. Kafka Table Engine:**
  - `engine/clickhouse_kafka_tables.sql` — CREATE TABLE ... ENGINE = Kafka + MV
  - `scripts/setup_engine.sh` — создание Kafka-таблиц
  - `scripts/teardown_engine.sh` — удаление Kafka-таблиц
- [x] **Механизм переключения** — `KAFKA_CONSUMER_ENABLED` флаг в config/lifespan
- [x] **Очистка данных** — `scripts/clean_test_data.sh`, интегрирован в Makefile

### Утилиты

```bash
make db-clean-test-data          # TRUNCATE таблиц перед тестом
make db-check-test-data          # показать row count (без удаления)
make connect-status              # статус коннекторов (решение B)
make pipeline-verify             # сравнение row count
```

---

## 9. Что делать дальше

1. **Масштабировать API** — добавить uvicorn workers (сейчас 1)
2. **Оптимизировать запросы** — ревизия MV, индексов, тяжёлых SELECT
3. **Мониторинг CH** — при росте данных Table Engine может перегружать CH

---

*Предыдущие результаты тестов решения A (11.03.2026): `load_tests_investigation/general_report_k6_post_11032026.md`*
