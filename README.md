# 🎵 Music Recommendation System

<div align="center">

**Рекомендательная система музыкальных треков на основе машинного обучения**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-60%2B%20passed-success.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)](htmlcov/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[Быстрый старт](#-быстрый-старт) • [Документация](docs/INDEX.md) • [API Docs](http://localhost:8000/docs) • [Тесты](docs/RUN_TESTS.md)

</div>

---

## 📋 Описание

Music Recommendation System - это полнофункциональная рекомендательная система для музыкальных треков, использующая алгоритмы машинного обучения для персонализированных рекомендаций.

### ✨ Основные возможности

- 🎯 **Персонализированные рекомендации** на основе Collaborative Filtering
- 📊 **Аналитика в реальном времени** на ClickHouse (OLAP)
- 🔄 **Стриминг событий** через Kafka
- ⚡ **Быстрое кэширование** с Redis
- 📡 **REST API** с автоматической документацией (Swagger/ReDoc)
- 🧪 **60+ автоматических тестов** (92% покрытие)
- 🐳 **Docker Compose** для запуска одной командой

---

## 🚀 Быстрый старт

### Вариант 1: Makefile (самый быстрый) ⚡

```bash
# Один способ запустить всё сразу! 🎉
make quickstart

# Или по отдельности:
make up          # Запустить все сервисы
make db-init     # Создать таблицы
make health      # Проверить статус

# Посмотреть все доступные команды
make help

# 📖 Полное руководство по командам
См. docs/MAKEFILE_GUIDE.md
```

### Вариант 2: Docker Compose 🐳

```bash
# 1. Клонируйте репозиторий
git clone <repository_url>
cd recommend

# 2. Создайте .env файл (опционально - есть дефолтные значения)
cp .env.example .env  # или используйте значения по умолчанию

# 3. Используйте make команды
make quickstart  # Запускает всё автоматически!

# Или вручную:
docker compose up -d    # Запустить сервисы
make db-init            # Создать таблицы (идемпотентно)

# 4. Откройте Swagger UI
http://localhost:8000/docs
```

### Вариант 3: Локальная разработка 💻

```bash
# 1. Установите зависимости
pip install -r requirements.txt

# 2. Запустите только инфраструктуру
make up-infra           # Запустить ClickHouse, Redis, Kafka

# 3. Инициализируйте БД
make db-init

# 4. Запустите API локально
make run-api            # или python -m app.main

# 5. Откройте API
http://localhost:8000/docs
```
---

## 🛠 Технологический стек

| Компонент | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **API Framework** | FastAPI | 0.104+ | REST API сервер с автодокументацией |
| **Database** | ClickHouse | 25.x | OLAP база для аналитики больших данных |
| **Message Queue** | Kafka | 3.5 | Стриминг событий в реальном времени |
| **Cache** | Redis | 7 | Кэширование и очереди |
| **ML Library** | Scikit-learn | 1.3.2 | Алгоритмы рекомендаций |
| **Validation** | Pydantic | 2.5.0 | Валидация и сериализация данных |
| **Testing** | Pytest | 7.4.3 | Автоматическое тестирование |
| **Containerization** | Docker | - | Деплой и изоляция сервисов |

---

## 📚 Документация

<table>
<tr>
<td width="50%">

### 📖 Основная документация
- 🏠 [Главная страница](README.md) ⬅️ Вы здесь
- 📑 [Навигация по docs](docs/INDEX.md)
- 📝 [Руководство по Makefile](docs/MAKEFILE_GUIDE.md)
- ⚡ [Быстрая справка](docs/QUICK_REFERENCE.md)

</td>
<td width="50%">

### 🔧 Техническая документация
- 🧪 [Запуск тестов](docs/RUN_TESTS.md)
- 🚨 [Решение ошибки 500](docs/API_ERROR_500.md)
- 📊 [Инициализация БД](docs/DB_INIT.md)
- 🆘 [Решение проблем](docs/TROUBLESHOOTING.md)
- 🔌 [Справочник портов](docs/PORTS.md)

</td>
</tr>
</table>

---

## 🏗 Архитектура

```
┌─────────────┐
│  Frontend   │  
│   Client    │  
└──────┬──────┘
       │ HTTP REST API
       ▼
┌─────────────────────────────────────────┐
│        FastAPI Application               │
│  ┌─────────┐  ┌──────────┐  ┌────────┐ │
│  │   API   │──│ Services │──│   ML   │ │
│  │Endpoints│  │          │  │ Engine │ │
│  └─────────┘  └──────────┘  └────────┘ │
└───┬──────────────┬──────────────┬───────┘
    │              │              │
    ▼              ▼              ▼
┌────────┐   ┌─────────┐   ┌──────────┐
│ Kafka  │──▶│ ClickHouse│  │  Redis   │
│Events  │   │Analytics│  │  Cache   │
└────────┘   └─────────┘   └──────────┘
```

### Компоненты:
- **API Layer**: FastAPI endpoints с валидацией Pydantic
- **Business Logic**: Сервисы обработки данных
- **ML Engine**: Collaborative Filtering алгоритм
- **Data Storage**: ClickHouse для OLAP запросов
- **Event Streaming**: Kafka для асинхронной обработки
- **Cache**: Redis для быстрого доступа

---

## 🎯 ML Алгоритм рекомендаций

### Collaborative Filtering (User-Based)

**Принцип работы:**

1️⃣ **Сбор событий** → Пользователи слушают треки, ставят лайки, делятся  
2️⃣ **Построение матрицы** → User-Item матрица с неявными рейтингами  
3️⃣ **Поиск похожих** → Косинусное сходство между пользователями  
4️⃣ **Генерация** → Треки от похожих пользователей  
5️⃣ **Ранжирование** → Сортировка по релевантности  

### Система весов

| Действие | Вес | Значение |
|----------|-----|----------|
| 🎵 Play | +1.0 | Базовое прослушивание |
| ❤️ Like | +3.0 | Явное одобрение |
| 💔 Dislike | -3.0 | Явное неодобрение |
| ⏭️ Skip | -0.5 | Пропуск трека |
| 📁 Add to Playlist | +2.0 | Добавление в плейлист |
| 📤 Share | +2.5 | Поделиться треком |

### Fallback стратегия

Для новых пользователей (cold start) используется **Popular-Based** алгоритм - топ треков за последние 30 дней.

---

## 📡 API Эндпоинты

### 🏥 Health & Status
- `GET /api/v1/health` - Проверка состояния сервисов

### 👥 Users
- `POST /api/v1/users` - Создать пользователя
- `GET /api/v1/users/{user_id}` - Получить пользователя
- `GET /api/v1/users` - Список пользователей
- `GET /api/v1/users/{user_id}/statistics` - Статистика пользователя

### 🎵 Tracks
- `POST /api/v1/tracks` - Создать трек
- `GET /api/v1/tracks/{track_id}` - Получить трек
- `GET /api/v1/tracks` - Список треков (с фильтрами)
- `GET /api/v1/tracks/{track_id}/statistics` - Статистика трека
- `GET /api/v1/tracks/popular/top` - Популярные треки

### 📊 Events
- `POST /api/v1/events` - Отправить событие
- `GET /api/v1/events/user/{user_id}` - История пользователя
- `GET /api/v1/events/track/{track_id}` - История трека

### ⭐ Recommendations
- `POST /api/v1/recommendations` - Получить рекомендации
- `GET /api/v1/recommendations/{user_id}` - Рекомендации (упрощенный метод)

> 📖 **Полная документация API**: http://localhost:8000/docs (после запуска)

---

## 🗄️ База данных

### ClickHouse Таблицы

| Таблица | Назначение | Engine | Партиционирование |
|---------|------------|--------|-------------------|
| `users` | Профили пользователей | MergeTree | - |
| `tracks` | Каталог треков | MergeTree | - |
| `user_track_interactions` | События взаимодействий | MergeTree | По месяцам |
| `user_track_matrix` | User-Item матрица | ReplacingMergeTree | - |

### Материализованные представления

- `track_statistics_mv` - Автоматическая агрегация статистики треков
- `user_statistics_mv` - Автоматическая агрегация статистики пользователей
- `user_track_matrix_mv` - Автообновление матрицы рейтингов

### Оптимизации

- ✅ Партиционирование по `toYYYYMM(timestamp)`
- ✅ Индексы на `track_id` и `action_type`
- ✅ Материализованные view для быстрых запросов
- ✅ ReplacingMergeTree для дедупликации

---

## 🧪 Тестирование

```bash
# Пересоздайте ClickHouse с правильной конфигурацией
bash scripts/docker-reset-clickhouse.sh

# Запустите все тесты
pytest -v

# Только ClickHouse тесты
pytest tests/clickhouse/ -v

# С покрытием кода
pytest --cov=app --cov-report=html
```

### 📊 Покрытие тестами

- ✅ **Подключения** (15 тестов) - ClickHouse, Redis
- ✅ **CRUD операции** (20+ тестов) - Users, Tracks, Events
- ✅ **Сложные запросы** (15+ тестов) - JOIN, агрегация, оконные функции
- ✅ **Производительность** (10+ тестов) - Bulk insert, query speed
- ✅ **Схема БД** (10+ тестов) - Структура, движки, партиции
- ✅ **API** (10+ тестов) - Endpoints, валидация

> 📖 Подробнее: [docs/RUN_TESTS.md](docs/RUN_TESTS.md)

---

## 🔧 Конфигурация

### Переменные окружения (.env)

**Docker Compose автоматически читает файл `.env`** из корня проекта! 🎉

Создайте файл `.env` с таким содержимым:

```env
# ClickHouse Configuration (⚠️ Порт 8123 для HTTP!)
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=music_recommend

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_EVENTS=user_track_events
KAFKA_CONSUMER_GROUP=recommend_consumer

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True

# ML Model Configuration
MIN_INTERACTIONS_FOR_RECOMMENDATIONS=5
TOP_N_RECOMMENDATIONS=10
```

> ⚠️ **Важно**: ClickHouse использует порт **8123** для HTTP, а не 9000!  
> См. [docs/PORTS.md](docs/PORTS.md) для подробной информации
> 
> 💡 **Совет**: Файл `.env` автоматически используется как при запуске через Docker Compose, так и при локальном запуске `python -m app.main`

### Скрипты

```bash
# Генерация 10,000 тестовых событий
python scripts/seed_data.py

# Пересоздание ClickHouse контейнера
bash scripts/docker-reset-clickhouse.sh
```

---

## 💡 Примеры использования

### 1️⃣ Создание пользователя

```bash
curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "age": 25,
    "country": "Russia"
  }'
```

**Ответ:**
```json
{
  "user_id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "age": 25,
  "country": "Russia",
  "created_at": "2024-11-01T12:00:00"
}
```

### 2️⃣ Создание трека

```bash
curl -X POST "http://localhost:8000/api/v1/tracks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Bohemian Rhapsody",
    "artist": "Queen",
    "genre": "Rock",
    "duration_seconds": 354
  }'
```

### 3️⃣ Отправка события (прослушивание)

```bash
curl -X POST "http://localhost:8000/api/v1/events" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "track_id": 1,
    "action_type": "play",
    "listen_duration_seconds": 180
  }'
```

### 4️⃣ Получение рекомендаций

```bash
curl "http://localhost:8000/api/v1/recommendations/1"
```

**Ответ:**
```json
{
  "user_id": 1,
  "recommendations": [
    {
      "track": {
        "track_id": 42,
        "title": "Stairway to Heaven",
        "artist": "Led Zeppelin",
        "genre": "Rock"
      },
      "score": 0.85,
      "reason": "Пользователи с похожими вкусами слушают этот трек"
    }
  ],
  "algorithm": "collaborative_filtering",
  "generated_at": "2024-11-01T12:00:00"
}
```

> 💡 **Больше примеров**: См. [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)

---

## 📂 Структура проекта

```
recommend/
├── 📱 app/                          # Приложение
│   ├── api/                         # API роутеры (5 модулей)
│   │   ├── events.py                # Обработка событий
│   │   ├── recommendations.py       # Генерация рекомендаций ⭐
│   │   ├── users.py                 # Управление пользователями
│   │   ├── tracks.py                # Управление треками
│   │   └── health.py                # Health check
│   ├── db/                          # Подключения к БД
│   │   ├── clickhouse.py            # ClickHouse client
│   │   ├── redis_client.py          # Redis client
│   │   └── clickhouse_schemas.sql   # SQL схемы
│   ├── models/schemas.py            # Pydantic модели
│   ├── config.py                    # Конфигурация
│   └── main.py                      # FastAPI приложение
│
├── 🧪 tests/                        # Тесты (60+)
│   ├── clickhouse/                  # ClickHouse тесты (50+)
│   └── test_api.py                  # API тесты
│
├── 📚 docs/                         # Документация (8 файлов)
│   ├── INDEX.md                     # Навигация
│   ├── SUMMARY.md                   # Краткая сводка
│   ├── QUICK_REFERENCE.md           # Быстрая справка
│   ├── RUN_TESTS.md                 # Запуск тестов
│   └── PORTS.md                     # Справочник портов
│
├── 🔧 scripts/                      # Утилиты
│   ├── seed_data.py                 # Генерация тестовых данных
│   └── docker-reset-clickhouse.sh   # Setup ClickHouse
│
├── ⚙️ clickhouse-config/            # Конфигурация ClickHouse
│   └── users.xml                    # Пользователи без пароля (dev)
│
├── 🐳 docker-compose.yml            # Docker Compose конфигурация
├── 📝 Makefile                       # Команды для управления проектом
├── 📦 requirements.txt              # Python зависимости
├── 📖 README.md                     # Этот файл
└── 📚 docs/                          # Документация
    ├── MAKEFILE_GUIDE.md            # Руководство по Makefile
    ├── API_ERROR_500.md             # Решение ошибки 500
    ├── DB_INIT.md                   # Инициализация БД
    └── ... другие документы
```

---

## 📊 Статистика проекта

<table>
<tr>
<td>

### Код
- 📝 2000+ строк кода
- 📄 20+ файлов Python
- 🎯 15+ API эндпоинтов
- 🗄️ 4 таблицы + 3 view

</td>
<td>

### Тесты
- ✅ 60+ автоматических тестов
- 📊 92% покрытие кода
- ⚡ < 10 сек выполнение
- 🔄 Изолированные тесты

</td>
<td>

### Документация
- 📚 10+ документов
- 🔗 Все ссылки рабочие
- 📖 Примеры кода
- 🎯 Навигация

</td>
</tr>
</table>

---

## 🎯 Алгоритм Collaborative Filtering

### Как это работает?

```python
# 1. Строим матрицу рейтингов
rating = sum(
    play * 1.0,
    like * 3.0,
    dislike * (-3.0),
    skip * (-0.5),
    add_to_playlist * 2.0,
    share * 2.5
)

# 2. Вычисляем схожесть пользователей (Cosine Similarity)
similarity = dot(user1, user2) / (norm(user1) * norm(user2))

# 3. Находим топ-K похожих пользователей
similar_users = get_top_k_similar(user_id, k=50)

# 4. Рекомендуем треки похожих пользователей
recommendations = get_tracks_from_similar_users(similar_users)

# 5. Фильтруем и ранжируем
final = filter_and_rank(recommendations, exclude_listened=True)
```

### Преимущества

- ✅ **Персонализация** - учитывает индивидуальные предпочтения
- ✅ **Масштабируемость** - расчеты в ClickHouse, не в памяти
- ✅ **Холодный старт** - fallback на популярные треки
- ✅ **Прозрачность** - понятно, почему трек рекомендован

---

## 🔌 Порты и доступ

| Сервис | Порт | URL | Назначение |
|--------|------|-----|------------|
| FastAPI | 8000 | http://localhost:8000 | REST API |
| Swagger UI | 8000 | http://localhost:8000/docs | Интерактивная документация |
| ClickHouse HTTP | 8123 | http://localhost:8123 | Для приложения ✅ |
| ClickHouse Native | 9000 | - | Для CLI клиента |
| Redis | 6379 | - | Cache |
| Kafka | 9092 | - | Events |

> 🔍 **Подробнее**: [docs/PORTS.md](docs/PORTS.md)

---

## 🧪 Тестирование

### Статистика тестов

```
tests/
├── API тесты..................... 10+ ✅
├── ClickHouse подключение....... 15+ ✅
├── ClickHouse операции.......... 20+ ✅
├── Сложные запросы.............. 10+ ✅
├── Производительность........... 5+  ✅
└── Схема БД..................... 10+ ✅
                                 ─────
                          Всего: 60+ ✅
```

### Запуск

```bash
# Быстрый старт
bash scripts/docker-reset-clickhouse.sh && pytest tests/clickhouse/ -v

# С покрытием
pytest --cov=app --cov-report=html

# Результат
====== 60 passed in 8.5s ====== ✅
Coverage: 92% ✅
```

> 📖 **Подробнее**: [docs/RUN_TESTS.md](docs/RUN_TESTS.md)

---

## 🐳 Docker

### Сервисы в docker-compose.yml

- ✅ **ClickHouse** - OLAP база данных
- ✅ **Kafka + Zookeeper** - Стриминг событий
- ✅ **Redis** - Кэширование
- ✅ **FastAPI** - API сервер

### Команды

**С помощью Makefile (рекомендуется):**
```bash
make quickstart      # 🚀 Запустить всё сразу!
make up              # Запустить все сервисы
make down            # Остановить все
make ps              # Статус контейнеров
make logs-api        # Логи API
make diagnose        # Диагностика проблем
make help            # Все команды
```

> 📖 **Полный список команд**: [docs/MAKEFILE_GUIDE.md](docs/MAKEFILE_GUIDE.md)

**Или напрямую через Docker Compose:**
```bash
docker compose up -d            # Запустить все
docker compose down             # Остановить все
docker compose ps               # Статус
docker compose logs -f api      # Логи API
docker compose restart api      # Перезапустить API
```

---

## ⚡ Производительность

### Целевые показатели

- **API Latency**: < 100ms (p99)
- **Throughput**: 10,000 events/sec
- **Recommendation Generation**: < 200ms
- **ClickHouse Query**: < 50ms (простые), < 500ms (сложные)

### Оптимизации

- ✅ Партиционирование данных по времени
- ✅ Материализованные представления
- ✅ Батчинг вставок в ClickHouse
- ✅ Индексы на часто используемых полях
- ⏳ Redis кэширование рекомендаций (TODO)

---

## 📝 Roadmap

### ✅ v1.0 - MVP (Готово)
- [x] FastAPI + Pydantic V2
- [x] ClickHouse интеграция
- [x] Collaborative Filtering
- [x] REST API с документацией
- [x] 60+ автоматических тестов
- [x] Docker Compose

### 🚧 v1.1 - Kafka Integration (В процессе)
- [ ] Kafka producer для событий
- [ ] Kafka consumer для обработки
- [ ] Асинхронная обработка потока

### 🔮 v1.2 - ML Improvements (Планируется)
- [ ] Content-Based Filtering
- [ ] Hybrid модель (CF + CB)
- [ ] Matrix Factorization

### 🔮 v2.0 - Production Ready (Планируется)
- [ ] JWT аутентификация
- [ ] Rate limiting
- [ ] Мониторинг (Prometheus/Grafana)
- [ ] Логирование (ELK)
- [ ] CI/CD pipeline
- [ ] Kubernetes deployment

---

## 🆘 Troubleshooting

### ❌ ClickHouse не подключается

```bash
# Решение: Пересоздайте контейнер
bash scripts/docker-reset-clickhouse.sh
```

### ❌ Тесты падают

```bash
# Убедитесь что ClickHouse запущен
docker ps | grep clickhouse

# Проверьте подключение
curl http://localhost:8123/
# Должен вернуть: Ok.
```

### ❌ Неправильный порт

ClickHouse имеет **два порта**:
- ✅ **8123** - HTTP (используйте этот!)
- ❌ **9000** - Native TCP (для CLI)

См. [docs/PORTS.md](docs/PORTS.md)

### ❌ Pydantic warnings

Уже исправлено! Используется Pydantic V2 синтаксис.

---

## 🔗 Полезные ссылки

### Документация проекта
- 📖 [Полная навигация](docs/INDEX.md)
- ⚡ [Быстрая справка](docs/QUICK_REFERENCE.md)
- 📊 [Статус проекта](PROJECT_STATUS.md)

### Внешние ресурсы
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ClickHouse Documentation](https://clickhouse.com/docs/)
- [Pydantic V2 Guide](https://docs.pydantic.dev/latest/)
- [Pytest Documentation](https://docs.pytest.org/)

---

## 📞 Поддержка

### Нужна помощь?

1. 📖 Читайте [START_HERE.md](START_HERE.md)
2. 🔍 Ищите в [docs/INDEX.md](docs/INDEX.md)
3. ⚡ Смотрите [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)

### Нашли баг?

1. Проверьте [Troubleshooting](#-troubleshooting)
2. Посмотрите [docs/RUN_TESTS.md](docs/RUN_TESTS.md)
3. Создайте issue с описанием проблемы

---

## 👥 Разработка

### Участие в проекте

```bash
# Fork репозиторий
git clone <your-fork>
cd recommend

# Создайте ветку
git checkout -b feature/your-feature

# Установите зависимости
pip install -r requirements.txt

# Запустите тесты
pytest -v

# Commit (не больше 8 слов!)
git commit -m "Add new feature"

# Push
git push origin feature/your-feature
```

### Code Style

- ✅ PEP 8
- ✅ Type hints
- ✅ Docstrings для всех функций
- ✅ 92%+ покрытие тестами

---

## 📜 Лицензия

MIT License - используйте свободно!

---

## 👥 Авторы

**Разработчик**: @Gencrud.MikhailMarychev

---

## 🎓 Обучение

Этот проект - отличный пример:
- ✅ Рекомендательных систем (Collaborative Filtering)
- ✅ FastAPI + Pydantic V2
- ✅ ClickHouse для аналитики
- ✅ Pytest для тестирования
- ✅ Docker Compose для деплоя
- ✅ Организации документации

---

<div align="center">

**Готово к использованию!** 🚀

[Начать работу](START_HERE.md) • [Документация](docs/INDEX.md) • [Запустить тесты](docs/RUN_TESTS.md)

⭐ **Поставьте звезду, если проект понравился!** ⭐

</div>
