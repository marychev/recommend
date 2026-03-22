# Анализ: Kafka-ClickHouse интеграция — наш подход vs альтернативы

## Контекст

Документация ClickHouse предлагает 4 основных подхода для интеграции Kafka → ClickHouse:
1. **ClickPipes** (только ClickHouse Cloud)
2. **Kafka Connect Sink** (отдельный фреймворк)
3. **Kafka Table Engine** (встроенный движок ClickHouse)
4. **Custom code** (наш текущий подход)

---

## Наш текущий подход

```
API → EventQueue (batch 100 / 1.5s) → Kafka Producer → Kafka Broker
                                                           ↓
ClickHouse ← BatchBuffer (batch 1000 / 5s) ← DataHandler ← Multi-Consumer (aiokafka)
```

**Что мы делаем:**
- Пишем Python-код с aiokafka (producer + consumer)
- Два уровня батчинга (EventQueue → Kafka, BatchBuffer → ClickHouse)
- Ручное управление оффсетами (auto-commit каждые 5 сек)
- HTTP-вставки в ClickHouse через aiochclient
- Три параллельных консьюмера (users, tracks, events)
- Обработка ошибок, reconnect с exponential backoff
- Fallback: если Kafka недоступен → пишем напрямую в ClickHouse

---

## Альтернатива 1: Kafka Table Engine (встроенный в ClickHouse)

```sql
CREATE TABLE events_queue (
    user_id UInt32, track_id UInt32, action_type String, timestamp DateTime
) ENGINE = Kafka('kafka:9092', 'user_track_events', 'clickhouse_group', 'JSONEachRow');

CREATE MATERIALIZED VIEW events_mv TO user_track_interactions AS
SELECT * FROM events_queue;
```

**Весь наш consumer-код (multi_consumer.py, data_handler.py, batch_buffer.py, event_queue.py) заменяется на ~10 строк SQL.**

### Плюсы:
- Нулевой код на Python для потребления данных
- ClickHouse сам управляет оффсетами, батчингом, потоками
- Автоматическая интеграция с MaterializedView (у нас уже есть MV для статистик)
- До 100K строк/сек на один Kafka Engine
- Настройка через `kafka_max_block_size`, `kafka_num_consumers`

### Минусы:
- **At-least-once** семантика (дубликаты возможны) — но у нас и сейчас то же самое
- Ограниченная горизонтальная масштабируемость консьюмеров (не больше числа партиций)
- Сложная отладка ошибок (логи в clickhouse-server.err.log, не в приложении)
- **Нет возможности обновлять Redis-метрики** при потреблении — это критично для нас
- Нет fallback-логики (Kafka недоступен → данные теряются до восстановления)

### Вердикт:
**Не подходит напрямую** из-за Redis-обновлений. Наш DataHandler при получении event-ов обновляет Redis-счётчики (метрики, кеш популярных треков). Kafka Table Engine — это чистый pipe Kafka→ClickHouse без middleware-логики. Мы бы потеряли side-effects.

---

## Альтернатива 2: Kafka Connect Sink

### Плюсы:
- **Exactly-once** семантика через KeeperMap — единственный подход с такой гарантией
- Dead Letter Queue для невалидных сообщений
- Масштабирование через tasks.max
- Встроенные retry с умными error-кодами ClickHouse
- Мониторинг через JMX

### Минусы:
- Ещё один компонент в инфраструктуре (JVM-процесс, Kafka Connect framework)
- Требует Kafka Connect кластер + конфигурацию
- Та же проблема — **нет Redis side-effects**
- Operational complexity значительно выше
- Для нашего масштаба — overkill

### Вердикт:
**Избыточно** для нашего проекта. Имеет смысл в enterprise-сценариях с десятками топиков и строгими требованиями exactly-once.

---

## Альтернатива 3: ClickPipes

Только для ClickHouse Cloud. **Не применимо** — мы self-hosted.

---

## Итоговая оценка

| Критерий | Наш подход | Kafka Engine | Kafka Connect |
|----------|-----------|--------------|---------------|
| Сложность кода | Высокая (~500 строк Python) | Минимальная (~10 строк SQL) | Средняя (конфиг) |
| Инфраструктура | Kafka + Python app | Kafka + ClickHouse | Kafka + Connect + JVM |
| Гарантии доставки | At-least-once | At-least-once | Exactly-once |
| Redis side-effects | Да | Нет | Нет |
| Fallback при сбое Kafka | Да (прямая запись в CH) | Нет | Нет |
| Гибкость обработки | Полная | Только SQL-трансформации | Средняя |
| Отладка | Python-логи | CH server logs | JMX + логи |
| Производительность | Хорошая (батчинг) | Отличная (нативная) | Отличная |

---

## Моё мнение

### Наш подход — обоснованный выбор

Для нашего проекта custom-код оправдан по трём причинам:

1. **Redis side-effects** — при потреблении events мы обновляем Redis-метрики и кеш. Ни Kafka Engine, ни Kafka Connect этого не дают. Пришлось бы строить отдельный pipeline для Redis, что удвоило бы сложность.

2. **Fallback-логика** — если Kafka недоступен, мы пишем напрямую в ClickHouse. Это важно для resilience. Встроенные решения такого не предлагают.

3. **Контроль над обработкой** — мы можем валидировать данные, трансформировать, логировать, и всё это в одном месте на Python.

### Где можно улучшить, заимствуя идеи

1. **Kafka Table Engine для read-only данных** — таблицы `users` и `tracks` не требуют Redis side-effects. Можно использовать Kafka Engine + MV только для них, а events оставить на Python-консьюмере. Это уберёт 2 из 3 консьюмеров.

2. **Dead Letter Queue** (идея из Kafka Connect) — сейчас невалидные сообщения просто логируются. Можно добавить DLQ-топик для ошибочных записей.

3. **Более агрессивный батчинг** — документация рекомендует блоки 500K-1M строк для Kafka Engine. Наш BatchBuffer с 1000 записей может быть маловат для пиковых нагрузок. Стоит рассмотреть адаптивный размер батча.

### Гибридный подход (возможная оптимизация)

```
users topic  ──→ Kafka Engine ──→ MV ──→ users table (ClickHouse)
tracks topic ──→ Kafka Engine ──→ MV ──→ tracks table (ClickHouse)
events topic ──→ Python Consumer ──→ Redis + BatchBuffer ──→ ClickHouse
```

Это сократит код и даст нативную производительность для users/tracks, сохранив гибкость для events.


```
Лаг данных в нашем текущем пайплайне
Прежде чем сравнивать с Kafka Connect, нужно понимать, какой лаг у нас сейчас. Данные проходят через несколько буферов, каждый добавляет задержку:


Событие создано
    │
    ▼
EventQueue ─── до 1.5 сек (или мгновенно если набралось 100 событий)
    │
    ▼
Kafka Producer → Broker ─── ~миллисекунды (acks=all, GZIP)
    │
    ▼
Kafka Consumer ─── зависит от poll-интервала, обычно ~мс
    │
    ▼
BatchBuffer ─── до 5 сек (или мгновенно если набралось 1000 записей)
    │
    ▼
ClickHouse INSERT (HTTP)
Worst-case лаг: ~6.5 секунд (1.5с EventQueue + 5с BatchBuffer)
Best-case лаг: ~миллисекунды (оба буфера сбрасываются мгновенно при заполнении)

Это двойная буферизация — данные буферизуются и перед Kafka, и после Kafka. Плюс auto-commit оффсетов каждые 5 секунд (constants.py:28) означает, что при падении консьюмера мы можем перечитать до 5 секунд данных (дубликаты).

Как Kafka Connect Sink решает ту же задачу
Kafka Connect — это фреймворк, который берёт на себя всё то, что мы написали руками: потребление из Kafka, батчинг, вставку в ClickHouse, управление оффсетами.

Ключевые отличия по лагу:
Аспект	Наш подход	Kafka Connect Sink
Буферизация перед Kafka	EventQueue (1.5с / 100 шт)	Нет — Connect читает напрямую из топика
Буферизация перед ClickHouse	BatchBuffer (5с / 1000 шт)	max.poll.records (500 по умолчанию, рекомендуют 5000-10000)
Контроль размера батча	Фиксированный (1000)	Настраиваемый + async_insert на стороне CH
Оффсеты	Auto-commit 5с	Коммит после успешного INSERT (exactly-once возможен)
При падении	Дубликаты до 5с	Exactly-once через KeeperMap (0 дубликатов)
Exactly-once — главное преимущество Connect
У нас сейчас: консьюмер читает → кладёт в буфер → через 5 сек буфер пишет в ClickHouse → auto-commit оффсета. Если процесс упал между INSERT и commit — данные будут перечитаны и вставлены повторно.

Kafka Connect Sink с exactlyOnce=true использует KeeperMap (встроенное key-value хранилище ClickHouse на ZooKeeper) для атомарной записи: "вставить данные + сохранить оффсет" в одной транзакции. Падение в любой точке — данные либо записаны целиком, либо нет.

Async Inserts — интересный подход к лагу
Kafka Connect может использовать async_insert на стороне ClickHouse:


async_insert=1              — ClickHouse сам буферизует мелкие INSERT-ы
wait_for_async_insert=1     — ждать подтверждения записи
async_insert_max_data_size=16MB  — порог для flush
async_insert_busy_timeout_ms=1000 — макс. задержка
Это переносит батчинг с клиента на сервер ClickHouse. Клиент шлёт мелкие INSERT-ы часто (низкий лаг), а ClickHouse сам собирает их в большие блоки (высокая эффективность). Мы этот подход не используем — у нас батчинг полностью на стороне Python.

Что стоит обдумать к занятию
3 ключевых вопроса:

Нужен ли нам exactly-once? Сейчас у нас at-least-once. Для счётчика прослушиваний дубликат — это искажение метрик. Для рекомендаций — менее критично. Насколько это важно для нашей системы?

Стоит ли убрать двойную буферизацию? EventQueue перед Kafka + BatchBuffer после — это два места, где данные могут застрять или потеряться. Kafka Connect убирает эту сложность. Но мы теряем Redis side-effects.

Async inserts как компромисс? Можно не переходить на Kafka Connect, а просто включить async_insert в ClickHouse и уменьшить наш BatchBuffer до минимума. Это снизит лаг без смены архитектуры.

А у нас есть возможность сделать как бы новую версию в этом проекте. И запускать его скажем make up-kafka-connect-sinc или название получше придумать?
Можно что то такого реазиловать? Просто, чтобы видеть глазами и тестировать руками
Отличная идея — поднять Kafka Connect Sink рядом с текущим решением для сравнения. Давай разберусь, что у нас есть.

Read docker-compose.yml
Read Makefile
Да, это отлично реализуемо. Можно создать отдельный docker-compose файл с Kafka Connect, который поднимается рядом с основной инфраструктурой и пишет в те же таблицы ClickHouse.

Read clickhouse_schemas.sql
Bash Check existing docker-compose files
IN
ls /home/recommend/docker-compose*.yml
```