# 🚀 Оптимизация ClickHouse для слабых компьютеров

Руководство по оптимизации ClickHouse для работы на компьютерах с ограниченными ресурсами.

## 📊 Текущие настройки

### Docker ресурсы (docker-compose.yml)

**Важно:** Лимиты в docker-compose.yml работают только если Docker Desktop имеет достаточно ресурсов. Сначала настройте Docker Desktop!

**ClickHouse:**
- CPU: 1-2 ядра (минимум 1, максимум 2)
- RAM: 2-4GB (минимум 2GB, максимум 4GB)

**Kafka:**
- CPU: 0.5-1 ядро
- RAM: 512MB-1GB

**Redis:**
- CPU: 0.25-0.5 ядра
- RAM: 256MB-512MB

**Примечание:** В docker-compose.yml используются параметры `mem_limit`, `mem_reservation` и `cpus` для ограничения ресурсов каждого контейнера.

### ClickHouse конфигурация

**Файлы:**
- `clickhouse-config/users.xml` - настройки пользователей и профилей
- `clickhouse-config/performance.xml` - оптимизация производительности

## ⚙️ Оптимизации

### 1. Память

```xml
<!-- Максимальная память на один запрос: 2GB -->
<max_memory_usage>2000000000</max_memory_usage>

<!-- Максимальная память для всех запросов: 4GB -->
<max_memory_usage_for_all_queries>4000000000</max_memory_usage_for_all_queries>

<!-- Использовать диск при превышении памяти -->
<max_bytes_before_external_group_by>1000000000</max_bytes_before_external_group_by>
<max_bytes_before_external_sort>1000000000</max_bytes_before_external_sort>
```

**Что это дает:**
- Предотвращает исчерпание памяти
- Автоматически использует диск для больших запросов
- Позволяет обрабатывать больше запросов параллельно

### 2. Вставки (INSERT)

```xml
<!-- Размер блока для вставки: 1MB -->
<max_insert_block_size>1048576</max_insert_block_size>
```

**Что это дает:**
- Быстрее вставка данных
- Меньше накладных расходов
- Лучшая производительность POST запросов

### 3. Потоки

```xml
<!-- Максимум 4 потока для запросов -->
<max_threads>4</max_threads>
```

**Что это дает:**
- Не перегружает CPU
- Оптимально для 2-4 ядерных процессоров
- Баланс между производительностью и нагрузкой

### 4. Кэширование

```xml
<!-- Кэш несжатых данных: 512MB -->
<uncompressed_cache_size>536870912</uncompressed_cache_size>
<use_uncompressed_cache>1</use_uncompressed_cache>
```

**Что это дает:**
- Ускорение повторных запросов
- Меньше нагрузки на диск
- Быстрее чтение данных

### 5. Сжатие

```xml
<compression>
    <method>lz4</method>
</compression>
```

**Что это дает:**
- Быстрое сжатие (lz4 быстрее чем zstd)
- Меньше места на диске
- Быстрее вставки данных

## 🔧 Настройка Docker Desktop

### Для Windows/Mac:

1. Откройте **Docker Desktop**
2. Перейдите в **Settings → Resources**
3. Установите:
   - **Memory:** минимум 8GB (рекомендуется 12GB)
   - **CPUs:** минимум 4 ядра (рекомендуется 6-8)
   - **Swap:** 2GB
   - **Disk image size:** 50GB+

4. Нажмите **Apply & Restart**

### Для Linux:

Docker использует все доступные ресурсы системы. Убедитесь, что:
- RAM: минимум 8GB
- CPU: минимум 4 ядра
- Swap: 2-4GB

## 📈 Мониторинг производительности

### Проверка использования ресурсов:

```bash
# Статистика контейнеров
docker stats

# Логи ClickHouse
docker-compose logs clickhouse | tail -50

# Медленные запросы
docker exec music_recommend_clickhouse clickhouse-client --query "
SELECT query, query_duration_ms, read_rows, read_bytes
FROM system.query_log
WHERE type = 'QueryFinish' AND query_duration_ms > 1000
ORDER BY query_duration_ms DESC
LIMIT 10
"
```

### Проверка настроек:

```bash
# Проверить текущие настройки памяти
docker exec music_recommend_clickhouse clickhouse-client --query "
SELECT name, value
FROM system.settings
WHERE name LIKE '%memory%' OR name LIKE '%thread%'
ORDER BY name
"
```

## 🎯 Best Practices

### 1. Батчинг INSERT

**Плохо:**
```python
for item in items:
    await clickhouse.insert("table", [[item]])
```

**Хорошо:**
```python
await clickhouse.insert("table", [[item] for item in items])
```

### 2. Использование LIMIT

Всегда добавляйте LIMIT в SELECT запросы:
```sql
SELECT * FROM users WHERE age > 18 LIMIT 1000
```

### 3. Индексы

Убедитесь, что есть индексы на часто используемых полях:
```sql
ALTER TABLE user_track_interactions 
ADD INDEX idx_user_id user_id TYPE minmax GRANULARITY 4;
```

### 4. Партиционирование

Используйте партиционирование для больших таблиц:
```sql
PARTITION BY toYYYYMM(timestamp)
```

### 5. Кэширование в Redis

Кэшируйте результаты тяжелых запросов:
- Рекомендации: TTL 1 час
- Статистика: TTL 5-10 минут
- Списки: TTL 1-5 минут

## 🔍 Troubleshooting

### Проблема: Медленные POST запросы

**Решение:**
1. Проверьте использование памяти: `docker stats`
2. Увеличьте `max_insert_block_size` в `performance.xml`
3. Убедитесь, что есть индексы
4. Проверьте логи: `docker-compose logs clickhouse | grep ERROR`

### Проблема: Нехватка памяти

**Решение:**
1. Уменьшите `max_memory_usage` в `users.xml`
2. Увеличьте `max_bytes_before_external_group_by`
3. Увеличьте RAM в Docker Desktop
4. Закройте другие приложения

### Проблема: Медленные SELECT запросы

**Решение:**
1. Добавьте LIMIT в запросы
2. Используйте индексы
3. Проверьте партиционирование
4. Включите кэширование: `use_uncompressed_cache=1`

## 📚 Дополнительные ресурсы

- [ClickHouse Performance Tuning](https://clickhouse.com/docs/en/operations/performance/)
- [ClickHouse Best Practices](https://clickhouse.com/docs/en/guides/best-practices/)
- [Docker Resource Limits](https://docs.docker.com/config/containers/resource_constraints/)

---

**Дата создания:** 2025-11-30  
**Версия:** 1.0.0

