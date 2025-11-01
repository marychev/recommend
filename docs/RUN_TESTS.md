# 🧪 Запуск тестов

Краткое руководство по запуску тестов для Music Recommendation System.

## 📋 Предварительные требования

### 1. Установите зависимости для тестирования

```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

### 2. Запустите ClickHouse

#### Вариант A: Docker Compose (рекомендуется)

```bash
docker-compose up -d clickhouse
```

#### Вариант B: Отдельный контейнер

```bash
docker run -d --name clickhouse \
  -p 8123:8123 -p 9000:9000 \
  clickhouse/clickhouse-server:latest
```

#### Проверьте подключение

```bash
# Проверка что ClickHouse запущен
docker ps | grep clickhouse

# Тест подключения (HTTP порт 8123)
curl http://localhost:8123/
# Должен вернуть: Ok.

# ⚠️ ВАЖНО: Используйте порт 8123 для HTTP, а не 9000!
# Порт 9000 - это нативный протокол для clickhouse-client
```

## 🚀 Запуск тестов

### Все тесты

```bash
pytest -v
```

### Только тесты ClickHouse

```bash
pytest tests/clickhouse/ -v
```

### Только тесты API

```bash
pytest tests/test_api.py -v
```

### Конкретный тест

```bash
pytest tests/clickhouse/test_connection.py::TestClickHouseConnection::test_connection_success -v
```

### С покрытием кода

```bash
pytest --cov=app --cov-report=html
```

После этого откройте `htmlcov/index.html` в браузере.

### С подробным выводом

```bash
pytest -vv -s
```

## 📊 Ожидаемый результат

```bash
tests/test_api.py::TestRootEndpoint::test_root PASSED                    [  2%]
tests/test_api.py::TestHealthCheck::test_health_check PASSED             [  4%]
tests/clickhouse/test_connection.py::TestClickHouseConnection::test_connection_success PASSED [ 10%]
tests/clickhouse/test_operations.py::TestUsersOperations::test_insert_single_user PASSED [ 25%]
...

====== 50 passed in 5.43s ======
```

## 🐛 Troubleshooting

### Ошибка: "Authentication failed"

**Проблема**: ClickHouse требует пароль (новые версии 25.x+)

**Решение**: Используйте скрипт пересоздания контейнера:
```bash
bash scripts/docker-reset-clickhouse.sh
```

### Ошибка: "Connection refused"

**Проблема**: ClickHouse не запущен

**Решение**:
```bash
docker-compose up -d clickhouse
# или
docker start clickhouse
```

### Ошибка: "Module not found"

**Проблема**: Не установлены зависимости

**Решение**:
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov httpx
```

### Ошибка: Deprecation warnings

**Проблема**: Устаревшие конфигурации Pydantic

**Решение**: Уже исправлено! Используется новый стиль `ConfigDict`.

### Тесты падают случайно

**Решение**: Запустите последовательно (без параллелизма)
```bash
pytest tests/clickhouse/ -v --tb=short
```

## 📈 Дополнительные опции

### Остановить при первой ошибке

```bash
pytest -x
```

### Запустить только упавшие тесты

```bash
pytest --lf
```

### Посмотреть самые медленные тесты

```bash
pytest --durations=10
```

### Запустить в тихом режиме

```bash
pytest -q
```

### Запустить с маркерами

```bash
# Только быстрые тесты
pytest -m "not slow"

# Только интеграционные тесты
pytest -m integration
```

## 🔄 CI/CD

### GitHub Actions пример

```yaml
- name: Run tests
  run: |
    docker-compose up -d clickhouse redis
    sleep 5
    pytest --cov=app --cov-report=xml
```

## 📚 Дополнительная информация

- **Полная документация тестов**: [TESTING.md](TESTING.md)
- **Тесты ClickHouse**: [CLICKHOUSE_TESTS.md](CLICKHOUSE_TESTS.md)
- **Основная документация**: [../README.md](../README.md)

## ✨ Быстрый старт (для нетерпеливых)

```bash
# 1. Запустите ClickHouse
docker-compose up -d clickhouse

# 2. Подождите 5 секунд
sleep 5

# 3. Запустите тесты
pytest tests/clickhouse/ -v

# 4. Profit! 🎉
```

## 🎯 Статистика покрытия

После запуска с `--cov`:

```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
app/__init__.py                            0      0   100%
app/config.py                             15      0   100%
app/db/clickhouse.py                      45      5    89%
app/models/schemas.py                     85      0   100%
...
-----------------------------------------------------------
TOTAL                                    543     45    92%
```

---

**Готово!** Теперь вы можете запускать тесты и следить за качеством кода! 🚀

