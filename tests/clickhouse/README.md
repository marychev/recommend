# 🧪 Тесты ClickHouse

Комплексные тесты для проверки подключения и работы с ClickHouse.

## 📋 Структура тестов

```
tests/clickhouse/
├── conftest.py              # Фикстуры для тестов
├── test_connection.py       # Тесты подключения
├── test_operations.py       # Тесты операций с данными
├── test_schema.py           # Тесты структуры БД
└── README.md
```

## 🎯 Покрытие тестов

### 1. test_connection.py - Подключение
- ✅ Успешное подключение к ClickHouse
- ✅ Параметры подключения из конфигурации
- ✅ Выполнение простых запросов
- ✅ Запросы с параметрами
- ✅ Проверка существования базы данных
- ✅ Обработка ошибок подключения
- ✅ Отключение и переподключение
- ✅ Множественные запросы
- ✅ Методы клиента (execute, insert)

### 2. test_operations.py - Операции с данными
- ✅ Вставка одного/нескольких пользователей
- ✅ Вставка треков
- ✅ Вставка взаимодействий
- ✅ Выборка с фильтрами
- ✅ Агрегирующие запросы (count, avg, sum)
- ✅ JOIN запросы (users + interactions, tracks + interactions)
- ✅ Оконные функции
- ✅ Группировка данных
- ✅ Тесты производительности (bulk insert, query performance)

### 3. test_schema.py - Структура БД
- ✅ Проверка существования базы данных
- ✅ Проверка существования таблиц
- ✅ Структура таблиц (columns, types)
- ✅ Движки таблиц (MergeTree, ReplacingMergeTree)
- ✅ Партиционирование
- ✅ ENUM ограничения

## 🚀 Запуск тестов

### Запуск всех тестов ClickHouse

```bash
pytest tests/clickhouse/ -v
```

### Запуск конкретного файла

```bash
# Тесты подключения
pytest tests/clickhouse/test_connection.py -v

# Тесты операций
pytest tests/clickhouse/test_operations.py -v

# Тесты схемы
pytest tests/clickhouse/test_schema.py -v
```

### Запуск конкретного теста

```bash
pytest tests/clickhouse/test_connection.py::TestClickHouseConnection::test_connection_success -v
```

### Запуск с покрытием

```bash
pytest tests/clickhouse/ --cov=app.db.clickhouse --cov-report=html -v
```

### Запуск с подробным выводом

```bash
pytest tests/clickhouse/ -vv -s
```

## 📊 Фикстуры

### Основные фикстуры (conftest.py)

#### clickhouse_client (session scope)
Создает подключение к ClickHouse для всех тестов.
Автоматически создает и удаляет тестовую БД.

```python
def test_example(clickhouse_client):
    result = clickhouse_client.execute("SELECT 1")
    assert result.result_rows[0][0] == 1
```

#### create_test_schema (session scope)
Создает структуру таблиц для тестов.

```python
def test_example(clickhouse_client, create_test_schema):
    # Таблицы users, tracks, interactions уже созданы
    clickhouse_client.insert("users", [[1, "test", "test@test.com", 25, "Russia"]])
```

#### clean_tables (function scope)
Очищает таблицы перед каждым тестом.

```python
def test_example(clickhouse_client, create_test_schema, clean_tables):
    # Таблицы пустые
    # Ваш тест
    # После теста таблицы снова очистятся
```

#### sample_users, sample_tracks, sample_interactions
Возвращают тестовые данные.

```python
def test_example(clickhouse_client, create_test_schema, clean_tables, sample_users):
    clickhouse_client.insert("users", sample_users, 
                            column_names=["user_id", "username", "email", "age", "country"])
```

## 🔧 Настройка

### Требования

1. **ClickHouse должен быть запущен:**
```bash
# Docker
docker run -d --name clickhouse -p 9000:9000 clickhouse/clickhouse-server

# Или через docker-compose
docker-compose up -d clickhouse
```

2. **Переменные окружения в .env:**
```env
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=music_recommend
```

### Тестовая база данных

Тесты автоматически создают отдельную тестовую БД: `music_recommend_test`

Это означает, что:
- ✅ Тесты не влияют на основную БД
- ✅ Тестовая БД создается перед тестами
- ✅ Тестовая БД удаляется после тестов

## 📈 Примеры использования

### Тест с вставкой данных

```python
def test_insert_user(clickhouse_client, create_test_schema, clean_tables):
    """Тест вставки пользователя"""
    data = [[1, "john", "john@test.com", 25, "Russia"]]
    columns = ["user_id", "username", "email", "age", "country"]
    
    clickhouse_client.insert("users", data, column_names=columns)
    
    result = clickhouse_client.execute("SELECT count() FROM users")
    assert result.result_rows[0][0] == 1
```

### Тест с JOIN запросом

```python
def test_join_query(clickhouse_client, create_test_schema, clean_tables, 
                    sample_users, sample_tracks, sample_interactions):
    """Тест JOIN запроса"""
    # Вставляем данные
    clickhouse_client.insert("users", sample_users, 
                            column_names=["user_id", "username", "email", "age", "country"])
    clickhouse_client.insert("tracks", sample_tracks, 
                            column_names=["track_id", "title", "artist", "album", 
                                        "genre", "duration_seconds", "release_year"])
    clickhouse_client.insert("user_track_interactions", sample_interactions,
                            column_names=["user_id", "track_id", "action_type",
                                        "listen_duration_seconds", "timestamp"])
    
    # JOIN запрос
    result = clickhouse_client.execute("""
        SELECT u.username, count(*) as cnt
        FROM user_track_interactions i
        JOIN users u ON i.user_id = u.user_id
        GROUP BY u.username
    """)
    
    assert len(result.result_rows) == 3
```

### Тест производительности

```python
def test_bulk_insert(clickhouse_client, create_test_schema, clean_tables):
    """Тест массовой вставки"""
    import time
    
    data = [[i, f"user{i}", f"user{i}@test.com", 25, "Russia"] 
            for i in range(10000)]
    
    start = time.time()
    clickhouse_client.insert("users", data, 
                            column_names=["user_id", "username", "email", "age", "country"])
    elapsed = time.time() - start
    
    assert elapsed < 2.0  # Должно быть быстро
    
    result = clickhouse_client.execute("SELECT count() FROM users")
    assert result.result_rows[0][0] == 10000
```

## 🐛 Отладка тестов

### Посмотреть логи ClickHouse

```bash
# Docker
docker logs clickhouse

# Локально
sudo tail -f /var/log/clickhouse-server/clickhouse-server.log
```

### Подключиться к ClickHouse вручную

```bash
# Docker
docker exec -it clickhouse clickhouse-client

# Локально
clickhouse-client

# Проверить тестовую БД
USE music_recommend_test;
SHOW TABLES;
```

### Запустить тесты с отладочным выводом

```bash
pytest tests/clickhouse/ -vv -s --tb=short
```

### Остановить тесты при первой ошибке

```bash
pytest tests/clickhouse/ -x
```

## 📝 Добавление новых тестов

### Шаблон теста

```python
def test_my_feature(clickhouse_client, create_test_schema, clean_tables):
    """Описание теста"""
    # 1. Подготовка данных
    data = [[1, "test", "test@test.com", 25, "Russia"]]
    clickhouse_client.insert("users", data, 
                            column_names=["user_id", "username", "email", "age", "country"])
    
    # 2. Выполнение действия
    result = clickhouse_client.execute("SELECT username FROM users WHERE user_id = 1")
    
    # 3. Проверка результата
    assert result.result_rows[0][0] == "test"
```

### Добавление новой фикстуры

Добавьте в `conftest.py`:

```python
@pytest.fixture
def my_fixture(clickhouse_client):
    """Описание фикстуры"""
    # Подготовка
    yield data
    # Очистка (опционально)
```

## 🎯 Best Practices

1. **Используйте clean_tables** для изоляции тестов
2. **Не изменяйте production БД** - тесты используют отдельную БД
3. **Проверяйте не только успех, но и ошибки** (negative tests)
4. **Тестируйте производительность** критичных операций
5. **Используйте параметризацию** для похожих тестов

```python
@pytest.mark.parametrize("age,expected_count", [
    (20, 0),
    (25, 2),
    (30, 1),
])
def test_filter_by_age(clickhouse_client, create_test_schema, clean_tables, 
                       sample_users, age, expected_count):
    clickhouse_client.insert("users", sample_users, 
                            column_names=["user_id", "username", "email", "age", "country"])
    
    result = clickhouse_client.execute(
        f"SELECT count() FROM users WHERE age >= {age}"
    )
    assert result.result_rows[0][0] == expected_count
```

## 🚨 Troubleshooting

### Ошибка: "Connection refused"
```bash
# Проверьте, что ClickHouse запущен
docker ps | grep clickhouse

# Проверьте порты
netstat -an | grep 9000
```

### Ошибка: "Database already exists"
```bash
# Удалите тестовую БД вручную
clickhouse-client --query "DROP DATABASE IF EXISTS music_recommend_test"
```

### Тесты падают случайно
```bash
# Запустите тесты последовательно (без параллелизма)
pytest tests/clickhouse/ -v --tb=short
```

## 📚 Полезные ссылки

- [ClickHouse Documentation](https://clickhouse.com/docs/)
- [Pytest Documentation](https://docs.pytest.org/)
- [ClickHouse Python Driver](https://clickhouse.com/docs/en/integrations/python)

