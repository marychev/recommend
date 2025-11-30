# 🔧 Исправление проблемы с памятью ClickHouse

## ❌ Критическая проблема

**Ошибка:** `MEMORY_LIMIT_EXCEEDED` - запросы превышают лимит памяти (4.20 GiB)

**Симптомы:**
- Запросы рекомендаций падают с ошибкой памяти
- Fallback на популярные треки тоже падает
- p95 время ответа: 19039ms (19 секунд!)

## ✅ Что исправлено

### 1. Увеличены лимиты памяти в `users.xml`:

```xml
<max_memory_usage>6000000000</max_memory_usage> <!-- 6GB -->
<max_memory_usage_for_all_queries>8000000000</max_memory_usage_for_all_queries> <!-- 8GB -->
```

### 2. Включена внешняя сортировка/группировка:

```xml
<max_bytes_before_external_group_by>2000000000</max_bytes_before_external_group_by> <!-- 2GB -->
<max_bytes_before_external_sort>2000000000</max_bytes_before_external_sort> <!-- 2GB -->
```

Это позволяет ClickHouse использовать диск, когда память заканчивается.

### 3. Оптимизированы настройки JOIN:

```xml
<max_bytes_in_join>1000000000</max_bytes_in_join> <!-- 1GB -->
```

### 4. Обновлены настройки в запросах:

В `app/routers/recommendations.py`:
- `max_memory_usage`: 2GB → 5GB
- `max_bytes_before_external_group_by`: 1GB → 2GB
- `max_bytes_before_external_sort`: добавлено 2GB
- `max_bytes_in_join`: добавлено 1GB

## 🚀 Что нужно сделать

### 1. Перезапустить ClickHouse:

```bash
docker compose restart clickhouse
```

Или пересоздать контейнер:
```bash
docker compose stop clickhouse
docker compose rm -f clickhouse
docker compose up -d clickhouse
sleep 15
```

### 2. Проверить, что настройки применились:

```bash
docker exec music_recommend_clickhouse clickhouse-client -q "
    SELECT name, value
    FROM system.settings
    WHERE name IN (
        'max_memory_usage',
        'max_memory_usage_for_all_queries',
        'max_bytes_before_external_group_by',
        'max_bytes_before_external_sort'
    )
"
```

Должно показать новые значения.

### 3. Запустить тест снова:

```bash
make load-test-post-quick
```

## 📊 Ожидаемые улучшения

**До:**
- ❌ Запросы падают с `MEMORY_LIMIT_EXCEEDED`
- ❌ p95: 19039ms
- ❌ Fallback тоже падает

**После:**
- ✅ Запросы выполняются без ошибок памяти
- ✅ p95: < 5000ms (ожидаемо)
- ✅ Fallback работает

## ⚠️ Важно

1. **Увеличение памяти** - это временное решение
2. **Нужно оптимизировать запросы** - они все еще медленные
3. **Внешняя сортировка** - будет медленнее, но не упадет

## 🔄 Дальнейшие шаги

После исправления памяти нужно:
1. Оптимизировать JOIN запросы (см. `PERFORMANCE_ISSUES.md`)
2. Добавить индексы на `user_track_matrix`
3. Кэшировать прослушанные треки

---

**Следующий шаг:** Перезапустите ClickHouse и проверьте работу!

