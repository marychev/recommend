# 🚀 Нагрузочное тестирование с k6

Инфраструктура для нагрузочного тестирования Music Recommendation System API с использованием [k6](https://k6.io/).

## 📋 Содержание

- [Установка](#установка)
- [Генерация тестовых данных](#генерация-тестовых-данных)
- [Запуск тестов](#запуск-тестов)
- [Типы тестов](#типы-тестов)
- [Метрики и результаты](#метрики-и-результаты)
- [Настройка](#настройка)

## 🔧 Установка

### 1. Установка k6

**macOS:**
```bash
brew install k6
```

**Linux:**
```bash
# Debian/Ubuntu
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

### 2. Установка Python зависимостей

```bash
pip install -r requirements.txt
```

## 📊 Генерация тестовых данных

Перед запуском нагрузочных тестов необходимо сгенерировать тестовые данные:

```bash
# Убедитесь, что сервисы запущены
docker-compose up -d

# Генерируем 1,000,000 записей
python load_tests/generate_test_data.py
```

Скрипт создаст:
- **100,000 пользователей** (users)
- **50,000 треков** (tracks)
- **850,000 взаимодействий** (user_track_interactions)

**Итого: ~1,000,000 записей**

⏱️ Время генерации: ~5-10 минут в зависимости от производительности системы.

## 🏃 Запуск тестов

### 🔍 Диагностический тест (НАЧНИТЕ С НЕГО!)

**Рекомендуется запускать первым** для выявления проблем:

```bash
make load-test-diagnostics
# или
k6 run load_tests/k6_diagnostics_test.js
```

**Параметры:**
- ⏱️ Длительность: 1 минута
- 👥 Нагрузка: 10 VUs (минимальная)
- 🎯 Без thresholds - только диагностика
- 📊 Детальная статистика по каждому endpoint
- 💡 Автоматические рекомендации

**Что покажет:**
- Какие endpoints самые медленные
- Работает ли кэширование
- Есть ли ошибки
- Конкретные рекомендации по улучшению

---

### ⚡ Quick Test (Быстрая проверка)

Быстрая проверка готовности API:

```bash
make load-test-quick
# или
k6 run load_tests/quick_test.js
```

**Параметры:**
- ⏱️ Длительность: 30 секунд
- 👥 Нагрузка: 5 VUs
- ✅ Проверяет основные endpoints

---

### 🔥 Smoke Test

Минимальный тест работоспособности перед полноценным тестированием:

```bash
make load-test-smoke
# или
k6 run load_tests/k6_smoke_test.js
```

**Параметры:**
- ⏱️ Длительность: ~2 минуты
- 👥 Нагрузка: 2 VUs
- ✅ Проверяет все критичные endpoints
- 🎯 Пороги: p95 < 5s, ошибок < 10%

---

### 📊 Basic Load Test (Базовый нагрузочный тест)

Стандартный сценарий для проверки производительности:

```bash
make load-test-basic
# или
k6 run load_tests/k6_basic_load_test.js
```

**Параметры:**
- ⏱️ Длительность: ~15 минут
- 👥 Максимум: 200 VUs
- 📈 Постепенное увеличение нагрузки
- 🎯 Тестирует все основные endpoints

---

### ⚡ Spike Test (Пиковая нагрузка)

Проверяет поведение при резком росте трафика:

```bash
make load-test-spike
# или
k6 run load_tests/k6_spike_test.js
```

**Параметры:**
- ⏱️ Длительность: ~2 минуты
- 👥 Резкий скачок до 50 VUs
- 🎯 Пороги: p95 < 15s, ошибок < 30%

**Экстремальный вариант (500 VUs, без thresholds):**
```bash
make load-test-spike-extreme
```

---

### 💪 Stress Test (Стресс-тест)

Постепенно увеличивает нагрузку до точки отказа:

```bash
make load-test-stress
# или
k6 run load_tests/k6_stress_test.js
```

**Параметры:**
- ⏱️ Длительность: ~30 минут
- 👥 Максимум: 500 VUs (постепенно)
- 🎯 Выявляет предел системы

---

### 🕐 Soak Test (Тест на выносливость)

Длительный тест для выявления утечек памяти:

```bash
make load-test-soak
# или
k6 run load_tests/k6_soak_test.js
```

**Параметры:**
- ⏱️ Длительность: ~70 минут (1 час)
- 👥 Стабильная нагрузка: 50 VUs
- 🎯 Проверяет стабильность системы

## 📈 Типы тестов и их назначение

| Тест | VUs | Длительность | Назначение | Запуск |
|------|-----|--------------|------------|--------|
| **🔍 Diagnostics** | 10 | 1 мин | Выявление узких мест | `make load-test-diagnostics` |
| **⚡ Quick** | 5 | 30 сек | Быстрая проверка | `make load-test-quick` |
| **🔥 Smoke** | 2 | 2 мин | Готовность к тестам | `make load-test-smoke` |
| **📊 Basic Load** | 50-200 | 15 мин | Нормальная нагрузка | `make load-test-basic` |
| **⚡ Spike** | 4→50 | 2 мин | Пиковые нагрузки | `make load-test-spike` |
| **💥 Spike Extreme** | 10→500 | 1 мин | Экстрим без fail | `make load-test-spike-extreme` |
| **💪 Stress** | 50→500 | 30 мин | Поиск предела | `make load-test-stress` |
| **🕐 Soak** | 50 | 70 мин | Утечки памяти | `make load-test-soak` |

### 🎯 Когда какой тест запускать?

```
📍 РАЗРАБОТКА
├─ 🔍 Diagnostics    → После изменений в коде
├─ ⚡ Quick Test     → Перед коммитом
└─ 🔥 Smoke Test     → Перед pull request

📍 ТЕСТИРОВАНИЕ
├─ 📊 Basic Load     → Основной тест производительности
├─ ⚡ Spike Test     → Проверка на пики (акции, события)
└─ 💪 Stress Test    → Определение максимальной нагрузки

📍 ПРЕДПРОДАКШЕН
└─ 🕐 Soak Test      → Проверка стабильности (запускать на ночь)
```

### 📋 Детальное описание

#### 1️⃣ Diagnostics Test (k6_diagnostics_test.js)

**Назначение:** Детальная диагностика производительности каждого endpoint

**Особенности:**
- БЕЗ thresholds (всегда PASSED)
- Детальная статистика по каждому endpoint
- Автоматический анализ и рекомендации
- Показывает узкие места системы

**Что проверяет:**
- Время ответа Users API
- Время ответа Tracks API
- Время ответа Recommendations (самый тяжелый)
- Работает ли кэширование
- Количество ошибок по endpoint

#### 2️⃣ Quick Test (quick_test.js)

**Назначение:** Быстрая проверка работоспособности

**Thresholds:**
- p95 < 3000ms
- Ошибок < 10%

#### 3️⃣ Smoke Test (k6_smoke_test.js)

**Назначение:** Минимальная проверка перед полноценным тестированием

**Thresholds:**
- p95 < 5000ms
- Ошибок < 10%
- Успешных checks > 90%

**Что проверяет:**
- Health check
- Users API (list & by id)
- Tracks API (list & by id)
- Recommendations API

#### 4️⃣ Basic Load Test (k6_basic_load_test.js)

**Назначение:** Основной тест производительности под реальной нагрузкой

**Сценарии:**
- GET `/api/v1/users` - список пользователей
- GET `/api/v1/users/{id}` - конкретный пользователь
- GET `/api/v1/tracks` - список треков
- GET `/api/v1/tracks/{id}` - конкретный трек
- GET `/api/v1/recommendations/{user_id}` - рекомендации (главное!)
- GET `/api/v1/users/{id}/statistics` - статистика пользователя
- GET `/api/v1/tracks/{id}/statistics` - статистика трека

**Thresholds:**
- p95 < 10000ms, p99 < 20000ms
- Ошибок < 15%

#### 5️⃣ Spike Test (k6_spike_test.js)

**Назначение:** Проверка устойчивости к резким скачкам нагрузки

**Сценарий:**
- Разогрев: 4 VUs (10s)
- Резкий рост: 4 → 50 VUs (20s)
- Удержание: 50 VUs (30s)
- Снижение: 50 → 10 VUs (10s)

**Thresholds:**
- p95 < 15000ms
- Ошибок < 30%

**Экстремальная версия (500 VUs):**
- БЕЗ thresholds - только наблюдение
- Показывает поведение при критической нагрузке

#### 6️⃣ Stress Test (k6_stress_test.js)

**Назначение:** Поиск точки отказа системы

**Сценарий:**
- Постепенное увеличение: 50 → 500 VUs
- Фокус на тяжелых запросах (рекомендации, статистика)

**Thresholds:**
- p95 < 10000ms
- Ошибок < 20%

#### 7️⃣ Soak Test (k6_soak_test.js)

**Назначение:** Выявление утечек памяти и деградации

**Сценарий:**
- Стабильная нагрузка 50 VUs
- Длительность: 1 час
- Реалистичные сценарии пользователя

**Thresholds:**
- p95 < 2000ms, p99 < 5000ms
- Ошибок < 5%

## 📊 Метрики и результаты

### Основные метрики k6:

1. **http_req_duration** - время ответа сервера
   - `avg` - среднее время
   - `med` - медиана
   - `p(95)` - 95 перцентиль
   - `p(99)` - 99 перцентиль

2. **http_req_failed** - процент неуспешных запросов

3. **http_reqs** - общее количество запросов

4. **vus** - количество виртуальных пользователей

5. **vus_max** - максимальное количество пользователей

### Кастомные метрики:

- `users_response_time` - время ответа для /users эндпоинтов
- `tracks_response_time` - время ответа для /tracks эндпоинтов
- `recommendations_response_time` - время ответа для /recommendations
- `errors` - счетчик ошибок

### Результаты сохраняются в:

- `summary.json` - полная статистика (Basic Load Test)
- `stress_test_results.json` - результаты стресс-теста
- `soak_test_results.json` - результаты теста на выносливость

## ⚙️ Настройка

### Переменные окружения:

```bash
# Базовый URL API (по умолчанию: http://localhost:8000)
export API_URL=http://localhost:8000

# Запуск теста
k6 run load_tests/k6_basic_load_test.js
```

### Изменение диапазонов ID:

В каждом k6 скрипте можно настроить диапазоны ID:

```javascript
const USER_ID_MIN = 1;
const USER_ID_MAX = 100000;
const TRACK_ID_MIN = 1;
const TRACK_ID_MAX = 50000;
```

### Настройка пороговых значений:

Измените `thresholds` в блоке `options`:

```javascript
export const options = {
  thresholds: {
    'http_req_duration': ['p(95)<1000'], // 95% запросов < 1s
    'http_req_failed': ['rate<0.01'],     // Менее 1% ошибок
  },
};
```

## 📈 Мониторинг в реальном времени

### Grafana Cloud (рекомендуется)

k6 имеет встроенную интеграцию с Grafana Cloud:

```bash
k6 run --out cloud load_tests/k6_basic_load_test.js
```

### InfluxDB + Grafana

Экспорт метрик в InfluxDB:

```bash
k6 run --out influxdb=http://localhost:8086/k6 load_tests/k6_basic_load_test.js
```

### JSON вывод

Сохранение результатов в JSON:

```bash
k6 run --out json=results.json load_tests/k6_basic_load_test.js
```

## 🎯 Рекомендации

### 1. Подготовка к тестированию

- ✅ Убедитесь, что все сервисы запущены (`docker-compose up -d`)
- ✅ Сгенерируйте тестовые данные
- ✅ Проверьте доступность API (`curl http://localhost:8000/api/v1/health`)
- ✅ Освободите ресурсы системы (закройте лишние приложения)

### 2. Последовательность запуска

1. **Basic Load Test** - базовая проверка
2. **Spike Test** - проверка на пики
3. **Stress Test** - поиск пределов
4. **Soak Test** - проверка стабильности (запускать последним)

### 3. Интерпретация результатов

**Хорошие показатели:**
- ✅ p(95) < 2000ms для большинства запросов
- ✅ Процент ошибок < 5%
- ✅ Стабильное время ответа на протяжении теста
- ✅ RPS (запросов в секунду) растет пропорционально нагрузке

**Проблемные показатели:**
- ❌ Растущее время ответа при стабильной нагрузке
- ❌ Высокий процент ошибок (> 10%)
- ❌ Большая разница между p(95) и p(99)
- ❌ Падение RPS при увеличении пользователей

### 4. Оптимизация

Если тесты показывают проблемы:

1. **Увеличьте кэширование** - проверьте Redis
2. **Оптимизируйте запросы** - проверьте ClickHouse запросы
3. **Масштабируйте** - добавьте больше инстансов
4. **Настройте пулы** - увеличьте connection pools
5. **Добавьте индексы** - оптимизируйте БД

## 🔍 Диагностика и решение проблем

### 📋 Рекомендуемая последовательность

```bash
# 1️⃣ Проверьте базовую готовность системы
make diagnose

# 2️⃣ Запустите диагностический тест (ОБЯЗАТЕЛЬНО!)
make load-test-diagnostics

# 3️⃣ Запустите smoke test
make load-test-smoke

# 4️⃣ Если все OK - запускайте полноценные тесты
make load-test-basic
```

### 🎯 Если тесты падают

**Шаг 1: Запустите диагностику**
```bash
make load-test-diagnostics
```

Это покажет:
- ✅ Какие endpoints самые медленные
- ✅ Работает ли кэширование
- ✅ Есть ли ошибки
- ✅ Конкретные рекомендации

**Шаг 2: Проверьте логи**
```bash
make logs-errors  # Ошибки из всех сервисов
```

**Шаг 3: Проверьте подключения**
```bash
# ClickHouse
docker exec music_recommend_clickhouse clickhouse-client --query "SELECT 1"

# Redis
docker exec music_recommend_redis redis-cli PING

# Kafka
docker exec music_recommend_kafka kafka-topics.sh --bootstrap-server localhost:9092 --list
```

### 📖 Полное руководство

**Детальное руководство по диагностике:** [DIAGNOSTICS_GUIDE.md](DIAGNOSTICS_GUIDE.md)

Содержит:
- Типы проблем и их симптомы
- Пошаговая диагностика
- Оптимизация ClickHouse, Redis, API
- Масштабирование системы
- Мониторинг и метрики

### Быстрые решения типичных проблем

| Проблема | Причина | Решение |
|----------|---------|---------|
| ❌ ClickHouse client not connected | БД недоступна | `make restart` |
| ❌ Таблицы не созданы | Нет инициализации | `make db-init` |
| ❌ k6 command not found | k6 не установлен | `brew install k6` |
| ❌ Connection refused | API не запущен | `make up` |
| ❌ Высокий % ошибок | См. логи | `make logs-errors` |
| ❌ Медленные запросы | Мало ресурсов | Увеличьте CPU/RAM Docker |
| ❌ Нет данных | Не сгенерированы | `make load-test-data-generate` |

### Проблема: Тесты падают с ошибками

```bash
# 1. Проверьте, что данные есть
make db-stats
# Должно быть: users: 100000+, tracks: 50000+, interactions: 850000+

# 2. Если данных нет - сгенерируйте
make load-test-data-generate

# 3. Перезапустите все сервисы
make restart

# 4. Запустите диагностику
make load-test-diagnostics
```

### Проблема: Медленная производительность

```bash
# 1. Запустите диагностику
make load-test-diagnostics
# Посмотрите, какие endpoints медленные

# 2. Проверьте кэш Redis
docker exec music_recommend_redis redis-cli
> KEYS *recommendations*
> INFO memory

# 3. Проверьте ClickHouse
docker stats music_recommend_clickhouse
# Если CPU > 80% - нужно больше ресурсов

# 4. Проверьте логи на медленные запросы
make logs-api | grep "slow\|timeout"
```

### Проблема: Spike test не проходит

Это **НОРМАЛЬНО** если:
- У вас слабое железо (< 8GB RAM, < 4 CPU cores)
- Docker контейнерам выделено мало ресурсов
- Вы запускаете на WSL2/Windows

**Решения:**

1. **Уменьшите нагрузку** - уже сделано (50 VUs вместо 500)
2. **Запустите extreme версию без thresholds:**
```bash
make load-test-spike-extreme
# Покажет метрики без fail
```
3. **Увеличьте ресурсы Docker** в Docker Desktop Settings

### Полная диагностика системы

```bash
# Комплексная проверка всего
make diagnose

# Если ничего не помогает - полный рестарт
make down && make up && make db-init
sleep 30
make load-test-data-generate
make load-test-diagnostics
```

## 📚 Дополнительные ресурсы

- [k6 Documentation](https://k6.io/docs/)
- [k6 Best Practices](https://k6.io/docs/testing-guides/test-types/)
- [Grafana k6 Examples](https://github.com/grafana/k6/tree/master/examples)
- [k6 Community Forum](https://community.k6.io/)

## 📝 Примеры команд

```bash
# Базовый запуск
k6 run load_tests/k6_basic_load_test.js

# С кастомными параметрами
k6 run --vus 100 --duration 5m load_tests/k6_basic_load_test.js

# С переменными окружения
API_URL=http://production.example.com k6 run load_tests/k6_basic_load_test.js

# Запуск в режиме quiet
k6 run --quiet load_tests/k6_basic_load_test.js

# Только проверка скрипта (без выполнения)
k6 inspect load_tests/k6_basic_load_test.js
```

---

**Создано для:** Music Recommendation System  
**Инструмент:** k6 by Grafana Labs  
**Версия:** 1.0.0

