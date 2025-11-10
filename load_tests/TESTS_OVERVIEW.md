# 📊 Обзор k6 тестов - Music Recommendation System

Краткий справочник по всем нагрузочным тестам системы.

---

## 🗂️ Структура файлов

```
load_tests/
├── 📄 k6-helpers.js                  # Общие функции (helpers)
├── 🔍 k6_diagnostics_test.js         # Диагностический тест (НАЧАТЬ С НЕГО!)
├── ⚡ quick_test.js                  # Быстрая проверка (30s)
├── 🔥 k6_smoke_test.js               # Smoke test (2min)
├── 📊 k6_basic_load_test.js          # Основной нагрузочный тест (15min)
├── ⚡ k6_spike_test.js               # Spike test - 50 VUs (2min)
├── 💥 k6_spike_test_extreme.js      # Extreme spike - 500 VUs (без thresholds)
├── 💪 k6_stress_test.js              # Стресс-тест (30min)
├── 🕐 k6_soak_test.js                # Soak test (70min)
├── 🐍 generate_test_data.py          # Генерация 1M записей
├── 📖 README.md                      # Основная документация
├── 📖 QUICKSTART.md                  # Быстрый старт
├── 📖 DIAGNOSTICS_GUIDE.md           # Руководство по диагностике
└── 📖 TESTS_OVERVIEW.md              # Этот файл
```

---

## 🎯 Быстрый выбор теста

### Что вы хотите сделать?

| Цель | Тест | Команда |
|------|------|---------|
| 🔍 **Найти узкие места** | Diagnostics | `make load-test-diagnostics` |
| ⚡ **Быстро проверить API** | Quick | `make load-test-quick` |
| 🔥 **Готов ли к тестам?** | Smoke | `make load-test-smoke` |
| 📊 **Реальная нагрузка** | Basic Load | `make load-test-basic` |
| ⚡ **Устойчивость к пикам** | Spike | `make load-test-spike` |
| 💪 **Найти предел** | Stress | `make load-test-stress` |
| 🕐 **Утечки памяти?** | Soak | `make load-test-soak` |

---

## 📋 Детали по каждому тесту

### 1. 🔍 Diagnostics Test

**Файл:** `k6_diagnostics_test.js`

**Когда использовать:**
- ✅ Первый запуск после изменений
- ✅ При проблемах с производительностью
- ✅ Для выявления узких мест
- ✅ Перед полноценными тестами

**Характеристики:**
- VUs: 10
- Длительность: 1 минута
- Thresholds: НЕТ (всегда PASSED)
- Выход: Детальная статистика + рекомендации

**Команды:**
```bash
make load-test-diagnostics
k6 run load_tests/k6_diagnostics_test.js
```

**Что показывает:**
- Время ответа каждого endpoint
- Ошибки по endpoint
- Работает ли кэш Redis
- Рекомендации по оптимизации

---

### 2. ⚡ Quick Test

**Файл:** `quick_test.js`

**Когда использовать:**
- ✅ Перед коммитом кода
- ✅ Быстрая проверка после deploy
- ✅ CI/CD pipeline

**Характеристики:**
- VUs: 5
- Длительность: 30 секунд
- Thresholds: p95 < 3s, errors < 10%

**Команды:**
```bash
make load-test-quick
k6 run load_tests/quick_test.js
```

---

### 3. 🔥 Smoke Test

**Файл:** `k6_smoke_test.js`

**Когда использовать:**
- ✅ Перед pull request
- ✅ Перед запуском полноценных тестов
- ✅ После deploy в staging

**Характеристики:**
- VUs: 2
- Длительность: 2 минуты
- Thresholds: p95 < 5s, errors < 10%

**Команды:**
```bash
make load-test-smoke
k6 run load_tests/k6_smoke_test.js
```

**Что проверяет:**
- Health check
- Users API (list, by id)
- Tracks API (list, by id)
- Recommendations API

---

### 4. 📊 Basic Load Test

**Файл:** `k6_basic_load_test.js`

**Когда использовать:**
- ✅ Основной тест производительности
- ✅ Перед релизом
- ✅ Регулярное тестирование

**Характеристики:**
- VUs: 50 → 200 (постепенно)
- Длительность: 15 минут
- Thresholds: p95 < 10s, errors < 15%

**Команды:**
```bash
make load-test-basic
k6 run load_tests/k6_basic_load_test.js
```

**Профиль нагрузки:**
```
0-1m:   50 VUs  (разогрев)
1-4m:  100 VUs  (рост)
4-9m:  100 VUs  (стабильная)
9-11m: 200 VUs  (пик)
11-14m: 50 VUs  (снижение)
14-15m:  0 VUs  (завершение)
```

---

### 5. ⚡ Spike Test

**Файл:** `k6_spike_test.js`

**Когда использовать:**
- ✅ Проверка на внезапные пики (акции, события)
- ✅ Black Friday / Cyber Monday
- ✅ Запуск новой функции

**Характеристики:**
- VUs: 4 → 50 → 4 (резкий скачок)
- Длительность: 2 минуты
- Thresholds: p95 < 15s, errors < 30%

**Команды:**
```bash
make load-test-spike           # Стандартный (50 VUs)
make load-test-spike-extreme   # Экстремальный (500 VUs, без thresholds)
```

**Профиль нагрузки:**
```
0-10s:   4 VUs   (базовая)
10-30s: 50 VUs   (РЕЗКИЙ РОСТ!)
30-60s: 50 VUs   (удержание пика)
60-70s: 10 VUs   (снижение)
70-80s:  0 VUs   (завершение)
```

---

### 6. 💪 Stress Test

**Файл:** `k6_stress_test.js`

**Когда использовать:**
- ✅ Поиск точки отказа системы
- ✅ Планирование масштабирования
- ✅ Определение максимальной пропускной способности

**Характеристики:**
- VUs: 50 → 500 (постепенно)
- Длительность: 30 минут
- Thresholds: p95 < 10s, errors < 20%

**Команды:**
```bash
make load-test-stress
k6 run load_tests/k6_stress_test.js
```

**Профиль нагрузки:**
```
0-2m:   50 VUs
2-7m:  100 VUs
7-12m: 200 VUs
12-17m: 300 VUs
17-22m: 400 VUs
22-27m: 500 VUs  (МАКСИМУМ!)
27-29m:  0 VUs
```

---

### 7. 🕐 Soak Test

**Файл:** `k6_soak_test.js`

**Когда использовать:**
- ✅ Поиск утечек памяти
- ✅ Проверка деградации производительности
- ✅ Перед production deploy
- ✅ Запускать на ночь

**Характеристики:**
- VUs: 50 (стабильно)
- Длительность: 70 минут (1 час)
- Thresholds: p95 < 2s, errors < 5%

**Команды:**
```bash
make load-test-soak
k6 run load_tests/k6_soak_test.js
```

**Профиль нагрузки:**
```
0-5m:   50 VUs  (разогрев)
5-65m:  50 VUs  (1 час стабильной нагрузки)
65-70m:  0 VUs  (завершение)
```

**Что искать:**
- Растущее время ответа (деградация)
- Увеличение использования памяти
- Увеличение процента ошибок

---

## 🛠️ k6-helpers.js - Общие функции

**Назначение:** Устранение дублирования кода во всех тестах

**Что содержит:**

### Константы
- `BASE_URL` - базовый URL API
- `USER_ID_MIN/MAX` - диапазоны ID пользователей
- `TRACK_ID_MIN/MAX` - диапазоны ID треков

### Helper функции
- `getRandomUserId()` - случайный ID пользователя
- `getRandomTrackId()` - случайный ID трека
- `getRandomOffset()` - случайный offset для пагинации
- `randomInt(min, max)` - случайное число

### Форматирование
- `formatMs(ms)` - форматирует миллисекунды
- `formatPercent(rate)` - форматирует проценты
- `formatDuration(ms)` - форматирует длительность

### Статистика
- `getBasicStats(data)` - извлекает базовую статистику из результатов k6
- `printHeader(title)` - печатает красивую шапку
- `printBasicStats(stats)` - печатает базовую статистику
- `evaluateResults(stats, thresholds)` - оценивает результаты

**Использование в тестах:**
```javascript
import { 
  BASE_URL,
  getRandomUserId,
  getBasicStats,
  printHeader,
  formatPercent 
} from './k6-helpers.js';
```

---

## 📊 Рекомендуемая последовательность запуска

### 🎯 При первом запуске

```bash
# 1. Генерируем данные (один раз)
make load-test-data-generate  # ~5-10 минут

# 2. Диагностика
make load-test-diagnostics    # 1 минута

# 3. Smoke test
make load-test-smoke          # 2 минуты

# 4. Basic load test
make load-test-basic          # 15 минут
```

### 🎯 При разработке

```bash
# После каждого изменения кода
make load-test-quick          # 30 секунд

# Перед commit
make load-test-smoke          # 2 минуты

# Если есть проблемы
make load-test-diagnostics    # 1 минута
```

### 🎯 Перед релизом

```bash
# Полное тестирование
make load-test-diagnostics    # 1 минута - диагностика
make load-test-smoke          # 2 минуты - smoke
make load-test-basic          # 15 минут - основной тест
make load-test-spike          # 2 минуты - пики
make load-test-stress         # 30 минут - пределы

# Запустить на ночь
make load-test-soak           # 70 минут - выносливость
```

---

## 🎓 Best Practices

### ✅ DO (Делайте)

1. **Всегда начинайте с диагностики**
   ```bash
   make load-test-diagnostics
   ```

2. **Запускайте тесты по порядку**
   - Quick → Smoke → Basic → Spike → Stress → Soak

3. **Проверяйте логи при ошибках**
   ```bash
   make logs-errors
   ```

4. **Сохраняйте результаты**
   - k6 автоматически сохраняет в `results/*.json`

5. **Запускайте soak test на ночь**
   - Длится ~1 час
   - Требует стабильной системы

### ❌ DON'T (Не делайте)

1. ❌ Не запускайте stress test без подготовки
2. ❌ Не запускайте несколько тестов одновременно
3. ❌ Не игнорируйте warnings в диагностике
4. ❌ Не запускайте на production без smoke теста
5. ❌ Не увеличивайте нагрузку если система уже падает

---

## 🆘 Troubleshooting

### Проблема: Все тесты падают

```bash
# Полная перезагрузка
make down && make up && make db-init
sleep 30
make load-test-data-generate
make load-test-diagnostics
```

### Проблема: Конкретный тест падает

```bash
# 1. Запустите диагностику
make load-test-diagnostics

# 2. Проверьте логи
make logs-errors

# 3. Проверьте данные
make db-stats
```

### Проблема: Медленная производительность

См. детальное руководство: [DIAGNOSTICS_GUIDE.md](DIAGNOSTICS_GUIDE.md)

---

## 📚 Дополнительные ресурсы

- [README.md](README.md) - Основная документация
- [QUICKSTART.md](QUICKSTART.md) - Быстрый старт
- [DIAGNOSTICS_GUIDE.md](DIAGNOSTICS_GUIDE.md) - Диагностика и оптимизация
- [k6 Documentation](https://k6.io/docs/)
- [k6 Test Types](https://k6.io/docs/test-types/introduction/)

---

**Создано для:** Music Recommendation System  
**Версия:** 1.0.0  
**Последнее обновление:** 2025-11-10

