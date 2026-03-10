# Документация Music Recommendation System

Добро пожаловать в документацию проекта!

## Быстрый старт

```bash
make up        # Запустить сервисы
make db-init   # Заполнить БД данными
make health    # Проверить API
```

## Все документы

### Основные
- **[INDEX.md](INDEX.md)** - Полный указатель документации
- **[SUMMARY.md](SUMMARY.md)** - Краткая сводка проекта
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Быстрая справка
- **[MAKEFILE.md](MAKEFILE.md)** - Руководство по Makefile
- **[TECHNICAL_REQUIREMENTS.md](TECHNICAL_REQUIREMENTS.md)** - Техническое задание

### Инфраструктура
- **[CLICKHOUSE.md](CLICKHOUSE.md)** - ClickHouse (оптимизация, индексы, партиционирование)
- **[KAFKA.md](KAFKA.md)** - Kafka (архитектура, батчинг, мониторинг)
- **[CACHING.md](CACHING.md)** - Redis (кэширование, инвалидация, warmup)
- **[PORTS.md](PORTS.md)** - Справочник портов
- **[DB_INIT.md](DB_INIT.md)** - Инициализация БД

### Тестирование и диагностика
- **[TESTING.md](TESTING.md)** - Тестирование (unit, Kafka, нагрузочные)
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Решение проблем

### Разработка
- **[ACTION_TYPES.md](ACTION_TYPES.md)** - Типы действий
- **[CODE_REVIEW.md](CODE_REVIEW.md)** - Code review
- **[GIT_SETUP.md](GIT_SETUP.md)** - Настройка Git

## По задачам

**Хочу запустить проект:**
→ [../README.md](../README.md) → `make up && make db-init`

**Хочу запустить тесты:**
→ [TESTING.md](TESTING.md) или `make test`

**Хочу понять архитектуру:**
→ [TECHNICAL_REQUIREMENTS.md](TECHNICAL_REQUIREMENTS.md)

**Хочу настроить ClickHouse:**
→ [CLICKHOUSE.md](CLICKHOUSE.md) → [DB_INIT.md](DB_INIT.md)

**Хочу использовать Kafka:**
→ [KAFKA.md](KAFKA.md)

**Хочу настроить кэширование:**
→ [CACHING.md](CACHING.md)

**Проблема — что-то не работает:**
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md) или `make diagnose`

---

**Вернуться к**: [Главная](../README.md) | [Полный указатель](INDEX.md)
