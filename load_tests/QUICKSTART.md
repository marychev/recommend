# ⚡ Быстрый старт нагрузочного тестирования

Краткое руководство для быстрого начала работы с нагрузочным тестированием.

## 🚀 Шаг 1: Установка k6

### macOS
```bash
brew install k6
```

### Linux (Ubuntu/Debian)
```bash
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 \
  --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

### Windows
```powershell
choco install k6
```

## 📦 Шаг 2: Установка зависимостей Python

```bash
pip install -r requirements.txt
```

## 🐳 Шаг 3: Запуск сервисов

```bash
# Запустить все сервисы (ClickHouse, Redis, Kafka, API)
make up

# Инициализировать базу данных
make db-init
```

## 🌱 Шаг 4: Генерация тестовых данных

```bash
# Генерация 1,000,000 записей (~5-10 минут)
make load-test-data-generate

# Или напрямую
python load_tests/generate_test_data.py
```

**Что будет создано:**
- 100,000 пользователей
- 50,000 треков
- 850,000 взаимодействий

## ✅ Шаг 5: Проверка готовности

```bash
# Быстрая проверка (30 секунд)
make load-test-quick

# Или напрямую
k6 run load_tests/quick_test.js
```

## 🎯 Шаг 6: Запуск нагрузочных тестов

### Вариант A: Используя Makefile (рекомендуется)

```bash
# Базовый тест (~15 минут)
make load-test-basic

# Тест пиковой нагрузки (~3 минуты)
make load-test-spike

# Стресс-тест (~30 минут)
make load-test-stress

# Тест на выносливость (~70 минут)
make load-test-soak

# Все тесты последовательно
make load-test-all
```

### Вариант B: Запуск k6 напрямую

```bash
# Базовый тест
k6 run load_tests/k6_basic_load_test.js

# Spike test
k6 run load_tests/k6_spike_test.js

# Stress test
k6 run load_tests/k6_stress_test.js

# Soak test
k6 run load_tests/k6_soak_test.js
```

## 📊 Интерпретация результатов

После каждого теста k6 выведет статистику:

```
✓ GET /users status is 200
✓ GET /tracks status is 200
✓ GET /recommendations status is 200 or 404

checks.........................: 95.00%  ✓ 9500     ✗ 500
http_req_duration..............: avg=456ms  p(95)=1200ms  p(99)=2500ms
http_req_failed................: 5.00%   ✓ 500      ✗ 9500
```

### Хорошие показатели ✅

- **http_req_duration p(95) < 2000ms** - 95% запросов быстрее 2 секунд
- **http_req_failed < 5%** - менее 5% ошибок
- **Стабильное время ответа** - без резких скачков

### Проблемные показатели ⚠️

- **http_req_duration p(95) > 5000ms** - медленные ответы
- **http_req_failed > 10%** - много ошибок
- **Растущее время ответа** - деградация производительности

## 🔧 Настройка тестов

### Изменение базового URL

```bash
# Для другого окружения
export API_URL=http://production.example.com
k6 run load_tests/k6_basic_load_test.js
```

### Изменение параметров нагрузки

Отредактируйте соответствующий `.js` файл:

```javascript
export const options = {
  stages: [
    { duration: '1m', target: 50 },   // Изменить количество пользователей
    { duration: '3m', target: 100 },
  ],
};
```

## 🆘 Устранение неполадок

**📖 Полное руководство:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Быстрые решения

| Проблема | Команда |
|----------|---------|
| ClickHouse не подключен | `make up && sleep 10` |
| Таблицы не созданы | `make db-init` |
| k6 не найден | `brew install k6` |
| API недоступен | `make restart` |
| Мало данных | `make load-test-data-generate` |

### Если что-то пошло не так

```bash
# Полная диагностика
make diagnose

# Перезапуск с нуля
make down
make up
make db-init
make load-test-data-generate

# Проверка логов
make logs-errors
```

### Типичные ошибки и решения

**"ClickHouse client not connected"**
```bash
make up          # Запустите сервисы
sleep 10         # Подождите инициализации
make db-init     # Создайте таблицы
```

**"k6 command not found"**
```bash
# macOS
brew install k6

# Linux
# См. инструкции в Шаг 1
```

**"Connection refused"**
```bash
make ps          # Проверьте статус
make restart     # Перезапустите сервисы
```

## 📈 Мониторинг

### Grafana Cloud (опционально)

Для детального мониторинга используйте Grafana Cloud:

```bash
# Зарегистрируйтесь на https://grafana.com/auth/sign-up/create-user
# Получите токен и запустите:
k6 login cloud --token YOUR_TOKEN
k6 cloud load_tests/k6_basic_load_test.js
```

### Локальный мониторинг

Результаты сохраняются в JSON:

```bash
# Результаты будут в load_tests/results/
make load-test-results

# Или просмотрите напрямую
cat load_tests/results/*.json | jq
```

## 💡 Полезные команды

```bash
# Проверить все Makefile команды
make help

# Диагностика системы
make diagnose

# Проверить health API
make health

# Посмотреть статистику БД
make db-stats

# Посмотреть ошибки
make logs-errors
```

## 📚 Дополнительная документация

- Полная документация: [load_tests/README.md](README.md)
- Документация k6: https://k6.io/docs/
- Примеры k6: https://github.com/grafana/k6/tree/master/examples

---

**Готово! Теперь вы можете запускать нагрузочные тесты! 🚀**

Начните с быстрой проверки:
```bash
make load-test-quick
```

Затем запустите базовый тест:
```bash
make load-test-basic
```

