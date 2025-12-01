# K6 POST Load Tests

Набор тестов k6 для проверки нагрузки на POST эндпоинты API.

## ⚠️ Важно: Правильный запуск

**Всегда запускайте тесты из корневой директории проекта!**

```bash
# Убедитесь, что вы в корневой директории
cd /home/recommend  # или путь к вашему проекту

# Проверьте, что файлы существуют
ls load_tests/k6_test_*.js
```

Если вы видите ошибку `The moduleSpecifier "k6_test_events_post.js" couldn't be found`, это означает, что:
1. Вы запускаете k6 не из корневой директории проекта
2. Или используете неправильный путь к файлу

## Тесты

1. **k6_test_events_post.js** - Тест POST `/api/v1/events`
2. **k6_test_tracks_post.js** - Тест POST `/api/v1/tracks`
3. **k6_test_users_post.js** - Тест POST `/api/v1/users`
4. **k6_test_recommendations_post.js** - Тест POST `/api/v1/recommendations`

## Запуск тестов

**Важно:** Запускайте тесты из корневой директории проекта!

### Базовый запуск

```bash
# Из корневой директории проекта
cd /path/to/recommend

# Тест событий
k6 run load_tests/k6_test_events_post.js

# Тест треков
k6 run load_tests/k6_test_tracks_post.js

# Тест пользователей
k6 run load_tests/k6_test_users_post.js

# Тест рекомендаций
k6 run load_tests/k6_test_recommendations_post.js
```

### С указанием базового URL

```bash
BASE_URL=http://localhost:8000 k6 run load_tests/k6_test_events_post.js
```

### Сохранение результатов в файл

```bash
k6 run --out json=load_tests/results/events_post_results.json load_tests/k6_test_events_post.js
k6 run --out json=load_tests/results/tracks_post_results.json load_tests/k6_test_tracks_post.js
k6 run --out json=load_tests/results/users_post_results.json load_tests/k6_test_users_post.js
k6 run --out json=load_tests/results/recommendations_post_results.json load_tests/k6_test_recommendations_post.js
```

### Если используете Docker для k6

```bash
# Убедитесь, что вы в корневой директории проекта
docker run --rm -i -v $(pwd):/scripts grafana/k6 run /scripts/load_tests/k6_test_events_post.js
```

## Параметры нагрузки

### Events (События)
- **Разогрев**: 50 пользователей за 30 сек
- **Нормальная нагрузка**: 100 пользователей
- **Высокая нагрузка**: 200 пользователей
- **Пауза между запросами**: 1 секунда

### Tracks (Треки)
- **Разогрев**: 20 пользователей за 30 сек
- **Нормальная нагрузка**: 50 пользователей
- **Высокая нагрузка**: 100 пользователей
- **Пауза между запросами**: 2 секунды

### Users (Пользователи)
- **Разогрев**: 20 пользователей за 30 сек
- **Нормальная нагрузка**: 50 пользователей
- **Высокая нагрузка**: 100 пользователей
- **Пауза между запросами**: 2 секунды

### Recommendations (Рекомендации)
- **Разогрев**: 10 пользователей за 30 сек
- **Нормальная нагрузка**: 20 пользователей
- **Высокая нагрузка**: 50 пользователей
- **Пауза между запросами**: 3 секунды
- **Таймаут запроса**: 30 секунд

## Пороги производительности

### Events, Tracks, Users
- 95% запросов должны выполняться < 500ms
- 99% запросов должны выполняться < 1000ms
- Меньше 5% ошибок
- Больше 95% успешных запросов

### Recommendations
- 95% запросов должны выполняться < 2000ms
- 99% запросов должны выполняться < 5000ms
- Меньше 5% ошибок
- Больше 95% успешных запросов

## Генерация тестовых данных

### Events
- `user_id`: случайное число от 1 до 10000
- `track_id`: случайное число от 1 до 50000
- `action_type`: случайный из ['play', 'like', 'dislike', 'skip', 'add_to_playlist', 'share']
- `listen_duration_seconds`: только для 'play' (10-310 секунд)

### Tracks
- `title`: случайное название + уникальный номер
- `artist`: случайный из списка популярных исполнителей
- `album`: случайный из списка альбомов
- `genre`: случайный из списка жанров
- `duration_seconds`: 120-420 секунд
- `release_year`: 1970-2020

### Users
- `username`: уникальное имя с timestamp
- `email`: сгенерированный email
- `age`: 18-78 лет
- `country`: случайная страна

### Recommendations
- `user_id`: случайное число от 1 до 10000
- `top_n`: 5, 10 или 20
- `exclude_listened`: случайно true/false
- `include_performance_metrics`: иногда true (30% случаев)

## Интерпретация результатов

После выполнения теста вы увидите:
- Общее количество запросов
- Процент успешных запросов
- Процент ошибок
- Среднее время ответа
- P95 и P99 перцентили времени ответа

Если тест не проходит пороги производительности, проверьте:
1. Доступность сервисов (ClickHouse, Redis, Kafka)
2. Нагрузку на базу данных
3. Настройки кэширования
4. Логи приложения на наличие ошибок

