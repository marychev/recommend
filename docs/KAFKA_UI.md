# 📊 Kafka UI - Мониторинг и управление Kafka

## Описание

Kafka UI - это современный веб-интерфейс для мониторинга и управления Apache Kafka кластером. Предоставляет удобный способ просмотра топиков, сообщений, consumer groups и метрик производительности.

## 🚀 Быстрый старт

### Доступ

```bash
# Откройте в браузере
http://localhost:8081
```

### Запуск

Kafka UI автоматически запускается вместе с другими сервисами:

```bash
# Запустить все сервисы (включая Kafka UI)
make up

# Или только Kafka + Kafka UI
make up-kafka
```

### Остановка

```bash
# Остановить все сервисы
make down

# Или только Kafka UI
docker compose stop kafka-ui
```

## ✨ Основные возможности

### 1. 📊 Просмотр топиков

**Что можно увидеть:**
- Список всех топиков в кластере
- Количество партиций в каждом топике
- Размер данных (в байтах)
- Конфигурация топиков
- Retention policy

**Как использовать:**
1. Откройте http://localhost:8081
2. Перейдите в раздел **"Topics"**
3. Выберите топик `user_track_events`
4. Просмотрите детали топика

### 2. 📨 Просмотр сообщений

**Что можно увидеть:**
- Содержимое событий в режиме реального времени
- JSON форматирование
- Timestamp каждого сообщения
- Key и Value сообщений
- Headers (если есть)

**Как использовать:**
1. Откройте топик `user_track_events`
2. Нажмите **"Messages"**
3. Выберите партицию
4. Установите offset или выберите "Latest"
5. Просматривайте события по мере их поступления

**Пример сообщения:**
```json
{
  "user_id": 1001,
  "track_id": 12345,
  "action_type": "play",
  "listen_duration_seconds": 180,
  "timestamp": "2025-11-05T12:00:00.000Z"
}
```

### 3. 👥 Consumer Groups

**Что можно увидеть:**
- Список всех consumer groups
- Статус потребителей (active/inactive)
- Lag - отставание обработки
- Current offset - текущая позиция чтения
- Committed offset - последняя зафиксированная позиция

**Как использовать:**
1. Перейдите в раздел **"Consumers"**
2. Найдите группу `recommend_consumer`
3. Проверьте lag:
   - **Lag = 0** ✅ - обработка в реальном времени
   - **Lag > 0** ⚠️ - есть отставание
   - **Lag растет** ❌ - consumer не успевает

**Troubleshooting по lag:**
```bash
# Если lag растет:
# 1. Добавьте больше consumer'ов в группу
# 2. Увеличьте партиции топика
# 3. Оптимизируйте обработку событий
```

### 4. 📈 Метрики брокеров

**Что можно увидеть:**
- Статус брокеров (online/offline)
- Количество партиций на каждом брокере
- Использование диска
- Throughput (байт/сек)
- Количество активных подключений

**Как использовать:**
1. Перейдите в раздел **"Brokers"**
2. Выберите брокер
3. Просмотрите детальные метрики

### 5. ⚙️ Управление топиками

**Что можно делать:**
- Создавать новые топики
- Изменять конфигурацию
- Удалять топики
- Увеличивать количество партиций
- Изменять retention policy

**Создание топика через UI:**
1. Перейдите в **"Topics"**
2. Нажмите **"Create Topic"**
3. Заполните параметры:
   - Name: имя топика
   - Partitions: количество партиций (рекомендуется: 3)
   - Replication Factor: фактор репликации (для dev: 1)
   - Retention: время хранения (по умолчанию: 7 дней)

### 6. 📤 Отправка тестовых сообщений

**Как отправить событие:**
1. Откройте топик `user_track_events`
2. Нажмите **"Produce Message"**
3. Выберите формат: **JSON**
4. Введите тело сообщения:

```json
{
  "user_id": 999,
  "track_id": 888,
  "action_type": "like",
  "listen_duration_seconds": 0,
  "timestamp": "2025-11-05T12:00:00Z"
}
```

5. (Опционально) Добавьте Key
6. Нажмите **"Produce"**
7. Проверьте, что сообщение появилось в топике

## 🔍 Примеры использования

### Пример 1: Отладка событий

**Задача:** Проверить, что события от пользователя корректно попадают в Kafka

**Шаги:**
1. Отправьте событие через API:
```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1001,
    "track_id": 12345,
    "action_type": "play",
    "listen_duration_seconds": 180
  }'
```

2. Откройте Kafka UI: http://localhost:8081
3. Перейдите в Topics → user_track_events → Messages
4. Найдите свое событие в списке
5. Проверьте корректность данных

### Пример 2: Мониторинг производительности

**Задача:** Проверить, что consumer успевает обрабатывать события

**Шаги:**
1. Откройте Kafka UI: http://localhost:8081
2. Перейдите в Consumers → recommend_consumer
3. Проверьте Lag для каждой партиции:
   - Lag = 0 ✅ - все в порядке
   - Lag < 100 ⚠️ - небольшое отставание
   - Lag > 1000 ❌ - нужно масштабировать

### Пример 3: Анализ топиков

**Задача:** Посмотреть, сколько событий в каждом топике

**Шаги:**
1. Откройте Kafka UI: http://localhost:8081
2. Перейдите в Topics
3. Проверьте колонку "Messages":
   - user_track_events: количество событий
   - retention: время хранения
4. Нажмите на топик для детальной информации

## 🔧 Конфигурация

### Docker Compose

```yaml
kafka-ui:
  image: provectuslabs/kafka-ui:v0.7.0
  container_name: music_recommend_kafka_ui
  depends_on:
    - kafka
  ports:
    - "8081:8080"  # localhost:8081 → контейнер:8080
  environment:
    - KAFKA_CLUSTERS_0_BOOTSTRAP_SERVERS=kafka:29092
    - KAFKA_CLUSTERS_0_NAME=kafka
  networks:
    - music_recommend_network
```

### Переменные окружения

| Переменная | Значение | Описание |
|------------|----------|----------|
| `KAFKA_CLUSTERS_0_NAME` | `kafka` | Имя кластера |
| `KAFKA_CLUSTERS_0_BOOTSTRAP_SERVERS` | `kafka:29092` | Адрес Kafka внутри Docker |

**Важно:** Используется `kafka:29092` (internal port) для доступа из Docker сети.

## 🐛 Troubleshooting

### Kafka UI не открывается

**Симптомы:**
- Страница не загружается
- Ошибка "Connection refused"

**Решение:**

```bash
# 1. Проверьте, что контейнер запущен
docker ps | grep kafka-ui

# 2. Проверьте логи
docker logs music_recommend_kafka_ui

# 3. Перезапустите контейнер
docker compose restart kafka-ui

# 4. Проверьте порт
curl http://localhost:8081
```

### Не видно топиков

**Симптомы:**
- В Kafka UI пусто
- Ошибка подключения к Kafka

**Причины:**
1. Kafka еще не запустилась
2. Топики не созданы
3. Неправильная конфигурация подключения

**Решение:**

```bash
# 1. Проверьте, что Kafka запущена
docker ps | grep kafka

# 2. Проверьте логи Kafka
docker logs music_recommend_kafka

# 3. Проверьте топики внутри Kafka
docker exec music_recommend_kafka \
  kafka-topics --list \
  --bootstrap-server kafka:29092

# 4. Создайте топик вручную (если нужно)
docker exec music_recommend_kafka \
  kafka-topics --create \
  --topic user_track_events \
  --bootstrap-server kafka:29092 \
  --partitions 3 \
  --replication-factor 1
```

### Ошибка "No resolvable bootstrap urls"

**Симптомы:**
- В логах Kafka UI ошибка DNS resolution
- Не может подключиться к Kafka

**Причина:**
Неправильный адрес Kafka в конфигурации

**Решение:**

Проверьте `docker-compose.yml`:
```yaml
environment:
  - KAFKA_CLUSTERS_0_BOOTSTRAP_SERVERS=kafka:29092  # ✅ Правильно
  # НЕ localhost:9092 - это не работает из Docker!
```

### Медленная загрузка сообщений

**Симптомы:**
- Messages долго загружаются
- UI тормозит

**Причины:**
1. Слишком много сообщений в топике
2. Большой размер сообщений

**Решение:**

```bash
# 1. Ограничьте количество загружаемых сообщений
# В UI: установите "Max Messages" = 100

# 2. Используйте фильтры по времени
# В UI: установите "From" offset

# 3. Уменьшите retention для старых топиков
docker exec music_recommend_kafka \
  kafka-configs --alter \
  --topic user_track_events \
  --add-config retention.ms=604800000 \
  --bootstrap-server kafka:29092
# (604800000 ms = 7 дней)
```

## 📊 Мониторинг метрик

### Ключевые метрики для отслеживания

**1. Consumer Lag**
- **Нормально:** 0-10 сообщений
- **Внимание:** 10-100 сообщений
- **Критично:** > 100 сообщений

**2. Throughput**
- **Messages/sec:** количество событий в секунду
- **Bytes/sec:** объем данных в секунду

**3. Партиции**
- Равномерное распределение по партициям ✅
- Неравномерное распределение ⚠️ (нужно rebalancing)

**4. Retention**
- Убедитесь, что старые сообщения удаляются
- Проверяйте размер топиков

## 🔗 Полезные ссылки

- **Kafka UI GitHub:** https://github.com/provectus/kafka-ui
- **Документация:** https://docs.kafka-ui.provectus.io/
- **Docker Hub:** https://hub.docker.com/r/provectuslabs/kafka-ui

## 🎯 Best Practices

### 1. Регулярно проверяйте lag

```bash
# Каждый день проверяйте consumer lag
# Если растет - масштабируйте consumer'ы
```

### 2. Мониторьте размер топиков

```bash
# Следите за размером топиков
# Настройте retention policy
```

### 3. Используйте фильтры

```bash
# При поиске сообщений используйте фильтры
# Это экономит ресурсы Kafka
```

### 4. Не удаляйте топики в production

```bash
# Будьте осторожны с удалением топиков
# В production используйте backup
```

## 📚 Связанные документы

- [KAFKA_INTEGRATION.md](KAFKA_INTEGRATION.md) - Интеграция с Kafka
- [PORTS.md](PORTS.md) - Справочник портов
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Решение проблем
- [docker-compose.yml](../docker-compose.yml) - Конфигурация Docker

---

**Создано:** 2025-11-05  
**Версия Kafka UI:** v0.7.0  
**Порт:** 8081

