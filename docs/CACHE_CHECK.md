# 🔍 Проверка кэширования рекомендаций

## Быстрая проверка

### 1. Через скрипт

```bash
python scripts/check_cache.py
```

Скрипт проверит:
- ✅ Подключение к Redis
- 📊 Статистику кэша
- 🔑 Ключи кэша
- 🧪 Операции кэширования (set/get/invalidate)

### 2. Через API эндпоинт

```bash
# Статус кэша
curl http://localhost:8000/api/v1/debug/cache/status

# Ключи кэша
curl http://localhost:8000/api/v1/debug/cache/keys

# Тест операций
curl -X POST http://localhost:8000/api/v1/debug/cache/test
```

### 3. Через Redis CLI

```bash
# Подключиться к Redis
docker exec -it music_recommend_redis redis-cli

# Посмотреть все ключи рекомендаций
KEYS recommendations:user:*

# Посмотреть конкретный ключ
GET "recommendations:user:1001:top_n:10:exclude:True"

# TTL ключа (сколько осталось времени)
TTL "recommendations:user:1001:top_n:10:exclude:True"

# Статистика Redis
INFO stats
```

## Проверка в реальных условиях

### 1. Первый запрос (cache MISS)

```bash
# Запрос рекомендаций
time curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1001, "top_n": 10, "exclude_listened": true}'

# Проверить логи
docker-compose logs api | grep "Cache"
# Должно быть: ❌ Cache MISS
```

### 2. Второй запрос (cache HIT)

```bash
# Тот же запрос
time curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1001, "top_n": 10, "exclude_listened": true}'

# Проверить логи
docker-compose logs api | grep "Cache"
# Должно быть: ✅ Cache HIT
# Время ответа должно быть намного меньше (5-10ms vs 200-500ms)
```

### 3. Инвалидация кэша

```bash
# Создать событие (like инвалидирует кэш)
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1001,
    "track_id": 5,
    "action_type": "like"
  }'

# Проверить логи
docker-compose logs api | grep "Invalidated"
# Должно быть: 🗑️ Invalidated X cached recommendations

# Проверить, что кэш удален
docker exec -it music_recommend_redis redis-cli \
  KEYS "recommendations:user:1001:*"
# Должно вернуть пустой массив
```

## Мониторинг кэша

### Логи

```bash
# Cache hits
docker-compose logs api | grep "Cache HIT"

# Cache misses
docker-compose logs api | grep "Cache MISS"

# Инвалидации
docker-compose logs api | grep "Invalidated"

# Сохранения в кэш
docker-compose logs api | grep "Cached recommendations"
```

### Метрики

```bash
# Статистика через API
curl http://localhost:8000/api/v1/debug/cache/status | jq

# Пример ответа:
# {
#   "redis_connected": true,
#   "cache_stats": {
#     "status": "connected",
#     "cached_recommendations": 42,
#     "ttl_seconds": 3600
#   }
# }
```

## Типичные проблемы

### 1. Кэш не работает (всегда MISS)

**Причины:**
- Redis не подключен
- Ошибки при сохранении в кэш
- Неправильный формат ключа

**Решение:**
```bash
# Проверить подключение
docker-compose logs api | grep "Redis"

# Проверить ошибки
docker-compose logs api | grep "Error.*cache"
```

### 2. Кэш инвалидируется слишком часто

**Причина:**
- События play/skip инвалидируют кэш (исправлено - только like/dislike/share)

**Проверка:**
```bash
# Проверить логи инвалидации
docker-compose logs api | grep "Кэш НЕ инвалидируется"
```

### 3. Кэш не инвалидируется

**Причина:**
- События не обрабатываются
- Фоновая задача не выполняется

**Решение:**
```bash
# Проверить обработку событий
docker-compose logs api | grep "process_event_async"
```

## Оптимизация

### Увеличить TTL

```python
# В .env файле
RECOMMENDATIONS_CACHE_TTL=7200  # 2 часа вместо 1
```

### Проверить hit rate

```bash
# Запустить нагрузочный тест
k6 run load_tests/k6_recommendations_performance_test.js

# Проверить метрики кэша в отчете
```

## Формат ключей кэша

```
recommendations:user:{user_id}:top_n:{top_n}:exclude:{exclude_listened}
```

**Примеры:**
- `recommendations:user:1001:top_n:10:exclude:True`
- `recommendations:user:1001:top_n:20:exclude:False`
- `recommendations:user:2005:top_n:10:exclude:True`

**Важно:** Разные параметры = разные ключи = разные кэши

