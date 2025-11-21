# 🔍 Руководство по диагностике кэширования

## Проблема: Hit Rate = 0%

Мы выявили критическую проблему - кэш рекомендаций не работает (hit rate = 0%). Это руководство поможет диагностировать и исправить проблему.

## 🚀 Быстрая диагностика

### 1. Запустите систему
```bash
make up
```

### 2. Запустите диагностику кэша
```bash
make diagnose-cache
```

Или вручную:
```bash
python test_cache_api.py
```

## 🔧 Ручная диагностика через API

### 1. Проверка статуса кэша
```bash
curl http://localhost:8000/api/v1/debug/cache/status
```

**Ожидаемый результат:**
```json
{
  "redis_connected": true,
  "cache_stats": {
    "status": "connected",
    "cached_recommendations": 0,
    "ttl_seconds": 3600
  }
}
```

### 2. Проверка ключей кэша
```bash
curl http://localhost:8000/api/v1/debug/cache/keys
```

### 3. Тест операций кэширования
```bash
curl -X POST http://localhost:8000/api/v1/debug/cache/test
```

**Ожидаемый результат:**
```json
{
  "success": true,
  "results": {
    "redis_connection": true,
    "basic_redis_ops": true,
    "cache_save": {
      "success": true,
      "time_ms": 5.2
    },
    "cache_get": {
      "success": true,
      "time_ms": 2.1,
      "data_found": true
    }
  }
}
```

### 4. Симуляция hit rate
```bash
curl -X POST http://localhost:8000/api/v1/debug/cache/simulate-hitrate
```

**Ожидаемый результат:**
```json
{
  "success": true,
  "results": {
    "hit_rate": 90.0,
    "hits": 9,
    "misses": 1,
    "avg_cache_time": 2.5,
    "avg_miss_time": 15.3
  }
}
```

## 🚨 Возможные проблемы и решения

### Проблема 1: Redis не подключен
**Симптомы:**
```json
{
  "redis_connected": false,
  "cache_stats": {
    "status": "disconnected"
  }
}
```

**Решение:**
```bash
# Проверить статус Redis
make ps

# Перезапустить Redis
docker-compose restart redis

# Проверить логи Redis
make logs-redis
```

### Проблема 2: Кэш сохраняется, но не читается
**Симптомы:**
- `cache_save.success: true`
- `cache_get.success: false`

**Возможные причины:**
1. Проблемы с сериализацией/десериализацией JSON
2. Неправильные ключи кэша
3. TTL слишком короткий

**Решение:**
Проверить логи API:
```bash
make logs-api | grep -i cache
```

### Проблема 3: Агрессивная инвалидация
**Симптомы:**
- Тесты проходят успешно
- Но в реальных условиях hit rate = 0%

**Причина:** Каждое событие пользователя очищает кэш

**Решение:** Реализовать селективную инвалидацию (следующий этап)

## 📊 Интерпретация результатов

### ✅ Хорошие показатели:
- `redis_connected: true`
- `cache_save.success: true`
- `cache_get.success: true`
- `hit_rate > 80%` в симуляции

### ❌ Проблемные показатели:
- `redis_connected: false`
- `cache_save.success: false`
- `cache_get.data_found: false`
- `hit_rate < 10%` в симуляции

## 🔄 Следующие шаги

После успешной диагностики переходим к исправлению:

1. **Если все тесты проходят** → Проблема в агрессивной инвалидации
2. **Если Redis не подключен** → Исправить подключение к Redis
3. **Если операции кэша не работают** → Исправить логику кэширования

## 📝 Логирование

Для отладки включите детальное логирование кэша:

```python
# В app/services/cache.py
import logging
logging.getLogger("app.services.cache").setLevel(logging.DEBUG)
```

Затем проверьте логи:
```bash
make logs-api | grep "cache"
```

## 🎯 Цель

После исправления проблем ожидаемые показатели:
- **Hit Rate: 60-80%** (вместо текущих 0%)
- **Время ответа из кэша: 5-15ms** (вместо 200-500ms)
- **Снижение нагрузки на ClickHouse: в 3-5 раз**
