# 📚 Документация

Полная документация для Music Recommendation System.

## 📖 Основные документы

### Для начинающих
- 🚀 **[README.md](../README.md)** - Начните отсюда! Общий обзор проекта
- 📊 **[SUMMARY.md](SUMMARY.md)** - Краткая сводка проекта
- ⚡ **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Быстрая справка (команды, URL)
- 📋 **[TECHNICAL_REQUIREMENTS.md](TECHNICAL_REQUIREMENTS.md)** - Техническое задание проекта
- 📝 **[CHANGELOG.md](CHANGELOG.md)** - История изменений

### Тестирование
- 🧪 **[RUN_TESTS.md](RUN_TESTS.md)** - Как запускать тесты (краткое руководство)

### Конфигурация и качество
- 🔌 **[PORTS.md](PORTS.md)** - Справочник по портам сервисов
- 📊 **[DB_INIT.md](DB_INIT.md)** - Инициализация базы данных (идемпотентно)
- 🚨 **[API_ERROR_500.md](API_ERROR_500.md)** - Решение ошибки 500 Internal Server Error
- 🆘 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Решение проблем
- ✨ **[CODE_QUALITY.md](CODE_QUALITY.md)** - Качество кода и рефакторинг
- 🔄 **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - Итоги рефакторинга
- 🔐 **[GIT_SETUP.md](GIT_SETUP.md)** - Настройка Git и GitHub

## 🗂️ Структура документации

```
docs/
├── INDEX.md                    # Этот файл - навигация по документации
├── TECHNICAL_REQUIREMENTS.md  # Техническое задание
├── RUN_TESTS.md                # Быстрый старт тестов
├── TESTING.md                  # Полная документация тестов
├── CLICKHOUSE_TESTS.md         # Специфика тестов ClickHouse
├── PORTS.md                    # Справочник портов
└── CLICKHOUSE_CONFIG.md        # Конфигурация ClickHouse
```

## 🎯 Быстрая навигация

### Я хочу...

**...запустить проект**
1. Запустите `make quickstart` (самый простой способ!)
2. Или читайте [README.md](../README.md) для других вариантов
3. См. [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) для всех команд

**...запустить тесты**
1. Читайте [RUN_TESTS.md](RUN_TESTS.md)
2. Запустите `make test` или `pytest tests/clickhouse/ -v`

**...понять архитектуру**
1. Читайте [TECHNICAL_REQUIREMENTS.md](TECHNICAL_REQUIREMENTS.md)
2. См. структуру проекта в [README.md](../README.md)

**...настроить ClickHouse**
1. Читайте [CLICKHOUSE_CONFIG.md](CLICKHOUSE_CONFIG.md)
2. Проверьте [PORTS.md](PORTS.md) для портов
3. См. `clickhouse-config/users.xml`

**...написать тесты**
1. Читайте [TESTING.md](TESTING.md)
2. См. примеры в `tests/clickhouse/`
3. Используйте фикстуры из `conftest.py`

## 📦 Дополнительные файлы

### В корне проекта
- `README.md` - Главная страница
- `docker-compose.yml` - Docker конфигурация
- `requirements.txt` - Python зависимости
- `.gitignore` - Git ignore правила

### Скрипты
- `scripts/seed_data.py` - Генерация тестовых данных
- `scripts/safe_db_init.sh` - Безопасная инициализация БД (идемпотентно)
- `scripts/docker-reset-clickhouse.sh` - Пересоздание ClickHouse контейнера
- `scripts/check_services.sh` - Проверка доступности сервисов

### Конфигурация
- `clickhouse-config/users.xml` - Пользователи ClickHouse
- `.env.example` - Пример переменных окружения
- `app/config.py` - Конфигурация приложения

### Тесты
- `tests/README.md` - Документация тестов (ссылка на docs/TESTING.md)
- `tests/clickhouse/README.md` - Документация тестов ClickHouse
- `tests/conftest.py` - Фикстуры pytest

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

