# 📚 Документация

Полная документация для Music Recommendation System.

## 📖 Основные документы

### Для начинающих
- 🚀 **[README.md](../README.md)** - Начните отсюда! Общий обзор проекта
- 📊 **[SUMMARY.md](SUMMARY.md)** - Краткая сводка проекта
- ⚡ **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Быстрая справка (команды, URL)
- 📝 **[MAKEFILE.md](MAKEFILE.md)** - Полное руководство по Makefile
- 📋 **[TECHNICAL_REQUIREMENTS.md](TECHNICAL_REQUIREMENTS.md)** - Техническое задание

### База данных и инфраструктура
- 🗄️ **[DB_INIT.md](DB_INIT.md)** - Инициализация базы данных
- 🔌 **[PORTS.md](PORTS.md)** - Справочник по портам сервисов
- 📨 **[KAFKA_INTEGRATION.md](KAFKA_INTEGRATION.md)** - Интеграция с Kafka
- ⚡ **[REDIS_CACHING.md](REDIS_CACHING.md)** - Кэширование рекомендаций

### Тестирование
- 🧪 **[RUN_TESTS.md](RUN_TESTS.md)** - Как запускать тесты

### Troubleshooting
- 🚨 **[API_ERROR_500.md](API_ERROR_500.md)** - Решение ошибки 500
- 🆘 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Общее решение проблем

### Разработка
- ✨ **[CODE_QUALITY.md](CODE_QUALITY.md)** - Качество кода
- 🎯 **[ACTION_TYPES.md](ACTION_TYPES.md)** - Enum типов действий
- 🔐 **[GIT_SETUP.md](GIT_SETUP.md)** - Настройка Git

## 🗂️ Структура документации

```
docs/
├── INDEX.md                    # Этот файл - навигация
├── SUMMARY.md                  # Краткая сводка
├── QUICK_REFERENCE.md          # Быстрая справка
├── MAKEFILE.md                 # Руководство по Makefile
├── TECHNICAL_REQUIREMENTS.md   # Техническое задание
├── RUN_TESTS.md                # Запуск тестов
├── PORTS.md                    # Справочник портов
├── DB_INIT.md                  # Инициализация БД
├── KAFKA_INTEGRATION.md        # Интеграция Kafka
├── REDIS_CACHING.md            # Кэширование
├── ACTION_TYPES.md             # Типы действий (enum)
├── API_ERROR_500.md            # Решение ошибки 500
├── TROUBLESHOOTING.md          # Решение проблем
├── CODE_QUALITY.md             # Качество кода
└── GIT_SETUP.md                # Настройка Git
```

## 🎯 Быстрая навигация

### Я хочу...

**...запустить проект**
1. Запустите `make quickstart` (самый простой способ!)
2. Или читайте [README.md](../README.md) для других вариантов
3. См. [MAKEFILE.md](MAKEFILE.md) для всех команд

**...запустить тесты**
1. Читайте [RUN_TESTS.md](RUN_TESTS.md)
2. Запустите `make test` или `pytest tests/clickhouse/ -v`

**...понять архитектуру**
1. Читайте [TECHNICAL_REQUIREMENTS.md](TECHNICAL_REQUIREMENTS.md)
2. См. структуру проекта в [README.md](../README.md)

**...настроить ClickHouse**
1. Проверьте [PORTS.md](PORTS.md) для портов
2. Читайте [DB_INIT.md](DB_INIT.md) для инициализации
3. См. `clickhouse-config/users.xml`

**...написать тесты**
1. Читайте [RUN_TESTS.md](RUN_TESTS.md)
2. См. примеры в `tests/clickhouse/`
3. Запустите `make test`

**...использовать Kafka**
1. Читайте [KAFKA_INTEGRATION.md](KAFKA_INTEGRATION.md)
2. Проверьте логи: `make logs-kafka`

**...настроить кэширование**
1. Читайте [REDIS_CACHING.md](REDIS_CACHING.md)
2. Файл: `app/services/cache.py`

## 📦 Дополнительные файлы

### В корне проекта
- `README.md` - Главная страница
- `Makefile` - Команды управления
- `docker-compose.yml` - Docker конфигурация
- `requirements.txt` - Python зависимости
- `requirements-dev.txt` - Dev зависимости (линтеры)
- `.flake8` - Конфигурация flake8
- `pyproject.toml` - Конфигурация black, mypy

### Скрипты
- `scripts/seed_data.py` - Генерация тестовых данных
- `scripts/safe_db_init.sh` - Безопасная инициализация БД
- `scripts/docker-reset-clickhouse.sh` - Пересоздание ClickHouse
- `scripts/check_services.sh` - Проверка сервисов

### Конфигурация
- `app/config.py` - Настройки приложения
- `clickhouse-config/users.xml` - Пользователи ClickHouse

### Frontend
- `frontend/index.html` - Web UI
- `frontend/app.js` - JavaScript
- `frontend/styles.css` - Стили
- `frontend/README.md` - Документация UI

## 🔗 Внешние ресурсы

### Технологии
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ClickHouse Documentation](https://clickhouse.com/docs/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

### Python библиотеки
- [clickhouse-connect](https://clickhouse.com/docs/en/integrations/python)
- [Pydantic](https://docs.pydantic.dev/)
- [Redis Python](https://redis-py.readthedocs.io/)
- [Kafka Python](https://kafka-python.readthedocs.io/)

## 💡 Советы

1. **Начните с README.md** в корне проекта
2. **Используйте поиск** (Ctrl+F) в документах для быстрого нахождения информации
3. **Читайте примеры кода** в тестах - они показывают как использовать API
4. **Проверяйте логи** если что-то не работает: `docker logs music_recommend_clickhouse`
5. **Задавайте вопросы** если документация неясна

## 📝 Обновление документации

Документация постоянно обновляется. Если вы нашли ошибку или хотите что-то улучшить:

1. Отредактируйте соответствующий `.md` файл
2. Убедитесь что ссылки работают
3. Обновите INDEX.md если добавили новый документ

---

**Удачи в разработке!** 🚀

