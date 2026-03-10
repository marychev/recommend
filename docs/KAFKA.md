# Kafka — архитектура и настройка

## Архитектура

```
POST /events → EventQueue (batch 100, flush 1.5s) → Kafka Producer → Topic
                                                                        ↓
POST /users  → Kafka Producer → Topic                          Kafka Consumer
POST /tracks → Kafka Producer → Topic                    (batch 1000, flush 5s)
                                                                        ↓
                                                              ClickHouse (батч INSERT)
```

Все POST запросы проходят через Kafka — API отвечает мгновенно (ID генерируется до отправки), Consumer записывает в ClickHouse батчами.

## Конфигурация

### Docker Compose

- **Образ:** `confluentinc/cp-kafka:7.5.0`
- **Listeners:** INTERNAL (kafka:29092) + EXTERNAL (localhost:9092)
- **Zookeeper:** `confluentinc/cp-zookeeper:7.5.0` (порт 2181)

### Топики

| Топик | Назначение |
|-------|------------|
| `user_track_events` | События взаимодействий |
| `users` | Создание пользователей |
| `tracks` | Создание треков |

### Константы (`app/kafka/constants.py`)

**Producer:**
- `PRODUCER_START_TIMEOUT_DEFAULT` = 5.0s
- `PRODUCER_START_TIMEOUT_BATCH` = 2.0s
- `PRODUCER_START_TIMEOUT_QUICK` = 1.0s
- `PRODUCER_REQUEST_TIMEOUT_MS` = 60000ms

**Consumer:**
- `CONSUMER_AUTO_COMMIT_INTERVAL_MS` = 5000ms
- `CONSUMER_MAX_RETRIES` = 5
- `CONSUMER_RETRY_DELAY_INITIAL` = 1.0s

**Батчинг:**
- `DATA_HANDLER_BATCH_SIZE` = 1000 записей (Consumer → ClickHouse)
- `DATA_HANDLER_FLUSH_INTERVAL` = 5.0s
- EventQueue: 100 событий, flush каждые 1.5s (API → Kafka)

## Структура файлов

```
app/kafka/
├── constants.py       # Константы таймаутов и батчинга
├── client.py          # Подключение к Kafka
├── producer.py        # Отправка событий (send_event, send_user, send_track, send_batch_events)
├── consumer.py        # Обработка событий
├── data_handler.py    # Батчинг Consumer → ClickHouse (1000 записей, 5 сек)
└── multi_consumer.py  # Consumers для всех топиков (users, tracks, events)

app/services/
└── event_queue.py     # Батчинг API → Kafka (100 событий, 1.5 сек)
```

## Поток данных

```
POST /events
  ↓
EventQueue (batch_size=100, flush_interval=1.5s)
  ↓
Kafka Producer (start_timeout=2.0s)
  ↓
Kafka Topic (user_track_events)
  ↓
Kafka Consumer (retry_delay=1.0s, max_retries=5)
  ↓
DataHandler (batch_size=1000, flush_interval=5.0s)
  ↓
ClickHouse (батч INSERT)
```

## Батчинг и буферизация

### На уровне API (EventQueue)
- Накапливает до 100 событий
- Flush каждые 1.5 секунды
- Отправляет батчами через `send_batch_events()`

### На уровне Consumer (DataHandler)
- Накапливает до 1000 записей
- Flush каждые 5 секунд
- Записывает в ClickHouse одним INSERT
- При ошибке записи возвращаются в буфер

### На уровне ClickHouseClient
- Буферы для `users`, `tracks`, `user_track_interactions`
- Защита от race conditions (`asyncio.Lock`)
- Graceful shutdown: flush всех буферов при остановке

### Результаты оптимизации

| Метрика | До | После |
|---------|-----|-------|
| INSERT запросов | 100 | 1 батч |
| Время ответа | ~677ms | ~50-100ms |
| RPS | ~18 | 50+ |

## Отказоустойчивость

- **Fallback:** Если Kafka недоступна → прямой INSERT в ClickHouse
- **Retry:** Экспоненциальный backoff при ошибках
- **Буфер возврата:** При ошибке INSERT записи возвращаются в буфер
- **Graceful shutdown:** Все буферы сбрасываются при остановке

## Мониторинг и диагностика

```bash
# Логи Kafka
make logs-kafka

# Health check (включает статус Kafka)
make health

# Проверить топики
docker exec music_recommend_kafka \
  kafka-topics --list --bootstrap-server localhost:9092

# Читать события из топика
docker exec -it music_recommend_kafka bash
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic user_track_events --from-beginning
```

## Формат события

```json
{
  "user_id": 1001,
  "track_id": 12345,
  "action_type": "play",
  "listen_duration_seconds": 180,
  "timestamp": "2025-11-04T12:00:00.000Z"
}
```

## Troubleshooting

### Kafka недоступна

```bash
docker ps | grep kafka
make logs-kafka
docker compose restart kafka
```

### События не доставляются

```bash
# Проверить топики
docker exec music_recommend_kafka \
  kafka-topics --list --bootstrap-server localhost:9092

# Создать топик вручную
docker exec music_recommend_kafka \
  kafka-topics --create --topic user_track_events \
  --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1
```

## Связанные документы

- [CACHING.md](CACHING.md) — Redis кэширование
- [CLICKHOUSE.md](CLICKHOUSE.md) — Оптимизация ClickHouse
- [TESTING.md](TESTING.md) — Тестирование Kafka
