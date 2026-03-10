# Тестирование

## Быстрый старт

```bash
make test              # Все тесты
make test-clickhouse   # Только ClickHouse
make test-kafka        # Только Kafka
make test-api          # Только API
make test-cache        # Только кэш
```

## Предварительные требования

```bash
# Установить зависимости
pip install pytest pytest-asyncio pytest-cov httpx

# Запустить сервисы
make up
```

---

## Unit-тесты

### Запуск

```bash
pytest -v                              # Все тесты
pytest tests/clickhouse/ -v            # ClickHouse
pytest tests/api/ -v                   # API
pytest tests/cache/ -v                 # Кэш
pytest -x                              # Остановить при первой ошибке
pytest --lf                            # Только упавшие тесты
pytest --durations=10                  # Самые медленные тесты
pytest --cov=app --cov-report=html     # С покрытием кода
```

### Структура тестов

```
tests/
├── api/                      # Тесты API
├── cache/                    # Тесты кэширования
├── clickhouse/               # Тесты ClickHouse
│   ├── conftest.py           # Фикстуры (отдельная тестовая БД)
│   ├── test_connection.py    # Подключение
│   └── test_operations.py    # CRUD операции
└── kafka/                    # Тесты Kafka
    ├── conftest.py           # Фикстуры
    ├── test_kafka_client.py  # Подключение (18 тестов)
    ├── test_kafka_producer.py # Producer (17 тестов)
    ├── test_kafka_consumer.py # Consumer (17 тестов)
    └── test_kafka_integration.py # Интеграционные (8 тестов)
```

### Специальные тесты

```bash
make test-ttl-optimization   # Тест оптимизации TTL
make test-cache-warmup       # Тест прогрева кэша
make test-api-health         # Проверка здоровья API
```

---

## Тесты Kafka

### Unit тесты (не требуют Kafka)

```bash
make test-kafka   # 52 unit-теста, ~0.7s
```

- **Client (18):** singleton Producer, создание Consumer, health check, ошибки подключения
- **Producer (17):** сериализация (JSON, datetime, русский текст), batch, партиционирование по user_id
- **Consumer (17):** десериализация, кастомные топики/группы, фоновый consumer

### Интеграционные тесты (требуют Kafka)

```bash
make up-kafka
pytest tests/kafka/test_kafka_integration.py -v
```

- Подключение к Kafka, полный цикл send/consume, batch, параллельная отправка

---

## Нагрузочное тестирование (k6)

### Установка

```bash
make load-test-install   # Проверка установки k6
# macOS: brew install k6
# Linux: https://k6.io/docs/getting-started/installation/
```

### Подготовка данных

```bash
make load-test-data-generate   # Генерация ~1M записей (100k users, 50k tracks, 850k interactions)
```

### Типы тестов

| Команда | Тип | Длительность | VUs |
|---------|-----|-------------|-----|
| `make load-test-quick` | Быстрая проверка | 30s | 5 |
| `make load-test-smoke` | Smoke test | ~2 мин | 10 |
| `make load-test-diagnostics` | Диагностика | 1 мин | 10 |
| `make load-test-basic` | Базовый | ~15 мин | 50→200 |
| `make load-test-spike` | Пиковая нагрузка | ~2 мин | 200 |
| `make load-test-spike-extreme` | Экстрим | ~1 мин | 500 |
| `make load-test-stress` | Стресс | ~30 мин | 50→500 |
| `make load-test-soak` | Выносливость | ~70 мин | 50 |
| `make load-test-post` | POST запросы | ~5 мин | 50 |
| `make load-test-post-quick` | POST (быстрый) | 1 мин | 10 |
| `make load-test-recommendations` | Рекомендации | ~11 мин | - |

### Тесты отдельных эндпоинтов

```bash
make load-test-events-post            # POST /events
make load-test-tracks-post            # POST /tracks
make load-test-users-post             # POST /users
make load-test-recommendations-post   # POST /recommendations
make measure-insert-lag               # Лаг вставки в ClickHouse (k6)
make measure-insert-lag-python        # Лаг вставки (Python)
```

### Рекомендуемая последовательность

```bash
make load-test-quick     # 1. Проверка готовности
make load-test-basic     # 2. Базовая проверка
make load-test-spike     # 3. Пиковые нагрузки
make load-test-stress    # 4. Поиск пределов
make load-test-soak      # 5. Долгосрочная стабильность (опционально)
```

### Метрики k6

| Метрика | Хорошо | Приемлемо | Плохо |
|---------|--------|-----------|-------|
| p(95) | < 800ms | < 2000ms | > 5000ms |
| Ошибки | < 1% | < 5% | > 5% |

### Результаты

```bash
make load-test-results   # Показать результаты последних тестов
```

---

## Troubleshooting

### Тесты не запускаются

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov httpx
```

### ClickHouse: "Connection refused"

```bash
make up-clickhouse
sleep 5
make test-clickhouse
```

### ClickHouse: "Authentication failed"

```bash
bash scripts/docker-reset-clickhouse.sh
```

### Kafka тесты падают

```bash
make up-kafka
pytest tests/kafka/ -vv -s
```

### Нагрузочные тесты: много ошибок 500

```bash
make logs-errors
make db-stats
make diagnose
```

---

## CI/CD

```yaml
- name: Run tests
  run: |
    docker compose up -d clickhouse redis kafka zookeeper
    sleep 10
    pytest --cov=app --cov-report=xml
```

## Связанные документы

- [MAKEFILE.md](MAKEFILE.md) — Все make-команды
- [CLICKHOUSE.md](CLICKHOUSE.md) — Оптимизация ClickHouse
- [KAFKA.md](KAFKA.md) — Kafka интеграция
