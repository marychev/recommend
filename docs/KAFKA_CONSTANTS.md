# ⚙️ Константы Kafka

## Описание

Все таймауты и параметры батчинга для модуля Kafka централизованы в `app/kafka/constants.py` для избежания расхождений.

## 📋 Таймауты для Producer

### Запуск Producer

```python
PRODUCER_START_TIMEOUT_DEFAULT = 5.0   # секунд (по умолчанию)
PRODUCER_START_TIMEOUT_EVENTS = 5.0   # секунд (для событий - более критично)
PRODUCER_START_TIMEOUT_BATCH = 2.0     # секунд (для батчей)
PRODUCER_START_TIMEOUT_QUICK = 1.0     # секунд (для быстрых операций: users, tracks)
```

### Запросы к Kafka

```python
PRODUCER_REQUEST_TIMEOUT_MS = 60000  # миллисекунд (60 секунд)
```

### Остановка клиентов

```python
CLIENT_STOP_TIMEOUT = 2.0  # секунд
```

## 📋 Параметры для Consumer

### Автоматический коммит offset

```python
CONSUMER_AUTO_COMMIT_INTERVAL_MS = 5000  # миллисекунд (5 секунд)
```

### Переподключение

```python
CONSUMER_MAX_RETRIES = 5                    # Максимальное количество попыток
CONSUMER_RETRY_DELAY_INITIAL = 1.0         # секунд (начальная задержка, экспоненциально увеличивается)
```

### Подключение к Kafka

```python
CONNECT_KAFKA_MAX_RETRIES = 3
CONNECT_KAFKA_BASE_DELAY_NORMAL = 1.0   # секунд (обычный режим)
CONNECT_KAFKA_BASE_DELAY_FAST = 0.1     # секунд (fast_mode для тестов)
```

## 📋 Параметры для батчинга

### DataHandler (Kafka Consumer → ClickHouse)

```python
DATA_HANDLER_BATCH_SIZE = 1000        # записей
DATA_HANDLER_FLUSH_INTERVAL = 5.0     # секунд
```

**Использование:**
- Kafka Consumer обрабатывает события из топиков
- Накапливает в буфере до 1000 записей
- Автоматически сбрасывает каждые 5 секунд
- Записывает в ClickHouse батчами

### EventQueue (API → Kafka)

```python
# В app/services/event_queue.py
batch_size = 100        # событий (по умолчанию)
flush_interval = 1.5    # секунды (по умолчанию)
```

**Использование:**
- API добавляет события в очередь
- Накапливает до 100 событий
- Автоматически сбрасывает каждые 1.5 секунды
- Отправляет в Kafka батчами

## 🔄 Поток данных с константами

```
POST /events
  ↓
EventQueue (batch_size=100, flush_interval=1.5s)
  ↓
Kafka Producer (start_timeout=2.0s для батчей)
  ↓
Kafka Topic
  ↓
Kafka Consumer (retry_delay=1.0s, max_retries=5)
  ↓
DataHandler (batch_size=1000, flush_interval=5.0s)
  ↓
ClickHouse (батч INSERT)
```

## 📊 Преимущества централизации

✅ **Единое место** для всех таймаутов - легко изменять значения  
✅ **Нет расхождений** - все используют одни и те же константы  
✅ **Легче поддерживать** - изменения в одном месте  
✅ **Понятная документация** - все значения описаны в одном файле  

## 🔧 Изменение параметров

Для изменения параметров батчинга отредактируйте `app/kafka/constants.py`:

```python
# Увеличить размер батча для DataHandler
DATA_HANDLER_BATCH_SIZE = 2000  # было 1000

# Уменьшить интервал flush для EventQueue
# (в app/services/event_queue.py)
batch_size = 200  # было 100
flush_interval = 1.0  # было 1.5
```

## 📝 Связанные файлы

- `app/kafka/constants.py` - Константы
- `app/kafka/client.py` - Использует константы для producer/consumer
- `app/kafka/producer.py` - Использует константы для таймаутов
- `app/kafka/data_handler.py` - Использует константы для батчинга
- `app/services/event_queue.py` - Параметры очереди событий

---

**Создано**: 2025-01-30  
**Версия**: 1.0

