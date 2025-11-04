# 🚨 Решение ошибки 500 Internal Server Error

## Симптомы

При обращении к API вы видите:
```
HTTP/1.1 500 Internal Server Error
```

Например:
```bash
curl http://localhost:8000/api/v1/recommendations/1
# Возвращает 500 ошибку
```

## Причины

Ошибка 500 обычно возникает по следующим причинам:

1. ❌ **Нет данных в базе** - таблицы пустые
2. ❌ **Пользователь не существует** - пытаетесь получить рекомендации для несуществующего пользователя
3. ❌ **ClickHouse не подключен** - проблемы с подключением к БД
4. ❌ **Ошибка в SQL запросе** - синтаксическая ошибка

## 🔍 Диагностика

### Шаг 1: Запустите полную диагностику

```bash
make diagnose
```

Эта команда проверит:
- ✅ Статус контейнеров
- ✅ Доступность API
- ✅ Наличие таблиц в БД
- ✅ Количество данных
- ✅ Последние ошибки

### Шаг 2: Посмотрите ошибки в логах

```bash
make logs-errors
```

Эта команда покажет последние ошибки из логов API с выделением цветом.

## ✅ Решение

### Решение 1: Создайте тестовые данные (самая частая причина)

```bash
# Быстрое создание минимальных данных (3 пользователя, 3 трека)
make seed-quick
```

После этого попробуйте снова:
```bash
curl http://localhost:8000/api/v1/recommendations/1
```

### Решение 2: Полная генерация данных

```bash
# Создать 10,000 записей (займёт 1-2 минуты)
make seed

# Проверить что данные созданы
make db-stats
```

### Решение 3: Проверьте что БД инициализирована

```bash
# Проверить таблицы
make db-tables

# Если таблиц нет - инициализируйте БД
make db-init
```

### Решение 4: Перезапустите API

```bash
# Перезапустить API контейнер
docker compose restart api

# Или пересобрать образ
make build && make restart
```

## 📊 Проверка после исправления

```bash
# 1. Проверить статус
make health

# 2. Проверить health check
make health

# 3. Посмотреть данные
make db-stats

# 4. Тестовый запрос
curl http://localhost:8000/api/v1/recommendations/1
```

## 🎯 Примеры использования API

### Получить рекомендации для пользователя

```bash
# GET запрос (простой)
curl http://localhost:8000/api/v1/recommendations/1

# POST запрос (с параметрами)
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "top_n": 10,
    "exclude_listened": true
  }'
```

### Создать пользователя

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 100,
    "username": "newuser",
    "email": "newuser@example.com",
    "age": 25,
    "country": "US"
  }'
```

### Создать трек

```bash
curl -X POST http://localhost:8000/api/v1/tracks \
  -H "Content-Type: application/json" \
  -d '{
    "track_id": 100,
    "title": "Test Song",
    "artist": "Test Artist",
    "album": "Test Album",
    "genre": "Rock",
    "duration_seconds": 180,
    "release_year": 2023
  }'
```

## 🐛 Типичные ошибки

### Ошибка: "Пользователь не найден" (404)

```json
{
  "detail": "Пользователь с ID 999 не найден"
}
```

**Решение:** Создайте пользователя или используйте существующий ID:
```bash
# Проверить существующих пользователей
docker exec music_recommend_clickhouse clickhouse-client -q \
  "SELECT user_id, username FROM music_recommend.users LIMIT 10"
```

### Ошибка: "Недостаточно данных для рекомендаций"

API автоматически переключается на популярные треки, если:
- У пользователя < 5 взаимодействий
- Нет похожих пользователей

**Решение:** Создайте больше взаимодействий:
```bash
make seed-quick  # или make seed
```

## 📖 Swagger документация

Откройте в браузере:
```
http://localhost:8000/docs
```

Там вы можете:
- 📚 Посмотреть все эндпоинты
- 🧪 Протестировать API прямо из браузера
- 📖 Прочитать документацию по каждому эндпоинту

## 🆘 Дополнительная помощь

```bash
# Полная информация о системе
make info

# Все доступные команды
make help

# Проверка всех сервисов
make check-services
```

## 📝 Полезные команды Makefile

```bash
make diagnose      # Полная диагностика
make logs-errors   # Только ошибки из логов
make logs-api      # Все логи API
make seed-quick    # Быстрые тестовые данные
make seed          # Полная генерация данных
make db-stats      # Статистика БД
make health    # Проверка API
make health        # Health check
```

## 🔗 См. также

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Решение других проблем
- [README.md](../README.md) - Основная документация
- [RUN_TESTS.md](RUN_TESTS.md) - Запуск тестов
- [DB_INIT.md](DB_INIT.md) - Инициализация БД

---

**💡 Совет:** Всегда начинайте диагностику с команды `make diagnose` - она покажет полную картину системы.

