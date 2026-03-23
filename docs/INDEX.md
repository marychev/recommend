# Документация

Полная документация для Music Recommendation System.

## Основные документы

### Для начинающих
- **[README.md](../README.md)** - Начните отсюда! Общий обзор проекта
- **[SUMMARY.md](SUMMARY.md)** - Краткая сводка проекта
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Быстрая справка (команды, URL)
- **[MAKEFILE.md](MAKEFILE.md)** - Полное руководство по Makefile
- **[TECHNICAL_REQUIREMENTS.md](TECHNICAL_REQUIREMENTS.md)** - Техническое задание

### Инфраструктура
- **[CLICKHOUSE.md](CLICKHOUSE.md)** - ClickHouse: оптимизация, индексы, партиционирование
- **[KAFKA.md](KAFKA.md)** - Kafka: архитектура, конфигурация, батчинг
- **[CACHING.md](CACHING.md)** - Redis: кэширование, инвалидация, warmup
- **[DB_INIT.md](DB_INIT.md)** - Инициализация базы данных
- **[PORTS.md](PORTS.md)** - Справочник по портам сервисов

### Тестирование и диагностика
- **[TESTING.md](TESTING.md)** - Запуск тестов (unit, Kafka, нагрузочные)
- **[PIPELINE_BENCHMARK.md](PIPELINE_BENCHMARK.md)** - Бенчмарк Kafka→ClickHouse (3 решения, результаты, баги)
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Решение проблем и диагностика

### Разработка
- **[ACTION_TYPES.md](ACTION_TYPES.md)** - Enum типов действий
- **[CODE_REVIEW.md](CODE_REVIEW.md)** - Code review
- **[GIT_SETUP.md](GIT_SETUP.md)** - Настройка Git
- **[POST_OPTIMIZATION_BEST_PRACTICES.md](POST_OPTIMIZATION_BEST_PRACTICES.md)** - Оптимизация POST запросов
- **[SYSTEM_SPECIFICATIONS.md](SYSTEM_SPECIFICATIONS.md)** - Спецификации системы
- **[WSL_SWAP.md](WSL_SWAP.md)** - Отключение подкачки (swap) в WSL

## Структура документации

```
docs/
├── INDEX.md                              # Этот файл - навигация
├── SUMMARY.md                            # Краткая сводка
├── QUICK_REFERENCE.md                    # Быстрая справка
├── MAKEFILE.md                           # Руководство по Makefile
├── TECHNICAL_REQUIREMENTS.md             # Техническое задание
├── CLICKHOUSE.md                         # ClickHouse (объединённый)
├── KAFKA.md                              # Kafka (объединённый)
├── CACHING.md                            # Redis кэширование (объединённый)
├── TESTING.md                            # Тестирование (объединённый)
├── PIPELINE_BENCHMARK.md                 # Бенчмарк Kafka→ClickHouse
├── TROUBLESHOOTING.md                    # Диагностика (объединённый)
├── PORTS.md                              # Справочник портов
├── DB_INIT.md                            # Инициализация БД
├── ACTION_TYPES.md                       # Типы действий
├── CODE_REVIEW.md                        # Code review
├── GIT_SETUP.md                          # Настройка Git
├── POST_OPTIMIZATION_BEST_PRACTICES.md   # Оптимизация POST
└── SYSTEM_SPECIFICATIONS.md              # Спецификации системы
```

## Быстрая навигация

### Я хочу...

**...запустить проект**
1. `make up` — запустить сервисы
2. `make db-init` — заполнить БД данными
3. `make health` — проверить API
4. См. [MAKEFILE.md](MAKEFILE.md) для всех команд

**...запустить тесты**
→ [TESTING.md](TESTING.md) или `make test`

**...понять архитектуру**
→ [TECHNICAL_REQUIREMENTS.md](TECHNICAL_REQUIREMENTS.md)

**...настроить ClickHouse**
→ [CLICKHOUSE.md](CLICKHOUSE.md) | [DB_INIT.md](DB_INIT.md) | [PORTS.md](PORTS.md)

**...использовать Kafka**
→ [KAFKA.md](KAFKA.md) | `make logs-kafka`

**...настроить кэширование**
→ [CACHING.md](CACHING.md) | `make diagnose-cache`

**...решить проблему**
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | `make diagnose`

---

**Вернуться к**: [Главная](../README.md)
