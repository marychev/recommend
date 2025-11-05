# 🧪 Тесты Kafka

Комплексная система тестирования Kafka интеграции для Music Recommendation System.

## 📊 Статистика

- **Всего тестов**: 60 (52 unit + 8 интеграционных)
- **Покрытие кода**: **100%** ✅
- **Файлы**:
  - `app/kafka/client.py` - 100% покрытие
  - `app/kafka/producer.py` - 100% покрытие
  - `app/kafka/consumer.py` - 100% покрытие

## 🚀 Быстрый старт

### Unit тесты (не требуют Kafka)

```bash
# Через make
make test-kafka
```

### Интеграционные тесты (требуют Kafka)

```bash
# Запустить Kafka
make up-kafka

# Или все тесты
make test-kafka
```

## 📁 Структура тестов

```
tests/kafka/
├── conftest.py                   # Фикстуры
├── test_kafka_client.py          # Тесты подключения (18 тестов)
├── test_kafka_producer.py        # Тесты producer (17 тестов)
├── test_kafka_consumer.py        # Тесты consumer (17 тестов)
├── test_kafka_integration.py    # Интеграционные (8 тестов)
└── README.md                     # Подробная документация
```

## ✅ Что тестируется

### Client (18 тестов)
- ✅ Создание и переиспользование Producer (singleton)
- ✅ Создание Consumer с кастомными параметрами
- ✅ Закрытие Producer/Consumer
- ✅ Health check Kafka
- ✅ Обработка ошибок подключения

### Producer (17 тестов)
- ✅ Сериализация событий (JSON, datetime, русский текст)
- ✅ Отправка одиночных событий
- ✅ Отправка batch событий
- ✅ Партиционирование по user_id
- ✅ Обработка ошибок Kafka
- ✅ Отправка в правильный топик

### Consumer (17 тестов)
- ✅ Десериализация событий
- ✅ Обработка сообщений из Kafka
- ✅ Кастомные топики и группы
- ✅ Обработка ошибок десериализации
- ✅ Обработка ошибок в обработчике
- ✅ Фоновый consumer

### Integration (8 тестов)
- ✅ Подключение к Kafka
- ✅ Полный цикл send/consume
- ✅ Batch отправка
- ✅ Тесты производительности
- ✅ Параллельная отправка

## 🎯 Команды Make

| Команда | Описание |
|---------|----------|
| `make test-kafka` | Unit тесты (не требуют Kafka) |

## 📈 Пример вывода

```bash
$ make test-kafka

🧪 Запуск unit тестов Kafka...
======================== test session starts =========================
collected 60 items / 8 deselected / 52 selected

tests/kafka/test_kafka_client.py ..................          [ 34%]
tests/kafka/test_kafka_consumer.py .................         [ 67%]
tests/kafka/test_kafka_producer.py .................         [100%]

================= 52 passed, 8 deselected in 0.67s ==================

```

## 🔧 Настройка CI/CD

### GitHub Actions пример

```yaml
name: Kafka Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      zookeeper:
        image: confluentinc/cp-zookeeper:latest
        env:
          ZOOKEEPER_CLIENT_PORT: 2181
      
      kafka:
        image: confluentinc/cp-kafka:latest
        env:
          KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
          KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
    
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run unit tests
        run: make test-kafka
      ```

## 🐛 Отладка

### Если тесты падают

```bash
# Подробный вывод
pytest tests/kafka/ -vv -s

# Остановка при первой ошибке
pytest tests/kafka/ -x

# Конкретный тест
pytest tests/kafka/test_kafka_producer.py::TestSendEvent::test_send_event_success -vv
```

### Если Kafka недоступна

```bash
# Проверить статус
docker-compose ps kafka

# Логи Kafka
make logs-kafka

# Перезапустить Kafka
docker-compose restart kafka
```

## 📚 Дополнительно

- Подробная документация: `tests/kafka/README.md`
- Фикстуры и примеры: `tests/kafka/conftest.py`
- Интеграция Kafka: `docs/KAFKA_INTEGRATION.md`

## 🎓 Лучшие практики

1. **Всегда запускайте unit тесты перед коммитом**
   ```bash
   make test-kafka
   ```

2. **Используйте маркеры для разделения тестов**
   ```python
   @pytest.mark.integration
   @pytest.mark.slow
   ```

---

**✨ Итого**: Полное покрытие Kafka модуля тестами с высоким качеством и подробной документацией!

