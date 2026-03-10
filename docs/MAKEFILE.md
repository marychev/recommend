# Makefile - Полное руководство

Все команды для управления проектом Music Recommendation System.

## Быстрый старт

```bash
make up           # Запустить все сервисы
make help         # Посмотреть все команды
make info         # Информация о проекте
```

---

## Docker команды

### Запуск сервисов

```bash
make up              # Запустить ВСЕ сервисы
make up-clickhouse   # Только ClickHouse
make up-kafka        # Только Kafka + Zookeeper
make up-redis        # Только Redis
```

### Остановка и перезапуск

```bash
make down            # Остановить все сервисы
make rebuild         # Пересобрать и перезапустить все
make restart-api     # Перезапустить только API
```

### Статус и информация

```bash
make ps              # Показать статус контейнеров
make status          # Статус контейнеров + health check
make urls            # Показать URLs всех сервисов
make info            # Полная информация о проекте
```

### Сборка образов

```bash
make build           # Собрать Docker образы
make rebuild         # Пересобрать и перезапустить
```

---

## База данных

### Инициализация

```bash
make db-init         # Заполнить БД тестовыми данными (seed_data.py)
make db-reset        # Пересоздать ClickHouse с нуля (данные удаляются!)
```

### Оптимизация

```bash
make db-indexes      # Добавить индексы (safe_add_indexes.sh)
make db-optimize     # Оптимизировать таблицы (OPTIMIZE TABLE FINAL)
make fix-clickhouse  # Восстановить ClickHouse после проблем
make diagnose-performance  # Диагностика производительности
```

### Просмотр

```bash
make db-shell        # Открыть clickhouse-client
make db-tables       # Показать список таблиц
make db-stats        # Статистика: размер и количество строк
```

---

## Тестирование

### Основные тесты

```bash
make test            # Запустить все тесты
make test-clickhouse # Только тесты ClickHouse
make test-kafka      # Только тесты Kafka
make test-api        # Только тесты API
make test-cache      # Только тесты кэша
```

### Специальные тесты

```bash
make test-ttl-optimization  # Тест оптимизации TTL
make test-cache-warmup      # Тест прогрева кэша
make test-api-health        # Проверка здоровья API
```

### Нагрузочное тестирование (k6)

```bash
make load-test-install       # Проверка установки k6
make load-test-data-generate # Сгенерировать данные для тестов
make load-test-quick         # Быстрая проверка (30 сек)
make load-test-smoke         # Smoke test (~2 мин)
make load-test-diagnostics   # Диагностика производительности (1 мин)
make load-test-basic         # Базовый тест (~15 мин)
make load-test-spike         # Пиковая нагрузка 200 VUs (~2 мин)
make load-test-spike-extreme # Экстремальный spike 500 VUs
make load-test-stress        # Стресс-тест (~30 мин)
make load-test-soak          # Тест на выносливость (~70 мин)
make load-test-post          # Тест POST запросов (~5 мин)
make load-test-post-quick    # Быстрый тест POST (1 мин)
make load-test-recommendations      # Анализ рекомендаций (~11 мин)
make load-test-events-post          # Тест POST /events
make load-test-tracks-post          # Тест POST /tracks
make load-test-users-post           # Тест POST /users
make load-test-recommendations-post # Тест POST /recommendations
make measure-insert-lag             # Лаг вставки в ClickHouse (k6)
make measure-insert-lag-python      # Лаг вставки (Python скрипт)
make load-test-results              # Показать результаты тестов
```

---

## Логи и диагностика

### Просмотр логов

```bash
make logs            # Все сервисы (follow)
make logs-api        # Только API
make logs-clickhouse # Только ClickHouse
make logs-kafka      # Только Kafka
make logs-redis      # Только Redis
make logs-errors     # Только ошибки из API
```

### Диагностика

```bash
make diagnose        # Полная диагностика (API, БД, данные)
make diagnose-system # Комплексная диагностика (Docker, Kafka, ClickHouse, Redis)
make diagnose-cache  # Диагностика кэширования Redis
make diagnose-cache-curl  # Диагностика кэширования через curl
make health          # Health check API
make check-services  # Проверить все сервисы
```

---

## Качество кода

```bash
make lint            # Проверить код (flake8 + black)
make lint-install    # Установить линтеры
make format          # Автоформатирование (black + trailing whitespace)
```

---

## Очистка

```bash
make clean           # Удалить кэши и __pycache__
make clean-all       # Полная очистка + контейнеры + volumes
```

---

## Таблица всех команд

### Docker

| Команда | Описание |
|---------|----------|
| `make up` | Запустить все сервисы |
| `make down` | Остановить все сервисы |
| `make rebuild` | Пересобрать и перезапустить |
| `make restart-api` | Перезапустить только API |
| `make ps` | Статус контейнеров |
| `make status` | Статус + health check |
| `make build` | Собрать образы |
| `make shell` | Shell в API контейнере |
| `make up-clickhouse` | Запустить ClickHouse |
| `make up-kafka` | Запустить Kafka |
| `make up-redis` | Запустить Redis |

### База данных

| Команда | Описание |
|---------|----------|
| `make db-init` | Заполнить БД тестовыми данными |
| `make db-indexes` | Добавить индексы |
| `make db-optimize` | Оптимизировать таблицы |
| `make db-reset` | Пересоздать ClickHouse |
| `make db-shell` | Открыть clickhouse-client |
| `make db-tables` | Показать таблицы |
| `make db-stats` | Статистика таблиц |
| `make fix-clickhouse` | Восстановить ClickHouse |
| `make diagnose-performance` | Диагностика производительности |

### Тестирование

| Команда | Описание |
|---------|----------|
| `make test` | Запустить все тесты |
| `make test-clickhouse` | Только ClickHouse тесты |
| `make test-kafka` | Только Kafka тесты |
| `make test-api` | Только API тесты |
| `make test-cache` | Только тесты кэша |
| `make test-ttl-optimization` | Тест оптимизации TTL |
| `make test-cache-warmup` | Тест прогрева кэша |
| `make test-api-health` | Проверка здоровья API |

### Логи и диагностика

| Команда | Описание |
|---------|----------|
| `make logs` | Все сервисы |
| `make logs-api` | Только API |
| `make logs-clickhouse` | Только ClickHouse |
| `make logs-kafka` | Только Kafka |
| `make logs-redis` | Только Redis |
| `make logs-errors` | Только ошибки |
| `make diagnose` | Полная диагностика |
| `make diagnose-system` | Комплексная диагностика |
| `make diagnose-cache` | Диагностика кэша |
| `make health` | Health check API |
| `make check-services` | Проверить сервисы |

### Качество кода

| Команда | Описание |
|---------|----------|
| `make lint` | Проверка кода |
| `make lint-install` | Установить линтеры |
| `make format` | Автоформатирование |

### Очистка

| Команда | Описание |
|---------|----------|
| `make clean` | Кэши и __pycache__ |
| `make clean-all` | Полная очистка + volumes |

### Информация

| Команда | Описание |
|---------|----------|
| `make help` | Справка по командам |
| `make info` | Информация о проекте |
| `make urls` | URLs сервисов |

---

## Примеры сценариев

### Первый запуск

```bash
make up              # Запустить сервисы
make db-init         # Заполнить БД данными
make health          # Проверить API
```

### Перезапуск после изменений кода

```bash
make rebuild         # Пересобрать и перезапустить
```

### Отладка проблем

```bash
make diagnose        # Полная диагностика
make logs-errors     # Смотреть ошибки
make db-stats        # Проверить данные
```

### Разработка с тестами

```bash
make format          # Отформатировать
make lint            # Проверить стиль
make test            # Запустить тесты
```

### Полная очистка и перезапуск

```bash
make clean-all       # Удалить всё
make up              # Запустить сервисы
make db-init         # Заполнить данные
```

---

## Порты

| Сервис | Порт | URL |
|--------|------|-----|
| API | 8000 | http://localhost:8000 |
| Swagger | 8000 | http://localhost:8000/docs |
| ClickHouse HTTP | 8123 | http://localhost:8123 |
| ClickHouse Native | 9000 | - |
| Kafka | 9092 | - |
| Kafka Internal | 29092 | - |
| Redis | 6379 | - |
| Zookeeper | 2181 | - |

---

## Связанные документы

- [README.md](../README.md) - Главная документация
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Быстрая справка
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Решение проблем
- [TESTING.md](TESTING.md) - Тестирование
