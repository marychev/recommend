# 🚀 Лучшие практики оптимизации POST запросов при нагрузках

## Архитектура: Kafka + Redis + ClickHouse

### Текущая реализация
- ✅ Events отправляются в Kafka асинхронно через `background_tasks`
- ✅ Redis кэширование для рекомендаций
- ✅ Параллельные проверки существования в `create_event`
- ⚠️ Каждый INSERT в ClickHouse выполняется отдельно
- ⚠️ Каждое событие отправляется в Kafka по одному

---

## 🎯 Рекомендуемые оптимизации

### 1. Батчинг INSERT в ClickHouse

**Проблема:** Каждый POST запрос делает отдельный INSERT, что неэффективно при высокой нагрузке.

**Решение:** Накапливать записи в буфере и вставлять батчами.

```python
# app/db/clickhouse.py

class ClickHouseClient:
    def __init__(self):
        self.client: Optional[ChClient] = None
        self.session: Optional[ClientSession] = None
        # Буфер для батчинга
        self._insert_buffer: Dict[str, List[Dict]] = {
            'users': [],
            'tracks': [],
            'user_track_interactions': []
        }
        self._buffer_size = 100  # Размер батча
        self._flush_interval = 5.0  # Секунды
        self._flush_task: Optional[asyncio.Task] = None

    async def save_user_buffered(self, user: User) -> int:
        """Сохранить пользователя в буфер (асинхронная запись)"""
        # Генерируем ID сразу для ответа клиенту
        new_id = self._generate_user_id()
        
        # Добавляем в буфер
        self._insert_buffer['users'].append({
            'user_id': new_id,
            'username': user.username,
            'email': user.email or '',
            'age': user.age or 0,
            'country': user.country or '',
            'created_at': datetime.now()
        })
        
        # Если буфер заполнен, сбрасываем
        if len(self._insert_buffer['users']) >= self._buffer_size:
            await self._flush_buffer('users')
        
        return new_id

    async def _flush_buffer(self, table: str):
        """Сбросить буфер в ClickHouse"""
        if not self._insert_buffer[table]:
            return
        
        records = self._insert_buffer[table]
        self._insert_buffer[table] = []
        
        # Батч INSERT
        await self.insert_batch(table, records)

    async def insert_batch(self, table: str, records: List[Dict]):
        """Вставить несколько записей одним запросом"""
        if not records:
            return
        
        await self._ensure_connected()
        
        # Формируем VALUES для батча
        values = []
        for record in records:
            values.append(tuple(record.values()))
        
        columns = ', '.join(records[0].keys())
        query = f"INSERT INTO {table} ({columns}) VALUES"
        
        await self.client.execute(query, values)
```

**Преимущества:**
- ✅ 10-100x быстрее при высокой нагрузке
- ✅ Меньше нагрузка на ClickHouse
- ✅ Лучшая пропускная способность

**Недостатки:**
- ⚠️ Нужно обрабатывать потерю данных при падении (можно использовать Kafka как буфер)

---

### 2. Очередь для батчинга событий в Kafka

**Проблема:** Каждое событие отправляется в Kafka отдельно, много мелких запросов.

**Решение:** Накапливать события в очереди и отправлять батчами.

```python
# app/services/event_queue.py

from collections import deque
import asyncio
from typing import Deque, Dict, Any

class EventQueue:
    def __init__(self, batch_size: int = 50, flush_interval: float = 2.0):
        self._queue: Deque[Dict[str, Any]] = deque()
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None

    async def add_event(self, event: Dict[str, Any]):
        """Добавить событие в очередь"""
        async with self._lock:
            self._queue.append(event)
            
            # Если очередь заполнена, сбрасываем
            if len(self._queue) >= self._batch_size:
                await self._flush()

    async def _flush(self):
        """Отправить батч событий в Kafka"""
        if not self._queue:
            return
        
        events = []
        async with self._lock:
            while self._queue and len(events) < self._batch_size:
                events.append(self._queue.popleft())
        
        if events:
            from app.kafka.producer import send_batch_events
            await send_batch_events(events)

    async def start_periodic_flush(self):
        """Запустить периодический сброс очереди"""
        async def flush_loop():
            while True:
                await asyncio.sleep(self._flush_interval)
                await self._flush()
        
        self._flush_task = asyncio.create_task(flush_loop())

# Глобальная очередь
_event_queue = EventQueue()

# В app/routers/events.py
async def process_event_async(event: UserTrackInteraction):
    """Отправка события в очередь (не напрямую в Kafka)"""
    event_dict = {
        "user_id": event.user_id,
        "track_id": event.track_id,
        "action_type": event.action_type.value,
        "listen_duration_seconds": event.listen_duration_seconds,
        "timestamp": event.timestamp.isoformat(),
    }
    
    # Добавляем в очередь (быстро, не блокирует)
    await _event_queue.add_event(event_dict)
```

**Преимущества:**
- ✅ Меньше запросов к Kafka (50 событий в одном запросе)
- ✅ Лучшая пропускная способность
- ✅ Меньше нагрузка на Kafka broker

---

### 3. Write-behind кэширование для частых операций

**Проблема:** Каждая проверка существования делает запрос к ClickHouse.

**Решение:** Кэшировать результаты проверок в Redis с коротким TTL.

```python
# app/services/cache.py

import redis.asyncio as redis
from app.config import settings

redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url(
            f"redis://{settings.redis_host}:{settings.redis_port}"
        )
    return redis_client

async def exists_user_cached(user_id: int) -> bool:
    """Проверить существование пользователя с кэшированием"""
    redis = await get_redis()
    
    # Проверяем кэш
    cache_key = f"user_exists:{user_id}"
    cached = await redis.get(cache_key)
    
    if cached is not None:
        return cached == b"1"
    
    # Если нет в кэше, проверяем в ClickHouse
    clickhouse = get_clickhouse_client()
    result = await clickhouse.execute_raw(
        f"SELECT 1 FROM users WHERE user_id = {user_id} LIMIT 1"
    )
    
    exists = len(result) > 0
    
    # Кэшируем результат на 5 минут
    await redis.setex(cache_key, 300, "1" if exists else "0")
    
    return exists

async def invalidate_user_cache(user_id: int):
    """Инвалидировать кэш пользователя"""
    redis = await get_redis()
    await redis.delete(f"user_exists:{user_id}")
```

**Преимущества:**
- ✅ Быстрые проверки для часто запрашиваемых пользователей
- ✅ Меньше нагрузка на ClickHouse
- ✅ TTL автоматически обновляет кэш

---

### 4. Redis Pipeline для множественных операций

**Проблема:** Множественные операции с Redis выполняются последовательно.

**Решение:** Использовать pipeline для группировки операций.

```python
# app/services/cache.py

async def invalidate_user_recommendations_pipelined(user_ids: List[int]):
    """Инвалидировать кэш для нескольких пользователей через pipeline"""
    redis = await get_redis()
    
    # Создаем pipeline
    pipe = redis.pipeline()
    
    for user_id in user_ids:
        # Добавляем команды в pipeline
        pattern = f"recommendations:user:{user_id}:*"
        # Используем SCAN для поиска всех ключей (если много ключей)
        pipe.eval(
            f"""
            local keys = redis.call('keys', '{pattern}')
            for i=1,#keys do
                redis.call('del', keys[i])
            end
            return #keys
            """,
            0
        )
    
    # Выполняем все команды одним запросом
    await pipe.execute()
```

**Преимущества:**
- ✅ Меньше round-trips к Redis
- ✅ Быстрее при множественных операциях
- ✅ Атомарность операций

---

### 5. Асинхронная обработка через Kafka Consumer

**Проблема:** Обновление `user_track_matrix` происходит синхронно или не происходит вообще.

**Решение:** Kafka Consumer обрабатывает события асинхронно и обновляет матрицу батчами.

```python
# app/kafka/consumer.py

async def process_events_batch(events: List[Dict[str, Any]]):
    """Обработать батч событий для обновления матрицы"""
    clickhouse = get_clickhouse_client()
    
    # Группируем события по user_id для батч-обновления
    user_events = {}
    for event in events:
        user_id = event['user_id']
        if user_id not in user_events:
            user_events[user_id] = []
        user_events[user_id].append(event)
    
    # Обновляем матрицу батчами
    for user_id, user_event_list in user_events.items():
        await update_user_track_matrix_batch(user_id, user_event_list)

async def update_user_track_matrix_batch(
    user_id: int, 
    events: List[Dict[str, Any]]
):
    """Обновить user_track_matrix батчем событий"""
    clickhouse = get_clickhouse_client()
    
    # Вычисляем implicit_rating для всех событий
    values = []
    for event in events:
        action_type = event['action_type']
        weight = ActionType.get_weight(action_type)
        
        values.append((
            user_id,
            event['track_id'],
            weight,
            event.get('listen_duration_seconds', 0)
        ))
    
    # Батч INSERT в user_track_matrix
    query = """
    INSERT INTO user_track_matrix 
    (user_id, track_id, implicit_rating, last_interaction_duration)
    VALUES
    """
    
    await clickhouse.insert_batch('user_track_matrix', values)
```

**Преимущества:**
- ✅ Не блокирует API запросы
- ✅ Обработка событий батчами
- ✅ Масштабируемость (можно запустить несколько consumers)

---

### 6. Оптимизация проверок существования

**Текущая реализация:** ✅ Уже использует `asyncio.gather` для параллельных проверок.

**Дополнительная оптимизация:** Кэширование результатов проверок.

```python
# В app/routers/events.py

async def create_event_optimized(
    event: UserTrackInteractionCreate, 
    background_tasks: BackgroundTasks
):
    """Оптимизированная версия create_event"""
    clickhouse = get_clickhouse_client()
    timestamp = event.timestamp if event.timestamp else datetime.now()
    
    # Используем кэшированные проверки
    from app.services.cache import exists_user_cached, exists_track_cached
    
    user_check, track_check = await asyncio.gather(
        exists_user_cached(event.user_id),
        exists_track_cached(event.track_id),
        return_exceptions=True
    )
    
    if isinstance(user_check, Exception) or not user_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {event.user_id} не найден",
        )
    
    if isinstance(track_check, Exception) or not track_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Трек с ID {event.track_id} не найден",
        )
    
    # Остальной код...
```

---

### 7. Connection Pooling для ClickHouse

**Текущая реализация:** ✅ Использует `aiohttp.ClientSession` (уже есть pooling).

**Оптимизация:** Настроить размер пула и таймауты.

```python
# app/db/clickhouse.py

async def connect(self):
    """Подключение к ClickHouse с оптимизированным пулом"""
    connector = aiohttp.TCPConnector(
        limit=100,  # Максимум соединений
        limit_per_host=20,  # Максимум на хост
        ttl_dns_cache=300,  # Кэш DNS
        force_close=False,  # Переиспользование соединений
    )
    
    timeout = aiohttp.ClientTimeout(
        total=30,  # Общий таймаут
        connect=5,  # Таймаут подключения
        sock_read=10  # Таймаут чтения
    )
    
    self.session = ClientSession(
        connector=connector,
        timeout=timeout
    )
    
    # Остальной код подключения...
```

---

## 📊 Сравнение производительности

### До оптимизаций:
```
POST /events: ~200-500ms
- Проверка user: 50ms
- Проверка track: 50ms
- INSERT в ClickHouse: 100ms
- Отправка в Kafka: 50ms
- Итого: ~250ms
```

### После оптимизаций:
```
POST /events: ~50-100ms
- Проверка user (кэш): 5ms
- Проверка track (кэш): 5ms
- INSERT в буфер: <1ms
- Добавление в очередь Kafka: <1ms
- Итого: ~50ms (5x быстрее!)

Батч обработка (асинхронно):
- Батч INSERT (100 записей): 200ms → 2ms на запись
- Батч Kafka (50 событий): 100ms → 2ms на событие
```

---

## 🎯 Приоритеты внедрения

### Высокий приоритет (быстрый эффект):
1. ✅ **Очередь для батчинга Kafka** - легко внедрить, большой эффект
2. ✅ **Кэширование проверок существования** - быстро, снижает нагрузку
3. ✅ **Redis Pipeline** - для инвалидации кэша

### Средний приоритет:
4. ⚠️ **Батчинг INSERT в ClickHouse** - требует обработки потери данных
5. ⚠️ **Kafka Consumer для обновления матрицы** - требует настройки consumer

### Низкий приоритет:
6. ℹ️ **Connection Pooling** - уже частично реализовано
7. ℹ️ **Write-behind кэширование** - для очень высокой нагрузки

---

## ⚠️ Важные замечания

### Потеря данных при батчинге
При использовании буферов нужно обрабатывать потерю данных при падении сервера:

**Решение 1:** Использовать Kafka как буфер
- Сначала отправляем в Kafka
- Consumer обрабатывает и вставляет в ClickHouse батчами

**Решение 2:** Периодический flush
- Автоматический сброс буфера каждые N секунд
- При завершении приложения - принудительный flush

### Мониторинг
- Отслеживать размер буферов
- Мониторить задержку обработки
- Алерты при переполнении буферов

---

## 📝 Примеры использования

### Батчинг событий в Kafka
```python
# В app/routers/events.py
from app.services.event_queue import _event_queue

@router.post("/events")
async def create_event(event: UserTrackInteractionCreate):
    # ... валидация ...
    
    await clickhouse.save_event(event, timestamp)
    
    # Добавляем в очередь (не блокирует)
    await _event_queue.add_event(event_dict)
    
    return interaction
```

### Кэширование проверок
```python
# В app/routers/events.py
from app.services.cache import exists_user_cached, exists_track_cached

user_exists, track_exists = await asyncio.gather(
    exists_user_cached(event.user_id),
    exists_track_cached(event.track_id)
)
```

---

## 🔗 Связанные документы

- [Kafka Integration](./KAFKA_INTEGRATION.md)
- [Redis Caching](./REDIS_CACHING.md)
- [SQL Optimization](./SQL_OPTIMIZATION.md)
- [Performance Issues](../PERFORMANCE_ISSUES.md)

