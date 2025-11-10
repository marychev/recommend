# 🔍 Руководство по диагностике производительности

Полное руководство по выявлению и устранению проблем производительности в Music Recommendation System.

---

## 📋 Содержание

- [Быстрая диагностика](#быстрая-диагностика)
- [Типы проблем](#типы-проблем)
- [Пошаговая диагностика](#пошаговая-диагностика)
- [Оптимизация](#оптимизация)
- [Мониторинг](#мониторинг)

---

## ⚡ Быстрая диагностика

### Шаг 1: Запустите диагностический тест

```bash
make load-test-diagnostics
```

Этот тест покажет:
- Время ответа каждого endpoint
- Количество ошибок по endpoint
- Узкие места системы
- Конкретные рекомендации

### Шаг 2: Проверьте систему

```bash
make diagnose
```

Покажет:
- Статус контейнеров
- Доступность API
- Данные в БД
- Последние ошибки

---

## 🎯 Типы проблем

### 1️⃣ Медленные запросы (High Latency)

**Симптомы:**
- p95 > 5000ms
- Среднее время ответа > 2000ms
- Timeout ошибки

**Причины:**
```
❌ ClickHouse медленно отвечает
❌ Нет индексов в БД
❌ Кэш Redis не работает
❌ Сложные SQL запросы
❌ Мало ресурсов CPU/RAM
```

### 2️⃣ Высокий процент ошибок (High Error Rate)

**Симптомы:**
- Ошибки > 5-10%
- 500 Internal Server Error
- Connection refused

**Причины:**
```
❌ ClickHouse не подключен
❌ Redis недоступен
❌ Нет данных в БД
❌ Переполнение connection pool
❌ Out of Memory
```

### 3️⃣ Деградация при нагрузке

**Симптомы:**
- При малой нагрузке работает OK
- При >50 VUs время ответа растет
- Система не масштабируется

**Причины:**
```
❌ Недостаточно connection pool
❌ Блокировки в БД
❌ Мало CPU/RAM
❌ Синхронная обработка запросов
```

---

## 🔬 Пошаговая диагностика

### Этап 1: Базовая проверка

```bash
# 1. Проверьте, что все сервисы запущены
make ps

# Должны работать:
# ✓ music_recommend_api
# ✓ music_recommend_clickhouse
# ✓ music_recommend_redis
# ✓ music_recommend_kafka
```

```bash
# 2. Проверьте API доступен
curl http://localhost:8000/

# Должен вернуть:
# {"message":"Music Recommendation System API","status":"running"}
```

```bash
# 3. Проверьте данные в БД
make db-stats

# Должно быть:
# users: 100000+
# tracks: 50000+
# interactions: 850000+
```

### Этап 2: Запустите smoke test

```bash
make load-test-smoke
```

**Если падает:**
- Система не готова к нагрузочному тестированию
- Переходите к [Этап 3: Анализ логов](#этап-3-анализ-логов)

**Если проходит:**
- Базовая функциональность работает
- Можно запускать полноценные тесты

### Этап 3: Анализ логов

```bash
# Проверьте ошибки в API
make logs-errors

# Или более детально
docker-compose logs -f api | grep ERROR
```

**Частые ошибки:**

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `ClickHouse client not connected` | БД недоступна | `make restart` |
| `Redis connection failed` | Кэш недоступен | Проверьте Redis |
| `KeyError: 'user_id'` | Нет данных | `make load-test-data-generate` |
| `500 Internal Server Error` | Ошибка в коде | Проверьте логи |
| `Connection pool exhausted` | Мало connections | Увеличьте pool |

### Этап 4: Диагностика производительности

```bash
make load-test-diagnostics
```

Анализируйте результаты:

**Если рекомендации медленные (>5s):**
```bash
# Проверьте Redis кэш
docker-compose exec redis redis-cli
> KEYS *recommendations*
> TTL recommendations:user:1

# Должны быть закэшированные ключи
```

**Если все endpoints медленные:**
```bash
# Проверьте ClickHouse
docker stats music_recommend_clickhouse

# Смотрите на CPU и Memory usage
# Если CPU > 80% - нужно больше ресурсов
```

### Этап 5: Проверка кэширования

```bash
# Запустите тест рекомендаций дважды
curl http://localhost:8000/api/v1/recommendations/1

# Первый запрос: ~2-5 секунд (вычисление)
# Второй запрос: ~50-100ms (из кэша)

# Если оба медленные - кэш не работает!
```

---

## 🛠️ Оптимизация

### 1️⃣ Оптимизация ClickHouse

#### Проверка индексов

```sql
-- Подключитесь к ClickHouse
docker exec -it music_recommend_clickhouse clickhouse-client

-- Проверьте структуру таблиц
SHOW CREATE TABLE music_recommend.user_track_interactions;

-- Проверьте размер таблиц
SELECT 
    table,
    formatReadableSize(sum(bytes)) as size
FROM system.parts
WHERE database = 'music_recommend'
GROUP BY table;
```

#### Оптимизация запросов

```sql
-- Включите логирование медленных запросов
SET log_queries = 1;
SET log_query_threads = 1;

-- Проверьте план выполнения
EXPLAIN SELECT * FROM music_recommend.users LIMIT 10;
```

### 2️⃣ Оптимизация Redis

```bash
# Проверьте использование памяти
docker exec music_recommend_redis redis-cli INFO memory

# Проверьте количество ключей
docker exec music_recommend_redis redis-cli DBSIZE

# Проверьте TTL политику
docker exec music_recommend_redis redis-cli CONFIG GET maxmemory-policy
```

**Настройки Redis (docker-compose.yml):**
```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### 3️⃣ Масштабирование API

#### Горизонтальное масштабирование

```yaml
# docker-compose.yml
api:
  deploy:
    replicas: 3  # Запустить 3 инстанса
```

#### Увеличение ресурсов

```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
```

#### Настройка connection pool

```python
# app/db/clickhouse.py
CLICKHOUSE_POOL_SIZE = 20  # Увеличить с 10

# app/services/cache_redis_client.py
REDIS_MAX_CONNECTIONS = 50  # Увеличить
```

### 4️⃣ Оптимизация кода

#### Асинхронная обработка

```python
# Используйте async/await для параллельных запросов
async def get_recommendations(user_id: int):
    # Параллельно получаем данные
    user_data, interactions = await asyncio.gather(
        get_user(user_id),
        get_user_interactions(user_id)
    )
```

#### Батчинг запросов

```python
# Вместо N запросов делайте 1
def get_users(ids: List[int]):
    return db.execute(
        "SELECT * FROM users WHERE user_id IN {ids}",
        {"ids": ids}
    )
```

#### Кэширование на уровне приложения

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user(user_id: int):
    # Кэш в памяти приложения
    return db.query(...)
```

---

## 📊 Мониторинг

### Grafana + Prometheus (рекомендуется)

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

### k6 Cloud (для нагрузочных тестов)

```bash
# Зарегистрируйтесь на grafana.com
k6 login cloud --token YOUR_TOKEN

# Запустите тест с отправкой метрик
k6 cloud load_tests/k6_basic_load_test.js
```

### Локальный мониторинг

```bash
# Метрики Docker контейнеров
docker stats

# Топ процессов в контейнере
docker exec music_recommend_api top

# Использование дискового пространства
docker system df
```

---

## 📈 Целевые показатели (SLA)

| Метрика | Хорошо ✅ | Норма ⚠️ | Плохо ❌ |
|---------|----------|---------|----------|
| **p95 latency** | < 1000ms | < 2000ms | > 5000ms |
| **p99 latency** | < 2000ms | < 5000ms | > 10000ms |
| **Error rate** | < 1% | < 5% | > 10% |
| **Throughput** | > 100 RPS | > 50 RPS | < 20 RPS |
| **Availability** | > 99.9% | > 99% | < 99% |

---

## 🎯 Чек-лист оптимизации

### Перед нагрузочным тестированием

- [ ] Все сервисы запущены и healthy
- [ ] Тестовые данные сгенерированы (1M+ записей)
- [ ] Smoke test проходит успешно
- [ ] Диагностический тест не показывает критичных проблем
- [ ] Логи API не содержат ошибок
- [ ] Redis доступен и кэширует данные
- [ ] ClickHouse отвечает быстро

### После выявления проблем

- [ ] Проверены и оптимизированы SQL запросы
- [ ] Добавлены индексы в ClickHouse
- [ ] Настроено кэширование Redis
- [ ] Увеличены connection pools
- [ ] Добавлены ресурсы Docker (CPU/RAM)
- [ ] Реализован батчинг запросов
- [ ] Добавлен мониторинг метрик

### Перед продакшеном

- [ ] Load test проходит с целевой нагрузкой
- [ ] Soak test (1 час) не показывает утечек памяти
- [ ] Spike test показывает устойчивость к пикам
- [ ] Настроен Grafana для мониторинга
- [ ] Настроены алерты на критичные метрики
- [ ] Документирована процедура масштабирования

---

## 💡 Полезные команды

```bash
# Быстрая диагностика
make diagnose                      # Общая диагностика
make load-test-diagnostics         # Детальная диагностика производительности
make db-stats                      # Статистика по данным в БД
make logs-errors                   # Последние ошибки из логов

# Управление сервисами
make restart                       # Перезапуск всех сервисов
make down && make up               # Полный рестарт
make logs-api                      # Логи API в реальном времени
make logs-clickhouse               # Логи ClickHouse

# Тестирование
make load-test-smoke               # Smoke test (быстрая проверка)
make load-test-basic               # Базовый нагрузочный тест
make load-test-spike               # Тест пиковой нагрузки
make load-test-stress              # Стресс-тест (поиск предела)
make load-test-soak                # Тест на выносливость (1 час)

# Очистка
make clean                         # Очистить кэши
make clean-all                     # Полная очистка (включая volumes)
```

---

## 🆘 Получить помощь

Если проблемы не решаются:

1. Соберите диагностическую информацию:
```bash
make diagnose > diagnosis.txt
make logs-errors > errors.txt
make db-stats > db_stats.txt
```

2. Запустите диагностический тест:
```bash
make load-test-diagnostics > diagnostics.txt
```

3. Проверьте [Troubleshooting Guide](TROUBLESHOOTING.md)

4. Создайте issue в репозитории с полной информацией

---

**Создано для:** Music Recommendation System  
**Версия:** 1.0.0  
**Последнее обновление:** 2025-11-10

