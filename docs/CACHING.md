# Redis кэширование рекомендаций

## Архитектура

```
POST /recommendations
    ↓
Проверка кэша в Redis
    ↓
Есть в кэше? ──YES──→ Вернуть из кэша (5-10ms)
    ↓ NO
Запрос к ClickHouse (200-500ms)
    ↓
Сохранение в Redis (TTL: 1-4 часа)
    ↓
Возврат результата
```

### Формат ключа

```
recommendations:user:{user_id}:top_n:{top_n}:exclude:{exclude_listened}
```

### TTL

По умолчанию 3600 секунд (1 час). Можно изменить:

```bash
# Через API
curl -X POST http://localhost:8000/api/v1/debug/cache/set-ttl/4  # 4 часа
curl http://localhost:8000/api/v1/debug/cache/current-ttl
```

```python
# В app/config.py
recommendations_cache_ttl: int = 3600
```

---

## Стратегия инвалидации

Кэш инвалидируется **только** при значимых действиях:

```python
CACHE_INVALIDATING_ACTIONS = {
    ActionType.LIKE,             # Явное одобрение
    ActionType.DISLIKE,          # Явное неодобрение
    ActionType.ADD_TO_PLAYLIST,  # Добавление в плейлист
    ActionType.SHARE,            # Поделиться треком
}

# PLAY и SKIP НЕ инвалидируют кэш
```

При инвалидации удаляются все ключи `recommendations:user:{user_id}:*`.

### Результат селективной инвалидации

| Этап | Оптимизация | Hit Rate |
|------|-------------|----------|
| 0 | Исходное (инвалидация на каждое событие) | 0% |
| 1 | Селективная инвалидация | 60% |
| 2 | Увеличение TTL (2-4 часа) | 75-80% |
| 3 | Предварительный прогрев | 85-90% |

---

## Cache Warmup (прогрев)

Проактивное кэширование для активных пользователей:

```bash
# Автоматический прогрев активных пользователей
curl -X POST "http://localhost:8000/api/v1/debug/cache/warmup?num_users=50"

# Статистика прогрева
curl http://localhost:8000/api/v1/debug/cache/warmup/stats

# Список активных пользователей
curl http://localhost:8000/api/v1/debug/cache/warmup/active-users
```

Прогрев определяет топ-N активных пользователей за последние 30 дней и генерирует для них рекомендации заранее.

---

## Диагностика кэша

### Через API

```bash
# Статус кэша
curl http://localhost:8000/api/v1/debug/cache/status

# Ключи кэша
curl http://localhost:8000/api/v1/debug/cache/keys

# Тест операций
curl -X POST http://localhost:8000/api/v1/debug/cache/test

# Симуляция hit rate
curl -X POST http://localhost:8000/api/v1/debug/cache/simulate-hitrate
```

### Через Redis CLI

```bash
docker exec -it music_recommend_redis redis-cli

KEYS recommendations:user:*                              # Все ключи
GET "recommendations:user:1001:top_n:10:exclude:True"    # Конкретный ключ
TTL "recommendations:user:1001:top_n:10:exclude:True"    # Оставшееся время
INFO stats                                                # Статистика Redis
INFO memory                                               # Использование памяти
```

### Через Makefile

```bash
make diagnose-cache       # Диагностика кэширования (Python скрипты)
make diagnose-cache-curl  # Диагностика через curl
make test-cache-warmup    # Тест прогрева кэша
```

### Логи

```bash
make logs-api | grep -i cache       # Cache hit/miss
make logs-api | grep "Invalidated"  # Инвалидации
```

---

## Типичные проблемы

### Кэш не работает (всегда MISS)

```bash
# Проверить подключение Redis
make health
docker exec -it music_recommend_redis redis-cli PING  # Должно быть PONG
```

### Кэш инвалидируется слишком часто

Убедитесь, что только LIKE/DISLIKE/ADD_TO_PLAYLIST/SHARE инвалидируют кэш (не PLAY/SKIP).

### Очистка кэша

```bash
# Весь кэш рекомендаций
docker exec -it music_recommend_redis redis-cli
> KEYS recommendations:*
> DEL <ключ>

# Или полная очистка Redis
> FLUSHDB
```

---

## Производительность

| Метрика | Без кэша | С кэшем (hit) |
|---------|----------|---------------|
| Latency (p50) | 250ms | 12ms |
| Latency (p99) | 500ms | 20ms |
| Нагрузка на ClickHouse | 100% | 10-20% |

## Связанные файлы

- `app/services/cache.py` — Функции кэширования
- `app/services/cache_warmup.py` — Прогрев кэша
- `app/routers/events.py` — Инвалидация кэша
- `app/routers/cache_debug.py` — Debug эндпоинты

## Связанные документы

- [KAFKA.md](KAFKA.md) — Kafka интеграция
- [CLICKHOUSE.md](CLICKHOUSE.md) — Оптимизация ClickHouse
