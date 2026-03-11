# TODO

## Безопасность

- [ ] **CORS**: заменить `allow_origins=["*"]` на конкретные домены в продакшене (`app/app.py:38`)
- [ ] **Аутентификация**: добавить API-key или JWT — сейчас все эндпоинты публичные
- [ ] **Rate limiting**: добавить ограничение запросов (slowapi) — защита от злоупотреблений
- [ ] **Ошибки в ответах**: не возвращать `str(e)` клиенту — логировать серверно, клиенту generic 500

## База данных (ClickHouse)

- [ ] **Миграции**: внедрить систему версионирования схемы (сейчас один SQL-файл, ручное применение)
- [ ] **Индексы**: добавить индекс на `user_id` в `user_track_interactions`, на `artist/genre` в `tracks`
- [ ] **TTL**: добавить `TTL timestamp + INTERVAL 2 YEAR` для старых взаимодействий
- [ ] **Оптимизация SQL**: `TODO optimize sql!` в `app/routers/tracks.py:295` — убрать лишний GROUP BY

## Kafka

- [ ] **Dead Letter Queue**: если все 3 fallback-а упали (queue → Kafka → ClickHouse) — событие теряется
- [ ] **Retry с backoff**: в consumer нет экспоненциального backoff при ошибках
- [ ] **Ручной offset commit**: auto-commit может потерять сообщения при падении после коммита

## Redis / Кэш

- [ ] **Cache stampede**: при истечении TTL N запросов одновременно идут в БД — добавить distributed lock
- [ ] **Инвалидация**: кэш не сбрасывается при `play`/`skip` — только при `like`/`dislike`/`add_to_playlist`
- [ ] **Прогрев кэша**: при старте греются popular tracks, но не user recommendations

## Тестирование

- [ ] **cache_debug router**: 14 эндпоинтов без тестов
- [ ] **Интеграционные тесты**: Kafka consumer → ClickHouse полный flow
- [ ] **Сценарии отказов**: Redis down, ClickHouse slow, Kafka unavailable — поведение не покрыто тестами
- [ ] **Semaphore contention**: нет тестов на конкурентные тяжёлые запросы рекомендаций

## DevOps / Docker

- [ ] **Health checks**: добавить для ClickHouse, Zookeeper, Redis, API в docker-compose
- [ ] **Resource limits**: нет memory/cpu limits в docker-compose (только комментарий)
- [ ] **CI/CD**: нет pipeline — линтеры, тесты, сборка, деплой не автоматизированы

## Мониторинг

- [ ] **Prometheus**: `prometheus-client` установлен, но не используется — подключить метрики
- [ ] **Request ID**: нет correlation ID для трассировки запроса через Kafka/Redis/ClickHouse
- [ ] **Structured logging**: перейти на JSON-логи (python-json-logger)
- [ ] **Query timing**: время запросов в ClickHouse и Redis не логируется

## Прочее

- [ ] При `make setup` проверять наличие данных перед вставкой, оптимизировать асинхронностью
- [ ] **Circuit breaker**: при медленном ClickHouse все запросы висят — нет fast-fail
- [ ] **Connection pooling**: один `ClientSession` на ClickHouse клиент, нет лимитов соединений
- [ ] **Валидация входных данных**: нет проверок email формата, duration range, string length
- [ ] Обновить зависимости (fastapi 0.104.1 может быть устаревшим)
