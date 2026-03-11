# 🧪 Тесты

Комплексная система тестирования для Music Recommendation System.

## 📁 Структура

```
tests/
├── __init__.py
├── README.md                            # Этот файл
├── api/                                 # Тесты API
│   ├── __init__.py
│   ├── test_api.py                      # Базовые тесты API (AsyncClient)
│   └── test_api_health_check.py         # Health check тесты
├── clickhouse/                          # Тесты ClickHouse
│   ├── __init__.py
│   ├── conftest.py                      # Фикстуры для ClickHouse
│   ├── test_connection.py               # Тесты подключения
│   ├── test_client_methods.py           # Тесты методов клиента
│   ├── test_operations_users.py         # Операции с пользователями
│   ├── test_operations_tracks.py        # Операции с треками
│   ├── test_operations_interactions.py  # Операции с взаимодействиями
│   ├── test_dbschema.py                 # Тесты структуры БД
│   ├── test_complex_queries.py          # Сложные запросы
│   ├── test_constraints_validation.py   # Валидация ограничений
│   ├── test_table_engines.py            # Тесты движков таблиц
│   ├── test_partitioning.py             # Тесты партиционирования
│   ├── test_performance.py              # Тесты производительности
│   └── README.md                        # Документация ClickHouse тестов
├── kafka/                               # Тесты Kafka
│   ├── __init__.py
│   ├── conftest.py                      # Фикстуры для Kafka
│   ├── test_kafka_client.py             # Тесты подключения
│   ├── test_kafka_producer.py           # Тесты producer
│   ├── test_kafka_consumer.py           # Тесты consumer
│   ├── test_kafka_integration.py        # Интеграционные тесты
│   └── README.md                        # Документация Kafka тестов
```

## 🚀 Быстрый старт

### Установка зависимостей для тестирования

```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

### Запуск всех тестов

```bash
pytest
```

### Запуск с покрытием

```bash
pytest --cov=app --cov-report=html
```

### Запуск конкретной группы тестов

```bash
# Только API тесты
pytest tests/api/ -v

# Только ClickHouse тесты
pytest tests/clickhouse/ -v

# Только Kafka тесты (unit)
pytest tests/kafka/ -v -m "not integration"

# Конкретный класс тестов
pytest tests/api/test_api.py::TestHealthCheck -v

# Конкретный тест
pytest tests/api/test_api.py::TestHealthCheck::test_health_check -v
```

## 📊 Типы тестов

### 1. Модульные тесты (Unit Tests)
- Тестируют отдельные функции и методы
- Быстрые, не требуют внешних зависимостей
- Расположены в корне tests/

### 2. Интеграционные тесты (Integration Tests)
- Тестируют взаимодействие с внешними сервисами
- Требуют запущенные ClickHouse, Redis, Kafka
- Расположены в tests/clickhouse/

### 3. API тесты (API Tests)
- Тестируют HTTP эндпоинты
- Используют AsyncClient от httpx
- Расположены в tests/api/

## 🎯 Покрытие

Текущее покрытие тестами:

- ✅ **ClickHouse**: Подключение, операции, схема (50+ тестов)
- ✅ **API**: Базовые эндпоинты (health, docs, root)
- ✅ **Kafka**: Producer, Consumer, Client, Integration (60+ тестов)
- ⏳ **API Users**: TODO
- ⏳ **API Tracks**: TODO
- ⏳ **API Events**: TODO
- ⏳ **API Recommendations**: TODO
- ⏳ **Redis**: TODO
- ⏳ **ML Models**: TODO

## 🔧 Настройка

### Переменные окружения для тестов

Создайте `.env.test`:

```env
# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=music_recommend_test

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_EVENTS=user_track_events_test
KAFKA_CONSUMER_GROUP=recommend_consumer_test
```

### Запуск сервисов для тестов

#### Вариант 1: Docker Compose

```bash
# Только ClickHouse и Redis (для unit тестов)
docker-compose up -d clickhouse redis

# Включая Kafka (для интеграционных тестов Kafka)
docker-compose up -d clickhouse redis kafka zookeeper
```

#### Вариант 2: Отдельные контейнеры

```bash
# ClickHouse
docker run -d --name clickhouse-test -p 9000:9000 clickhouse/clickhouse-server

# Redis
docker run -d --name redis-test -p 6379:6379 redis:7-alpine

# Kafka (для интеграционных тестов)
# Требует также Zookeeper
```

## 📝 Написание тестов

### Структура теста

```python
class TestFeatureName:
    """Описание группы тестов"""
    
    def test_specific_behavior(self, fixture1, fixture2):
        """Описание конкретного теста"""
        # 1. Arrange (Подготовка)
        data = prepare_test_data()
        
        # 2. Act (Действие)
        result = perform_action(data)
        
        # 3. Assert (Проверка)
        assert result == expected_value
```

### Использование фикстур

```python
import pytest

@pytest.fixture
def sample_data():
    """Фикстура с тестовыми данными"""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Тест использующий фикстуру"""
    assert sample_data["key"] == "value"
```

### Параметризация тестов

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    """Тест с параметрами"""
    assert input * 2 == expected
```

## 🎭 Моки и заглушки

### Мокирование внешних сервисов

```python
from unittest.mock import Mock, patch

def test_with_mock():
    """Тест с мокированием"""
    with patch('app.db.clickhouse.get_clickhouse_client') as mock_client:
        mock_client.return_value.execute.return_value = Mock(result_rows=[[1]])
        
        # Ваш тест
        result = some_function()
        assert result == expected
```

## 📈 Отчеты о покрытии

### Генерация HTML отчета

```bash
pytest --cov=app --cov-report=html
```

Откройте `htmlcov/index.html` в браузере.

### Просмотр покрытия в терминале

```bash
pytest --cov=app --cov-report=term-missing
```

### Проверка минимального покрытия

```bash
pytest --cov=app --cov-fail-under=80
```

## 🐛 Отладка тестов

### Запуск с подробным выводом

```bash
pytest -vv -s
```

### Остановка при первой ошибке

```bash
pytest -x
```

### Запуск только упавших тестов

```bash
pytest --lf
```

### Отладка конкретного теста

```bash
pytest tests/api/test_api.py::test_root -vv -s --pdb
```

## ⚡ Производительность

### Параллельный запуск тестов

```bash
pip install pytest-xdist
pytest -n auto
```

### Профилирование тестов

```bash
pytest --durations=10
```

## 🏷️ Маркеры тестов

### Использование маркеров

```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    """Медленный тест"""
    pass

@pytest.mark.integration
def test_with_database():
    """Интеграционный тест"""
    pass
```

### Запуск по маркерам

```bash
# Только быстрые тесты
pytest -m "not slow"

# Только интеграционные
pytest -m integration
```

## 🔄 CI/CD Integration

### GitHub Actions пример

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      clickhouse:
        image: clickhouse/clickhouse-server
        ports:
          - 9000:9000
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 📚 Лучшие практики

1. **Именование тестов**: Используйте описательные имена
   - ✅ `test_user_registration_with_valid_email`
   - ❌ `test1`, `test_user`

2. **Изоляция тестов**: Каждый тест должен быть независимым
   - Используйте фикстуры с `clean_tables`
   - Не полагайтесь на порядок выполнения

3. **Тестируйте edge cases**: Не только happy path
   - Пустые данные
   - Некорректный ввод
   - Граничные значения

4. **Используйте фикстуры**: Переиспользуйте подготовку данных
   - Смотрите `conftest.py` для общих фикстур

5. **Документируйте тесты**: Добавляйте docstring к каждому тесту

6. **Быстрота тестов**: Модульные тесты должны быть быстрыми
   - Используйте моки для внешних зависимостей
   - Интеграционные тесты выделяйте в отдельную группу

## 🆘 Помощь

### Проблемы с тестами

1. **Тесты не запускаются**
   ```bash
   # Проверьте установку pytest
   pip install pytest pytest-asyncio
   
   # Проверьте PYTHONPATH
   export PYTHONPATH="${PYTHONPATH}:${PWD}"
   ```

2. **Ошибки подключения к ClickHouse**
   ```bash
   # Проверьте, что ClickHouse запущен
   docker ps | grep clickhouse
   
   # Проверьте порты
   netstat -an | grep 9000
   ```

3. **Падают рандомно**
   ```bash
   # Запустите последовательно
   pytest -n 0
   ```

### Полезные команды

```bash
# Список всех тестов
pytest --collect-only

# Запуск с выводом print
pytest -s

# Запуск с breakpoint
pytest --pdb

# Очистка кэша pytest
pytest --cache-clear
```

## 📖 Дополнительные ресурсы

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [ClickHouse Testing](https://clickhouse.com/docs/en/development/tests/)
- [Coverage.py](https://coverage.readthedocs.io/)

