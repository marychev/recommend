# 🖥️ Характеристики системы для тестирования

Документ описывает характеристики железа и настройки системы, на которой выполняется тестирование Music Recommendation System.

---

## 📊 Общая информация о системе

### Платформа
- **ОС**: Windows 10/11 (версия 10.0.19045)
- **Среда выполнения**: WSL2 (Ubuntu)
- **Рабочая директория**: `/Ubuntu/home/recommend`
- **Shell**: PowerShell (Windows) + Bash (WSL)

### Особенности окружения
- Система оптимизирована для работы на **слабых компьютерах** с ограниченными ресурсами
- Используется Docker Desktop для контейнеризации сервисов
- Все сервисы запускаются в Docker контейнерах через `docker-compose`

---

## ⚙️ Рекомендуемые характеристики системы

### Минимальные требования (из документации)

**Для Docker Desktop (Windows/Mac):**
- **RAM**: минимум 8GB (рекомендуется 12GB)
- **CPU**: минимум 4 ядра (рекомендуется 6-8)
- **Swap**: 2GB
- **Disk image size**: 50GB+

**Для Linux (WSL2):**
- **RAM**: минимум 8GB
- **CPU**: минимум 4 ядра
- **Swap**: 2-4GB

### Текущие настройки Docker Desktop

Согласно документации `docs/CLICKHOUSE.md`, система настроена для работы на компьютерах с ограниченными ресурсами. Рекомендуемые настройки в Docker Desktop:

```
Settings → Resources:
├── Memory:         минимум 8GB (рекомендуется 12GB)
├── CPUs:           минимум 4 ядра (рекомендуется 6-8)
├── Swap:           2GB
└── Disk image size: 50GB+
```

---

## 🐳 Лимиты ресурсов контейнеров

### ClickHouse
- **CPU**: 1-2 ядра (минимум 1, максимум 2)
- **RAM**: 2-4GB (минимум 2GB, максимум 4GB) - лимит контейнера
- **Конфигурация памяти** (из `clickhouse-config/users.xml`):
  - Максимальная память на один запрос: **2GB** (оптимизировано под 4-6GB RAM)
  - Максимальная память для всех запросов: **3GB**
  - Использование диска при превышении памяти: включено (500MB для group_by и sort)
  - Максимальные строки в JOIN: 5,000,000
  - Максимальные байты в JOIN: 1GB
- **Алгоритм JOIN**: auto (автоматический выбор)

### Kafka
- **CPU**: 0.5-1 ядро
- **RAM**: 512MB-1GB
- **Версия**: 7.5.0 (Confluent Platform)
- **Zookeeper**: требуется для работы

### Redis
- **CPU**: 0.25-0.5 ядра
- **RAM**: 256MB-512MB
- **Максимальная память**: 256MB
- **Политика**: `allkeys-lru`
- **Версия**: 7-alpine

### API (FastAPI)
- **Контейнер**: `music_recommend_api`
- **Порт**: 8000
- **Лимиты**:
  - Concurrency: 1000
  - Max requests: 10000
  - Timeout keep-alive: 65s
  - Timeout graceful shutdown: 30s

---

## 💾 Конфигурация ClickHouse

### Настройки памяти (из `clickhouse-config/users.xml`)

**Текущие настройки (актуальные, из `clickhouse-config/users.xml`):**

```xml
<!-- Лимиты памяти (адаптировано под 4-6GB RAM) -->
<max_memory_usage>2000000000</max_memory_usage> <!-- 2GB на один запрос -->
<max_memory_usage_for_all_queries>3000000000</max_memory_usage_for_all_queries> <!-- 3GB на все запросы -->

<!-- Использовать диск при превышении памяти (раннее срабатывание для экономии RAM) -->
<max_bytes_before_external_group_by>500000000</max_bytes_before_external_group_by> <!-- 500MB -->
<max_bytes_before_external_sort>500000000</max_bytes_before_external_sort> <!-- 500MB -->

<!-- Оптимизация для JOIN операций -->
<join_algorithm>auto</join_algorithm>
<max_rows_in_join>5000000</max_rows_in_join>
<max_bytes_in_join>1000000000</max_bytes_in_join> <!-- 1GB -->
```

**Примечание:** Настройки памяти оптимизированы под WSL2 с 5.8GB RAM. Раннее срабатывание external group by/sort (500MB) позволяет избежать OOM при нагрузочных тестах.

### Дополнительные настройки производительности

(Если используются в `clickhouse-config/performance.xml`):

```xml
<!-- Размер блока для вставки: 1MB -->
<max_insert_block_size>1048576</max_insert_block_size>

<!-- Максимум 4 потока для запросов -->
<max_threads>4</max_threads>

<!-- Кэш несжатых данных: 512MB -->
<uncompressed_cache_size>536870912</uncompressed_cache_size>
<use_uncompressed_cache>1</use_uncompressed_cache>

<!-- Сжатие: lz4 (быстрое) -->
<compression>
    <method>lz4</method>
</compression>
```

---

## 📈 Мониторинг ресурсов

### Команды для проверки характеристик

```bash
# Статистика контейнеров
docker stats

# Проверка использования ресурсов
docker stats --no-stream

# Информация о системе (Linux/WSL)
lscpu          # Информация о CPU
free -h        # Информация о памяти
df -h          # Информация о диске

# Проверка настроек ClickHouse
docker exec music_recommend_clickhouse clickhouse-client --query "
SELECT name, value
FROM system.settings
WHERE name LIKE '%memory%' OR name LIKE '%thread%'
ORDER BY name
"
```

### Скрипт для получения информации о системе

Создан скрипт `scripts/get_system_info.py` для автоматического сбора информации о системе:

```bash
python3 scripts/get_system_info.py
```

Скрипт выводит:
- Информацию о платформе (ОС, версия, архитектура)
- Характеристики CPU (количество ядер, частота, загрузка)
- Информацию о памяти (RAM, Swap)
- Информацию о диске
- Статистику Docker контейнеров (если доступна)

---

## 🎯 Оптимизации для слабых компьютеров

### Примененные оптимизации

1. **Ограничение ресурсов контейнеров** - каждый контейнер имеет лимиты CPU и RAM
2. **Настройка ClickHouse** - оптимизированы параметры памяти и потоков
3. **Использование диска** - при превышении памяти данные обрабатываются на диске
4. **Кэширование** - включен кэш несжатых данных для ускорения запросов
5. **Сжатие lz4** - быстрое сжатие данных для экономии места

### Рекомендации при проблемах производительности

**Если система медленная:**
- Убедитесь, что Docker Desktop имеет достаточно ресурсов (8GB+ RAM, 4+ CPU)
- Проверьте использование ресурсов: `docker stats`
- Увеличьте лимиты в Docker Desktop Settings → Resources

**Если нехватка памяти:**
- Уменьшите `max_memory_usage` в `clickhouse-config/users.xml`
- Увеличьте `max_bytes_before_external_group_by` для использования диска
- Закройте другие приложения

**Если медленные запросы:**
- Проверьте индексы в ClickHouse
- Используйте LIMIT в SELECT запросах
- Включите кэширование в Redis

---

## 📝 Примечания

### Особенности тестирования на WSL2

Согласно документации `load_tests/README.md`:
- Spike тесты могут не проходить на слабом железе (< 8GB RAM, < 4 CPU cores)
- Docker контейнерам может быть выделено мало ресурсов
- Рекомендуется запускать тесты с уменьшенной нагрузкой (50 VUs вместо 500)

### Проверка реальных характеристик

Для получения актуальных характеристик вашей системы выполните:

```bash
# В WSL/Ubuntu
python3 scripts/get_system_info.py

# Или вручную
wsl lscpu
wsl free -h
wsl df -h
docker stats --no-stream
```

---

## 📚 Связанные документы

- `docs/CLICKHOUSE.md` - Детальная оптимизация ClickHouse
- `docs/TECHNICAL_REQUIREMENTS.md` - Технические требования проекта
- `load_tests/README.md` - Документация по нагрузочному тестированию
- `load_tests/DIAGNOSTICS_GUIDE.md` - Руководство по диагностике производительности
- `docker-compose.yml` - Конфигурация Docker контейнеров
- `clickhouse-config/users.xml` - Конфигурация ClickHouse

---

**Дата создания:** 2025-01-27  
**Версия:** 1.0.0
