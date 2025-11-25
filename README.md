# 🎵 Music Recommendation System

<div align="center">

[Документация](docs/INDEX.md) • [API Docs](http://localhost:8000/docs) • [Тесты](docs/RUN_TESTS.md)

</div>

---

## 📋 Описание

Music Recommendation System - это полнофункциональная рекомендательная система для музыкальных треков, использующая алгоритмы машинного обучения для персонализированных рекомендаций.

### ✨ Основные возможности

- 🎯 **Персонализированные рекомендации** на основе Collaborative Filtering
- 📊 **Аналитика в реальном времени** на ClickHouse (OLAP)
- 🔄 **Стриминг событий** через Kafka
- ⚡ **Оптимизированное Redis кэширование** рекомендаций (85-90% hit rate, ускорение в 100-800x)
- 📡 **REST API** с автоматической документацией (Swagger/ReDoc)

---

## 🚀 Быстрый старт

### Вариант 1: Makefile (самый быстрый) ⚡

```bash
# 🎉 Запустить ВСЁ сразу (backend + frontend)!
make quickstart

# Или по отдельности:
make up          # Запустить Docker сервисы
make db-init     # Создать таблицы

make help        # Посмотреть все доступные команды
make down        # Остановить все сервисы
```

**Откройте:**
- Kafka UI: http://localhost:8081
- Swagger API: http://localhost:8000/docs
- ClickHouse: http://localhost:8123/play


### Вариант 2: Локальная разработка 💻

```bash
# 1. Установите зависимости
pip install -r requirements.txt

# 2. Запустите инфраструктуру
make up-clickhouse      # Запустить ClickHouse
make up-kafka           # Запустить Kafka
make up-redis           # Запустить Redis

# 3. Инициализируйте БД
make db-init

# 4. Запустите API локально
make run-api            # или python -m app.main
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
- 📝 [Руководство по Makefile](docs/MAKEFILE.md)
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
make test
# Пересоздайте ClickHouse с правильной конфигурацией
bash scripts/docker-reset-clickhouse.sh
# С покрытием кода
pytest --cov=app --cov-report=html
```

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
| **Kafka UI** | 8081 | http://localhost:8081 | Мониторинг Kafka 📊 |
| FastAPI | 8000 | http://localhost:8000 | REST API |
| Swagger UI | 8000 | http://localhost:8000/docs | Интерактивная документация |
| ClickHouse HTTP | 8123 | http://localhost:8123 | Для приложения ✅ |
| ClickHouse Native | 9000 | - | Для CLI клиента |
| Redis | 6379 | - | Cache |
| Kafka | 9092 | - | Events (localhost), 29092 (Docker) |
| Zookeeper | 2181 | - | Kafka coordination |

> 🔍 **Подробнее**: [docs/PORTS.md](docs/PORTS.md)

---

## 🐳 Docker

### Сервисы в docker-compose.yml

- ✅ **ClickHouse** - OLAP база данных
- ✅ **Kafka + Zookeeper** - Стриминг событий
- ✅ **Kafka UI** - Веб интерфейс для мониторинга Kafka
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

> 📖 **Полный список команд**: [docs/MAKEFILE.md](docs/MAKEFILE.md)


---

## ⚡ Производительность

### Целевые показатели

- **API Latency**: < 100ms (p99)
- **Throughput**: 10,000 events/sec
- **Recommendation Generation**: < 200ms (первый раз), < 20ms (из кэша)
- **ClickHouse Query**: < 50ms (простые), < 500ms (сложные)
- **Cache Hit Rate**: 85-90% (для рекомендаций, после оптимизации)

### Оптимизации

- ✅ Партиционирование данных по времени
- ✅ Материализованные представления
- ✅ Батчинг вставок в ClickHouse
- ✅ Индексы на часто используемых полях
- ✅ Трехэтапная оптимизация кэширования (hit rate 85-90%)
- ✅ Селективная инвалидация кэша (только при значимых событиях)
- ✅ Конфигурируемый TTL (2-4 часа оптимально)
- ✅ Предварительный прогрев для активных пользователей

---

## 📝 Roadmap

### ✅ v1.0 - MVP (Готово)
- [x] FastAPI + Pydantic V2
- [x] ClickHouse интеграция
- [x] Collaborative Filtering
- [x] REST API с документацией
- [x] 60+ автоматических тестов
- [x] Docker Compose

### 🚧 v1.1 - Kafka Integration (Готово)
- [x] Kafka producer для событий
- [x] Kafka consumer для обработки
- [x] Асинхронная обработка потока

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

