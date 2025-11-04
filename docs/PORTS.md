# 🔌 Порты сервисов

Справочник портов, используемых в Music Recommendation System.

## ClickHouse

ClickHouse использует **два разных порта** для разных протоколов:

### Порт 8123 - HTTP Interface ✅
- **Используется**: `clickhouse-connect` (Python библиотека)
- **Протокол**: HTTP/HTTPS
- **Применение**: Наше приложение, тесты, HTTP клиенты
- **URL**: `http://localhost:8123`

### Порт 9000 - Native TCP Protocol
- **Используется**: `clickhouse-client` (CLI клиент)
- **Протокол**: Native TCP
- **Применение**: Интерактивная работа, миграции через CLI
- **Команда**: `clickhouse-client --port 9000`

## ⚠️ Важно!

**Наше приложение использует порт 8123**, так как библиотека `clickhouse-connect` работает через HTTP протокол.

```python
# ✅ Правильно
CLICKHOUSE_PORT=8123

# ❌ Неправильно (это порт для нативного клиента)
CLICKHOUSE_PORT=9000
```

## Все порты проекта

| Сервис | Порт | Протокол | Использование |
|--------|------|----------|---------------|
| **Frontend UI** | 8080 | HTTP | Web интерфейс ⭐ |
| **FastAPI** | 8000 | HTTP | REST API |
| **ClickHouse HTTP** | 8123 | HTTP | Python app, тесты |
| **ClickHouse Native** | 9000 | TCP | CLI клиент |
| **Kafka** | 9092 | Kafka Protocol | Стриминг событий |
| **Zookeeper** | 2181 | TCP | Kafka coordination |
| **Redis** | 6379 | Redis Protocol | Кэш, очереди |

## Примеры использования

### Python приложение (clickhouse-connect)
```python
import clickhouse_connect

client = clickhouse_connect.get_client(
    host='localhost',
    port=8123,  # ← HTTP порт
    username='default',
    password=''
)
```

### CLI клиент (clickhouse-client)
```bash
clickhouse-client \
  --host localhost \
  --port 9000 \
  --user default
```

### Docker контейнер
```yaml
clickhouse:
  image: clickhouse/clickhouse-server:latest
  ports:
    - "8123:8123"  # HTTP - для приложения
    - "9000:9000"  # Native - для CLI
```

### Проверка доступности

```bash
# HTTP порт (для приложения)
curl http://localhost:8123/
# Должен вернуть: Ok.

# Native порт (для CLI)
clickhouse-client --query "SELECT 1"
# Должен вернуть: 1
```

## Troubleshooting

### Ошибка: "Port 9000 is for clickhouse-client program"

**Причина**: Вы пытаетесь использовать HTTP библиотеку с нативным портом.

**Решение**: Измените порт на 8123 в `.env`:
```env
CLICKHOUSE_PORT=8123
```

### Ошибка: "Connection refused on port 8123"

**Причина**: ClickHouse не запущен или не слушает HTTP порт.

**Проверка**:
```bash
# Проверьте, что ClickHouse запущен
docker ps | grep clickhouse

# Проверьте, что порт открыт
curl http://localhost:8123/
```

**Решение**:
```bash
docker-compose up -d clickhouse
```

### Ошибка при работе с CLI

**Причина**: Пытаетесь подключиться к HTTP порту через нативный клиент.

**Решение**: Используйте порт 9000 для CLI:
```bash
clickhouse-client --host localhost --port 9000
```

## Миграция с порта 9000 на 8123

Если у вас в коде используется порт 9000:

1. **Обновите .env файл**:
```env
CLICKHOUSE_PORT=8123
```

2. **Перезапустите приложение**:
```bash
python -m app.main
```

3. **Перезапустите тесты**:
```bash
pytest tests/clickhouse/ -v
```

## Полезные ссылки

- [ClickHouse Interfaces](https://clickhouse.com/docs/en/interfaces/overview)
- [ClickHouse HTTP Interface](https://clickhouse.com/docs/en/interfaces/http)
- [clickhouse-connect Documentation](https://clickhouse.com/docs/en/integrations/python)

