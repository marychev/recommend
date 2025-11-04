# 📨 Kafka Integration

## Описание

Система использует Apache Kafka для асинхронной обработки событий взаимодействия пользователей с треками.

## 🎯 Зачем Kafka?

### Преимущества:

1. **Асинхронность** - API не ждет обработки события
2. **Масштабируемость** - можно добавить consumer'ов
3. **Надежность** - события не теряются при сбоях
4. **Декаплинг** - разделение приема и обработки событий
5. **Real-time** - обработка событий в реальном времени

### Архитектура:

```
┌─────────┐      HTTP POST      ┌─────────┐
│ Client  │ ──────────────────> │   API   │
└─────────┘                     └────┬────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
              ┌──────────┐     ┌─────────┐     ┌─────────┐
              │ClickHouse│     │  Kafka  │     │Background│
              │(синхронно│     │Producer │     │  Tasks  │
              └──────────┘     └────┬────┘     └─────────┘
                                    │
                          ┌─────────┴─────────┐
                          │   user_track_    │
                          │     events       │
                          │    (topic)       │
                          └─────────┬─────────┘
                                    │
                          ┌─────────▼─────────┐
                          │  Kafka Consumer   │
                          │  (опционально)    │
                          └───────────────────┘
                                    │
                      ┌─────────────┼─────────────┐
                      ▼             ▼             ▼
                ┌─────────┐   ┌─────────┐   ┌─────────┐
                │Analytics│   │Real-time│   │   ML    │
                │          │   │ Metrics │   │Training │
                └─────────┘   └─────────┘   └─────────┘
```

## 📁 Структура файлов

```
app/kafka/
├── __init__.py
├── client.py      # Подключение к Kafka
├── producer.py    # Отправка событий
└── consumer.py    # Обработка событий (опционально)
```

## ⚙️ Конфигурация

### Переменные окружения

```bash
# В .env или docker-compose.yml
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_EVENTS=user_track_events
KAFKA_CONSUMER_GROUP=recommend_consumer
```

### Docker Compose

```yaml
kafka:
  image: confluentinc/cp-kafka:latest
  ports:
    - "9092:9092"
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
```

## 🚀 Использование

### Producer (отправка событий)

```python
from app.kafka.producer import send_event

# Отправить одно событие
event = {
    "user_id": 1001,
    "track_id": 12345,
    "action_type": "play",
    "listen_duration_seconds": 180,
    "timestamp": datetime.now()
}

success = await send_event(event)
```

### Consumer (обработка событий)

```python
from app.kafka.consumer import consume_events

# Определить обработчик
async def process_event(event: dict):
    print(f"Обработка: {event}")
    # Ваша бизнес-логика

# Запустить consumer
await consume_events(process_event)
```

## 📊 Формат события

### JSON Schema

```json
{
  "user_id": 1001,
  "track_id": 12345,
  "action_type": "play",
  "listen_duration_seconds": 180,
  "timestamp": "2025-11-04T12:00:00.000Z"
}
```

### Поля:

- `user_id` (int) - ID пользователя
- `track_id` (int) - ID трека
- `action_type` (string) - Тип действия (см. ActionType enum)
- `listen_duration_seconds` (int) - Длительность прослушивания
- `timestamp` (ISO string) - Время события

## 🔄 Жизненный цикл события

### 1. Клиент отправляет событие

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1001,
    "track_id": 12345,
    "action_type": "play",
    "listen_duration_seconds": 180
  }'
```

### 2. API обрабатывает запрос

```python
# app/api/events.py
async def create_event(event, background_tasks):
    # 1. Валидация через Pydantic
    # 2. Сохранение в ClickHouse (синхронно)
    await clickhouse.insert(...)
    
    # 3. Отправка в Kafka (фоновая задача)
    background_tasks.add_task(process_event_async, interaction)
```

### 3. Producer отправляет в Kafka

```python
# app/kafka/producer.py
async def send_event(event):
    producer = await get_kafka_producer()
    message = serialize_event(event)
    await producer.send('user_track_events', value=message)
```

### 4. Consumer обрабатывает событие

```python
# app/kafka/consumer.py (опционально)
async for message in consumer:
    event = deserialize_event(message.value)
    await handler(event)
```

## 🎯 Применение

### 1. Real-time аналитика

```python
async def analytics_handler(event):
    # Обновить счетчики в Redis
    await redis.incr(f"play_count:{event['track_id']}")
    
    # Обновить тренды
    await update_trending_tracks(event)
```

### 2. Обновление материализованных представлений

```python
async def materialized_view_handler(event):
    # Пересчитать user_track_matrix
    await update_user_track_matrix(
        event['user_id'],
        event['track_id']
    )
```

### 3. ML модель real-time

```python
async def ml_handler(event):
    # Обновить модель онлайн
    await model.partial_fit(
        event['user_id'],
        event['track_id'],
        event['action_type']
    )
```

### 4. Нотификации

```python
async def notification_handler(event):
    if event['action_type'] == 'share':
        # Отправить уведомление
        await send_notification(
            user_id=event['user_id'],
            message=f"Трек {event['track_id']} был расшарен"
        )
```

## 🧪 Тестирование

### Проверка подключения

```bash
# Health check
curl http://localhost:8000/api/v1/health
```

Ответ:
```json
{
  "status": "healthy",
  "services": {
    "clickhouse": "connected",
    "redis": "connected",
    "kafka": "connected"
  }
}
```

### Отправка тестового события

```python
import asyncio
from app.kafka.producer import send_event
from datetime import datetime

async def test_send():
    event = {
        "user_id": 999,
        "track_id": 888,
        "action_type": "like",
        "listen_duration_seconds": 0,
        "timestamp": datetime.now()
    }
    
    success = await send_event(event)
    print(f"Отправлено: {success}")

asyncio.run(test_send())
```

### Чтение событий из Kafka

```bash
# Подключиться к Kafka контейнеру
docker exec -it music_recommend_kafka bash

# Прочитать события из топика
kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic user_track_events \
  --from-beginning
```

## 📈 Мониторинг

### Метрики Kafka

```python
# Получить метрики producer
producer = await get_kafka_producer()
metrics = await producer.metrics()

# Ключевые метрики:
# - record-send-rate: События/сек
# - record-error-rate: Ошибки/сек
# - request-latency-avg: Средняя задержка
```

### Логирование

```python
import logging

# Включить debug логи для Kafka
logging.getLogger('aiokafka').setLevel(logging.DEBUG)
```

## 🔧 Устранение неполадок

### Kafka недоступна

**Симптом**: `kafka_status: "disconnected"` в health check

**Решение**:
```bash
# Проверить что Kafka запущена
docker ps | grep kafka

# Перезапустить Kafka
docker-compose restart kafka

# Проверить логи
docker logs music_recommend_kafka
```

### События не доставляются

**Симптом**: События отправляются, но не читаются consumer'ом

**Причины**:
1. Неправильный топик
2. Consumer group offset
3. Сериализация

**Решение**:
```bash
# Проверить топики
docker exec music_recommend_kafka \
  kafka-topics --list --bootstrap-server localhost:9092

# Создать топик вручную (если нужно)
docker exec music_recommend_kafka \
  kafka-topics --create \
  --topic user_track_events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

### Медленная отправка

**Симптом**: API медленно отвечает

**Причины**:
1. Синхронная отправка в Kafka
2. Большой batch.size
3. Сетевые проблемы

**Решение**:
```python
# Используйте background tasks
background_tasks.add_task(process_event_async, event)

# Настройте producer
producer = AIOKafkaProducer(
    linger_ms=10,  # Подождать 10ms перед отправкой
    compression_type='gzip',  # Сжатие
    acks='all'  # Надежность
)
```

## 🚀 Production Best Practices

### 1. Множественные партиции

```bash
# Создать топик с 3 партициями для параллелизма
kafka-topics --create \
  --topic user_track_events \
  --partitions 3 \
  --replication-factor 3
```

### 2. Consumer Group

```python
# Запустить несколько consumer'ов в одной группе
# Они автоматически распределят партиции
consumer1 = await get_kafka_consumer(
    'user_track_events',
    group_id='recommend_consumer'
)
consumer2 = await get_kafka_consumer(
    'user_track_events',
    group_id='recommend_consumer'
)
```

### 3. Error Handling

```python
async def safe_send_event(event):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await send_event(event)
        except KafkaError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts")
                # Fallback: сохранить в DB для retry
                await save_failed_event(event)
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 4. Мониторинг

```python
# Используйте Prometheus metrics
from prometheus_client import Counter, Histogram

events_sent = Counter('kafka_events_sent_total', 'Total events sent')
send_duration = Histogram('kafka_send_duration_seconds', 'Send duration')

@send_duration.time()
async def send_event(event):
    result = await producer.send(...)
    events_sent.inc()
    return result
```

## 📚 Дополнительные ресурсы

- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [aiokafka Documentation](https://aiokafka.readthedocs.io/)
- [Confluent Platform](https://docs.confluent.io/)

## 🔗 Связанные файлы

- `app/kafka/client.py` - Подключение к Kafka
- `app/kafka/producer.py` - Producer
- `app/kafka/consumer.py` - Consumer
- `app/api/events.py` - Использование Kafka
- `app/utils/lifespan.py` - Lifecycle management
- `docker-compose.yml` - Конфигурация Kafka

---

**Создано**: 2025-11-04  
**Версия Kafka**: 3.5+  
**Библиотека**: aiokafka 0.8.1

