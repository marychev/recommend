# 🧪 Тесты Kafka

Комплексные тесты для Kafka интеграции в Music Recommendation System.

## 📁 Структура

```
tests/kafka/
├── __init__.py
├── conftest.py                    # Фикстуры для тестов
├── test_kafka_client.py           # Тесты подключения к Kafka
├── test_kafka_producer.py         # Тесты producer
├── test_kafka_consumer.py         # Тесты consumer
├── test_kafka_integration.py      # Интеграционные тесты
└── README.md                      # Этот файл
```

## 🎯 Покрытие тестами

### 1. test_kafka_client.py
- ✅ Создание Kafka Producer
- ✅ Singleton pattern для Producer
- ✅ Создание Kafka Consumer
- ✅ Закрытие Producer/Consumer
- ✅ Health check Kafka
- ✅ Подключение к Kafka
- ✅ Обработка ошибок

### 2. test_kafka_producer.py
- ✅ Сериализация событий
- ✅ Сериализация datetime
- ✅ Сериализация русского текста
- ✅ Отправка одиночного события
- ✅ Отправка batch событий
- ✅ Партиционирование по user_id
- ✅ Обработка ошибок Kafka
- ✅ Обработка неожиданных ошибок

### 3. test_kafka_consumer.py
- ✅ Десериализация событий
- ✅ Десериализация datetime
- ✅ Десериализация русского текста
- ✅ Обработка сообщений из Kafka
- ✅ Кастомные топики и группы
- ✅ Обработка ошибок десериализации
- ✅ Обработка ошибок в обработчике
- ✅ Фоновый consumer

### 4. test_kafka_integration.py (требует Kafka)
- ✅ Подключение к Kafka
- ✅ Health check
- ✅ Полный цикл send/consume
- ✅ Batch отправка
- ✅ Тесты производительности
- ✅ Тесты надежности
- ✅ Параллельная отправка

## 🚀 Запуск тестов

### Unit тесты (не требуют Kafka)

```bash
# Все unit тесты Kafka
pytest tests/kafka/ -v -m "not integration"

# Конкретный файл
pytest tests/kafka/test_kafka_producer.py -v

# Конкретный класс
pytest tests/kafka/test_kafka_producer.py::TestSendEvent -v

# Конкретный тест
pytest tests/kafka/test_kafka_producer.py::TestSendEvent::test_send_event_success -v
```

### Все тесты Kafka

```bash
# Сначала запустить Kafka
docker-compose up -d kafka zookeeper

# Все тесты (unit + integration)
pytest tests/kafka/ -v

# С покрытием
pytest tests/kafka/ -v --cov=app/kafka --cov-report=html
```

## 📊 Покрытие кода

### Генерация отчета

```bash
pytest tests/kafka/ --cov=app/kafka --cov-report=html --cov-report=term
```

### Целевое покрытие

- **app/kafka/client.py**: > 90%
- **app/kafka/producer.py**: > 95%
- **app/kafka/consumer.py**: > 85%
- **Общее**: > 90%

## 🎭 Фикстуры

### conftest.py предоставляет:

- `mock_kafka_producer` - мок Kafka Producer
- `mock_kafka_consumer` - мок Kafka Consumer
- `sample_event` - пример события
- `sample_event_serialized` - сериализованное событие
- `sample_events_batch` - пакет событий
- `mock_kafka_message` - мок сообщения из Kafka

## 🏷️ Маркеры тестов

### Доступные маркеры:

- `@pytest.mark.integration` - интеграционные тесты (требуют Kafka)
- `@pytest.mark.slow` - медленные тесты
- `@pytest.mark.asyncio` - асинхронные тесты


## 🔧 Настройка для тестов

### Docker Compose

```bash
# Запуск Kafka и Zookeeper для тестов
docker-compose up -d kafka zookeeper

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs kafka

# Остановка
docker-compose down
```

### Переменные окружения

Создайте `.env.test`:

```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_EVENTS=user_track_events_test
KAFKA_CONSUMER_GROUP=recommend_consumer_test
```

## 🐛 Отладка тестов

### Запуск с подробным выводом

```bash
pytest tests/kafka/ -vv -s
```

### Остановка при первой ошибке

```bash
pytest tests/kafka/ -x
```

### Запуск только упавших тестов

```bash
pytest tests/kafka/ --lf
```

### Отладка конкретного теста

```bash
pytest tests/kafka/test_kafka_producer.py::TestSendEvent::test_send_event_success -vv -s --pdb
```

## ⚡ Производительность

### Параллельный запуск

```bash
pip install pytest-xdist
pytest tests/kafka/ -n auto
```

### Профилирование тестов

```bash
pytest tests/kafka/ --durations=10
```

## 🆘 Проблемы и решения

### 1. Тесты не могут подключиться к Kafka

```bash
# Проверьте что Kafka запущена
docker-compose ps | grep kafka

# Проверьте порты
netstat -an | grep 9092

# Проверьте логи
docker-compose logs kafka
```

### 2. Интеграционные тесты падают

```bash
# Очистите топики
docker-compose exec kafka kafka-topics --delete \
  --topic user_track_events_test \
  --bootstrap-server localhost:9092

# Перезапустите Kafka
docker-compose restart kafka
```

### 3. Тесты работают медленно

```bash
# Запустите только unit тесты
pytest tests/kafka/ -m "not integration" -v

# Или используйте параллельный запуск
pytest tests/kafka/ -n auto -m "not integration"
```

### 4. MockProducer не работает

```python
# Убедитесь что очищаете глобальный producer
import app.kafka.client as client_module
client_module._kafka_producer = None
```

## 📚 Дополнительные ресурсы

- [aiokafka Documentation](https://aiokafka.readthedocs.io/)
- [Apache Kafka Testing](https://kafka.apache.org/documentation/#testing)
- [Pytest Async](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock Guide](https://docs.python.org/3/library/unittest.mock.html)

## ✅ Чеклист перед коммитом

- [ ] Все unit тесты проходят
- [ ] Покрытие > 90%
- [ ] Интеграционные тесты проходят (если Kafka доступна)
- [ ] Нет linter ошибок
- [ ] Добавлены docstrings к новым тестам
- [ ] Обновлен README если нужно

## 📈 Статистика тестов

```bash
# Подсчет тестов
pytest tests/kafka/ --collect-only | grep "test_" | wc -l

# Покрытие кода
pytest tests/kafka/ --cov=app/kafka --cov-report=term

# Время выполнения
pytest tests/kafka/ --durations=0
```

---

**Совет**: Всегда запускайте unit тесты перед коммитом, а интеграционные тесты перед push в основную ветку.

