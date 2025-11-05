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

### Базовый тест нагрузки

Стандартный сценарий для проверки производительности под нагрузкой:

```bash
k6 run load_tests/k6_basic_load_test.js
```

**Параметры:**
- Длительность: ~15 минут
- Максимум пользователей: 200
- Тестирует все основные эндпоинты

### Spike Test (Пиковая нагрузка)

Проверяет поведение системы при резком росте трафика:

```bash
k6 run load_tests/k6_spike_test.js
```

**Параметры:**
- Длительность: ~3 минуты
- Резкий скачок до 500 пользователей
- Проверяет восстановление после пика

### Stress Test (Стресс-тест)

Постепенно увеличивает нагрузку до точки отказа:

```bash
k6 run load_tests/k6_stress_test.js
```

**Параметры:**
- Длительность: ~30 минут
- Максимум пользователей: 500
- Выявляет предел системы

### Soak Test (Тест на выносливость)

Длительный тест для выявления утечек памяти и деградации:

```bash
k6 run load_tests/k6_soak_test.js
```

**Параметры:**
- Длительность: ~70 минут
- Стабильная нагрузка: 50 пользователей
- Проверяет стабильность системы

## 📈 Типы тестов

### 1. Basic Load Test (k6_basic_load_test.js)

**Назначение:** Проверка нормальной работы системы под ожидаемой нагрузкой.

**Сценарии:**
- GET `/api/v1/users` - список пользователей
- GET `/api/v1/users/{id}` - получение пользователя
- GET `/api/v1/tracks` - список треков
- GET `/api/v1/tracks/{id}` - получение трека
- GET `/api/v1/recommendations/{user_id}` - рекомендации
- GET `/api/v1/users/{id}/statistics` - статистика пользователя
- GET `/api/v1/tracks/{id}/statistics` - статистика трека

**Пороговые значения (Thresholds):**
- 95% запросов < 2000ms
- 99% запросов < 5000ms
- Процент ошибок < 5%

### 2. Spike Test (k6_spike_test.js)

**Назначение:** Проверка устойчивости к резким скачкам нагрузки.

**Сценарий:**
- Резкий рост с 10 до 500 пользователей за 10 секунд
- Удержание пиковой нагрузки 1 минуту
- Резкое снижение обратно

**Пороговые значения:**
- 95% запросов < 5000ms
- Процент ошибок < 15%

### 3. Stress Test (k6_stress_test.js)

**Назначение:** Определение максимальной пропускной способности системы.

**Сценарий:**
- Постепенное увеличение с 50 до 500 пользователей
- Шаг увеличения: 100 пользователей каждые 5 минут
- Фокус на тяжелых запросах (рекомендации, статистика)

**Пороговые значения:**
- 95% запросов < 10000ms
- Процент ошибок < 20%

### 4. Soak Test (k6_soak_test.js)

**Назначение:** Выявление утечек памяти и деградации производительности.

**Сценарий:**
- Стабильная нагрузка 50 пользователей
- Длительность: 1 час
- Реалистичные сценарии использования

**Пороговые значения:**
- 95% запросов < 2000ms
- Процент ошибок < 5%

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

## 🔍 Troubleshooting

**📖 Подробное руководство:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Быстрые решения типичных проблем

| Проблема | Решение |
|----------|---------|
| ❌ ClickHouse client not connected | `make up && sleep 10` |
| ❌ Таблицы не созданы | `make db-init` |
| ❌ k6 command not found | `brew install k6` (macOS) |
| ❌ Connection refused | `make restart` |
| ❌ Высокий % ошибок | `make logs-errors` |
| ❌ Медленная генерация | Увеличьте ресурсы Docker |

### Проблема: Слишком много ошибок 500

**Решение:**
```bash
# Проверьте логи сервиса
docker-compose logs -f app

# Проверьте ClickHouse
docker-compose logs -f clickhouse

# Перезапустите сервисы
make restart
```

### Проблема: Низкая производительность

**Решение:**
```bash
# Проверьте данные
make db-stats

# Проверьте Redis
docker-compose logs redis

# Увеличьте ресурсы Docker (память, CPU)
```

### Полная диагностика

```bash
# Выполните комплексную проверку
make diagnose

# Если ничего не помогает
make down && make up && make db-init && make load-test-data-generate
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

