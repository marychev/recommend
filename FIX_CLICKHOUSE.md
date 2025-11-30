# 🔧 Исправление проблемы с ClickHouse

## ✅ Что было исправлено

1. ✅ Убраны проблемные параметры ресурсов из `docker-compose.yml` (mem_limit, cpus)
2. ✅ Временно отключен `performance.xml` в `docker-compose.yml` для диагностики
3. ✅ Сохранены оптимизации в `users.xml` (они работают!)
4. ✅ Создан скрипт автоматического восстановления

## 🚀 Быстрое восстановление (1 команда)

### ⚡ Автоматическое восстановление (РЕКОМЕНДУЕТСЯ)

```bash
# В WSL или Linux:
make fix-clickhouse

# Или напрямую:
bash scripts/fix_clickhouse.sh
```

**Что делает скрипт:**
1. Останавливает контейнер ClickHouse
2. Удаляет контейнер (данные сохраняются)
3. Запускает заново
4. Ждет 15 секунд для инициализации
5. Проверяет подключение

### Вариант 2: Ручное восстановление

```bash
# 1. Остановите контейнер
docker compose stop clickhouse

# 2. Удалите контейнер (данные сохраняются)
docker compose rm -f clickhouse

# 3. Запустите заново
docker compose up -d clickhouse

# 4. Подождите 15 секунд
sleep 15

# 5. Проверьте
curl http://localhost:8123/
```

### 2. Проверьте, что ClickHouse запустился

```bash
# Проверьте логи
docker compose logs clickhouse --tail 50

# Проверьте подключение
curl http://localhost:8123/
```

Должно вернуть: `Ok.`

### 3. Проверьте настройки

```bash
# Проверить настройки памяти
docker exec music_recommend_clickhouse clickhouse-client --query "
SELECT name, value
FROM system.settings
WHERE name IN ('max_memory_usage', 'max_threads', 'max_insert_block_size')
"
```

### 4. Запустите тесты

```bash
# Тесты ClickHouse
make test-clickhouse

# Или напрямую
pytest tests/clickhouse/ -v
```

## 🔍 Если проблема осталась

### Вариант 1: Временно отключить performance.xml

Если проблема в конфигурации, временно отключите performance.xml:

```bash
# Закомментируйте строку в docker-compose.yml:
# - ./clickhouse-config/performance.xml:/etc/clickhouse-server/config.d/performance.xml:ro

# Перезапустите
docker compose restart clickhouse
```

### Вариант 2: Проверить логи на ошибки

```bash
# Полные логи
docker compose logs clickhouse

# Искать ошибки
docker compose logs clickhouse | grep -i error
```

### Вариант 3: Пересоздать контейнер ClickHouse

```bash
# Остановить и удалить контейнер
docker compose stop clickhouse
docker compose rm -f clickhouse

# Запустить заново
docker compose up -d clickhouse

# Подождать 10-15 секунд для инициализации
sleep 15

# Проверить
curl http://localhost:8123/
```

## 📝 Что осталось из оптимизаций

✅ **Оптимизации в users.xml:**
- max_memory_usage: 2GB
- max_memory_usage_for_all_queries: 4GB
- max_bytes_before_external_group_by: 1GB
- max_bytes_before_external_sort: 1GB
- max_threads: 4
- use_uncompressed_cache: 1
- max_insert_block_size: 1MB

✅ **Оптимизации в performance.xml (упрощенные):**
- Те же настройки памяти
- Кэширование включено
- Оптимизация потоков

## ⚠️ Важно

Лимиты ресурсов Docker теперь настраиваются только через **Docker Desktop Settings → Resources**, а не через docker-compose.yml.

---

**После исправления:** Запустите `make test-clickhouse` для проверки.

