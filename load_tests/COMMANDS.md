# Команды для Запуска K6 Тестов

## 🚀 Быстрый старт

### 1. Быстрый тест (5 минут) - **РЕКОМЕНДУЕТСЯ ДЛЯ НАЧАЛА**
```bash
k6 run load_tests/k6_quick_test.js
```

### 2. Полный сценарий (51 минута)
```bash
k6 run load_tests/k6_full_user_scenario_test.js
```

### 3. Тест производительности рекомендаций
```bash
k6 run load_tests/k6_recommendations_performance_test.js
```

---

## 🔧 С параметрами

### Указать URL API
```bash
k6 run --env API_URL=http://localhost:8000 load_tests/k6_quick_test.js
```

### Изменить количество VU (виртуальных пользователей)
```bash
k6 run --vus 50 --duration 2m load_tests/k6_quick_test.js
```

### Запустить только определенный сценарий
```bash
# Только Load Test
k6 run --include-scenario-in-results load_test load_tests/k6_full_user_scenario_test.js

# Только Stress Test
k6 run --include-scenario-in-results stress_test load_tests/k6_full_user_scenario_test.js

# Только Spike Test
k6 run --include-scenario-in-results spike_test load_tests/k6_full_user_scenario_test.js
```

---

## 📊 С выводом результатов

### HTML отчет (уже включен по умолчанию)
```bash
k6 run load_tests/k6_full_user_scenario_test.js
# Откройте summary_full_scenario.html в браузере
```

### JSON отчет
```bash
k6 run --out json=results.json load_tests/k6_quick_test.js
```

### CSV отчет
```bash
k6 run --out csv=results.csv load_tests/k6_quick_test.js
```

### Вывод в файл
```bash
k6 run load_tests/k6_quick_test.js > test_results.txt 2>&1
```

---

## 📈 Интеграция с мониторингом

### InfluxDB
```bash
# 1. Запустите InfluxDB
docker run -p 8086:8086 influxdb:1.8

# 2. Запустите тест с выводом в InfluxDB
k6 run --out influxdb=http://localhost:8086/k6 load_tests/k6_full_user_scenario_test.js
```

### Grafana Cloud
```bash
# Получите токен в Grafana Cloud
k6 run --out cloud load_tests/k6_full_user_scenario_test.js
```

### StatsD
```bash
k6 run --out statsd load_tests/k6_quick_test.js
```

---

## 🎯 Специальные сценарии

### Smoke Test (проверка работоспособности)
```bash
k6 run --vus 1 --duration 1m load_tests/k6_quick_test.js
```

### Soak Test (длительный тест на утечки памяти)
```bash
k6 run --vus 10 --duration 4h load_tests/k6_quick_test.js
```

### Spike Test (резкий скачок нагрузки)
```bash
k6 run --stage 30s:10,10s:100,30s:10 load_tests/k6_quick_test.js
```

### Stress Test (поиск точки отказа)
```bash
k6 run --stage 2m:10,5m:50,2m:100,5m:200,10m:0 load_tests/k6_quick_test.js
```

---

## 🐛 Отладка

### Вывод детальных логов
```bash
k6 run --verbose load_tests/k6_quick_test.js
```

### Вывод HTTP запросов
```bash
k6 run --http-debug load_tests/k6_quick_test.js
```

### Вывод полных HTTP запросов и ответов
```bash
k6 run --http-debug="full" load_tests/k6_quick_test.js
```

### Пропустить проверку TLS сертификата
```bash
k6 run --insecure-skip-tls-verify load_tests/k6_quick_test.js
```

---

## 🔄 Использование скрипта

### Linux/Mac
```bash
chmod +x load_tests/run_tests.sh
./load_tests/run_tests.sh
```

### Windows PowerShell
```powershell
# Создайте файл run_tests.ps1 или используйте напрямую k6 команды
k6 run load_tests\k6_quick_test.js
```

---

## 📦 Batch запуск

### Запустить все тесты последовательно
```bash
#!/bin/bash
k6 run load_tests/k6_quick_test.js
k6 run load_tests/k6_recommendations_performance_test.js
k6 run load_tests/k6_full_user_scenario_test.js
```

### Запустить тесты параллельно (осторожно!)
```bash
#!/bin/bash
k6 run load_tests/k6_quick_test.js &
k6 run load_tests/k6_recommendations_performance_test.js &
wait
```

---

## 🌐 Удаленное тестирование

### Через k6 Cloud
```bash
# 1. Залогиньтесь
k6 login cloud

# 2. Запустите тест в облаке
k6 cloud load_tests/k6_full_user_scenario_test.js
```

### Distributed тестирование
```bash
# На master ноде
k6 run --out json=master_results.json load_tests/k6_quick_test.js

# На worker нодах
k6 run --vus 100 --duration 5m load_tests/k6_quick_test.js
```

---

## 💡 Полезные комбинации

### Быстрый тест с логами
```bash
k6 run --verbose --http-debug load_tests/k6_quick_test.js 2>&1 | tee test.log
```

### Тест с ограничением по времени и VU
```bash
k6 run --vus 30 --duration 3m --out json=results.json load_tests/k6_quick_test.js
```

### Тест с разными этапами
```bash
k6 run \
  --stage 1m:10 \
  --stage 2m:30 \
  --stage 1m:50 \
  --stage 2m:30 \
  --stage 1m:0 \
  load_tests/k6_quick_test.js
```

### Тест с установкой лимитов
```bash
k6 run \
  --max-redirects 10 \
  --batch 20 \
  --batch-per-host 10 \
  load_tests/k6_quick_test.js
```

---

## 🔍 Анализ результатов

### Просмотр JSON результатов
```bash
cat summary_full_scenario.json | jq '.metrics'
```

### Фильтрация метрик
```bash
cat summary_full_scenario.json | jq '.metrics | 
  to_entries | 
  map(select(.key | startswith("http_req"))) | 
  from_entries'
```

### Экспорт в Excel-friendly формат
```bash
k6 run --out csv=results.csv load_tests/k6_quick_test.js
# Откройте results.csv в Excel
```

---

## 🎓 Примеры для разных целей

### Тест для CI/CD (быстрый)
```bash
k6 run --vus 5 --duration 30s --quiet load_tests/k6_quick_test.js
if [ $? -eq 0 ]; then
  echo "Tests passed"
  exit 0
else
  echo "Tests failed"
  exit 1
fi
```

### Ночной регрессионный тест
```bash
k6 run --vus 50 --duration 8h load_tests/k6_full_user_scenario_test.js
```

### Pre-production тест
```bash
k6 run \
  --env API_URL=https://staging.example.com \
  --vus 100 \
  --duration 30m \
  load_tests/k6_full_user_scenario_test.js
```

---

## 📝 Заметки

1. **Всегда начинайте с быстрого теста** (`k6_quick_test.js`)
2. **Проверьте доступность API** перед запуском длительных тестов
3. **Используйте `--env API_URL`** для указания правильного адреса
4. **Мониторьте ресурсы системы** во время тестов (CPU, RAM, Network)
5. **Анализируйте результаты** в HTML отчетах

---

## 🆘 Помощь

### Справка k6
```bash
k6 --help
k6 run --help
```

### Документация
- [k6.io/docs](https://k6.io/docs/)
- [k6.io/docs/using-k6/scenarios/](https://k6.io/docs/using-k6/scenarios/)
- [k6.io/docs/using-k6/metrics/](https://k6.io/docs/using-k6/metrics/)

