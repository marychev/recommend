# 📊 Руководство по сохранению и просмотру результатов тестов

Автоматическое сохранение результатов для pytest и k6 тестов с timestamp.

---

## 🧪 Pytest тесты

### Где сохраняются

```
tests/results/
├── junit_20251110_143025.xml      # JUnit XML (для CI/CD)
├── report_20251110_143025.html    # HTML отчет (красивый)
└── output_20251110_143025.log     # Консольный вывод
```

### Как запустить

```bash
# Все тесты (результаты автоматически сохраняются)
make test

# Только ClickHouse тесты
make test-clickhouse

# Только Kafka тесты
make test-kafka
```

### Просмотр результатов

```bash
# Показать последние результаты
make test-results

# Откроет HTML отчет (последний)
open tests/results/report_*.html    # macOS
xdg-open tests/results/report_*.html    # Linux
start tests/results/report_*.html   # Windows
```

### Форматы результатов

| Файл | Формат | Назначение |
|------|--------|------------|
| `junit_*.xml` | JUnit XML | CI/CD интеграция |
| `report_*.html` | HTML | Красивый отчет для человека |
| `output_*.log` | Text | Полный вывод консоли |

---

## ⚡ k6 нагрузочные тесты

### Где сохраняются

```
load_tests/results/
├── diagnostics_20251110_143525.json    # JSON метрики
├── diagnostics_20251110_143525.log     # Консольный вывод
├── quick_20251110_143600.json
├── quick_20251110_143600.log
├── smoke_20251110_143700.json
├── smoke_20251110_143700.log
├── basic_load_20251110_144000.json
├── basic_load_20251110_144000.log
└── ...
```

### Как запустить

```bash
# Диагностика (1 минута)
make load-test-diagnostics

# Quick test (30 секунд)
make load-test-quick

# Smoke test (2 минуты)
make load-test-smoke

# Базовый тест (15 минут)
make load-test-basic

# Spike test (2 минуты)
make load-test-spike

# Stress test (30 минут)
make load-test-stress

# Soak test (70 минут)
make load-test-soak
```

### Просмотр результатов

```bash
# Показать последние результаты
make load-test-results

# Анализ JSON результатов
cat load_tests/results/diagnostics_*.json | jq '.metrics'

# Просмотр логов
tail -100 load_tests/results/diagnostics_*.log
```

### Форматы результатов

| Файл | Формат | Назначение |
|------|--------|------------|
| `*_*.json` | JSON | Детальные метрики k6 |
| `*_*.log` | Text | Консольный вывод с summary |

---

## 📁 Структура директорий

```
project/
├── tests/
│   ├── results/           # Результаты pytest
│   │   ├── .gitkeep
│   │   ├── junit_*.xml
│   │   ├── report_*.html       # Откройте в браузере!
│   │   └── output_*.log
│   ├── clickhouse/
│   ├── kafka/
│   └── ...
│
└── load_tests/
    └── results/            # Результаты k6
        ├── .gitkeep
        ├── diagnostics_*.json
        ├── diagnostics_*.log
        ├── smoke_*.json
        ├── smoke_*.log
        └── ...
```

---

## 🔍 Анализ результатов

### Pytest HTML отчет

Откройте `tests/results/report_*.html` в браузере:

```bash
# macOS
open tests/results/report_20251110_143025.html

# Linux
xdg-open tests/results/report_20251110_143025.html

# Windows
start tests/results/report_20251110_143025.html
```

**Содержит:**
- ✅ Пройденные тесты
- ❌ Упавшие тесты
- ⚠️ Пропущенные тесты
- ⏱️ Время выполнения
- 📋 Полный traceback ошибок

### k6 JSON результаты

```bash
# Основные метрики
cat load_tests/results/smoke_20251110_143700.json | jq '.metrics | keys'

# HTTP метрики
cat load_tests/results/smoke_20251110_143700.json | jq '.metrics.http_req_duration'

# Количество запросов
cat load_tests/results/smoke_20251110_143700.json | jq '.metrics.http_reqs.values.count'

# Процент ошибок
cat load_tests/results/smoke_20251110_143700.json | jq '.metrics.http_req_failed.values.rate'
```

### k6 Log результаты

```bash
# Просмотр summary
tail -50 load_tests/results/smoke_20251110_143700.log

# Поиск ошибок
grep -i "error\|failed" load_tests/results/smoke_20251110_143700.log

# Время выполнения
grep "execution:" load_tests/results/smoke_20251110_143700.log
```

---

## 📊 Сравнение результатов

### Pytest - сравнить два запуска

```bash
# Показать различия в покрытии
diff test_results/output_20251110_143025.log \
     test_results/output_20251110_150000.log
```

### k6 - сравнить производительность

```bash
# Сравнить p95 latency
echo "Test 1:"
cat load_tests/results/smoke_20251110_143700.json | jq '.metrics.http_req_duration.values["p(95)"]'

echo "Test 2:"
cat load_tests/results/smoke_20251110_150000.json | jq '.metrics.http_req_duration.values["p(95)"]'
```

---

## 🧹 Очистка старых результатов

```bash
# Удалить результаты старше 7 дней
find tests/results/ -type f -mtime +7 -delete
find load_tests/results/ -type f -mtime +7 -delete

# Удалить все результаты pytest
rm -rf tests/results/*.{xml,html,log}

# Удалить все результаты k6
rm -rf load_tests/results/*.{json,log}

# Оставить только последние 10
ls -t tests/results/*.html | tail -n +11 | xargs rm -f
ls -t load_tests/results/*.json | tail -n +11 | xargs rm -f
```

---

## 🔧 Интеграция с CI/CD

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run pytest
        run: make test
      
      - name: Upload pytest results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: pytest-results
          path: |
            tests/results/*.html
            tests/results/*.xml
      
      - name: Run k6 smoke test
        run: make load-test-smoke
      
      - name: Upload k6 results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: k6-results
          path: load_tests/results/*.json
```

### GitLab CI

```yaml
test:
  stage: test
  script:
    - make test
  artifacts:
    when: always
    paths:
      - tests/results/
    reports:
      junit: tests/results/junit_*.xml

load-test:
  stage: test
  script:
    - make load-test-smoke
  artifacts:
    when: always
    paths:
      - load_tests/results/
```

---

## 💡 Полезные команды

```bash
# Pytest
make test                    # Запустить + сохранить результаты
make test-results            # Показать последние результаты
make test-clickhouse         # Только ClickHouse тесты
make test-kafka              # Только Kafka тесты

# k6
make load-test-diagnostics   # Диагностика + сохранить
make load-test-smoke         # Smoke test + сохранить
make load-test-basic         # Basic test + сохранить
make load-test-results       # Показать последние результаты

# Просмотр
open tests/results/report_*.html              # Pytest HTML
cat load_tests/results/smoke_*.json | jq     # k6 JSON
tail -100 load_tests/results/smoke_*.log     # k6 log
```

---

## ✅ Чек-лист

### Перед коммитом

- [ ] Запустили `make test` - результаты в `test_results/`
- [ ] Проверили HTML отчет - все тесты прошли
- [ ] Запустили `make load-test-smoke` - система работает
- [ ] Проверили метрики - нет деградации

### Перед релизом

- [ ] Запустили `make test` - все OK
- [ ] Запустили `make load-test-diagnostics` - нет узких мест
- [ ] Запустили `make load-test-basic` - нормальная нагрузка OK
- [ ] Сохранили результаты для сравнения с будущими версиями

---

**Создано:** 2025-11-10  
**Версия:** 1.0  
**Проект:** Music Recommendation System

