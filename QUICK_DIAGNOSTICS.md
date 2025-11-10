# 🚨 Быстрая диагностика проблемы (75% ошибок в smoke test)

## 📊 Симптомы из вашего smoke теста:

```
• Процент ошибок:        75.00%    ❌ КРИТИЧНО!
• Успешные проверки:     33.33%    ❌ ОЧЕНЬ МАЛО!
• Среднее время:         5.44ms    ⚠️ Слишком быстро (запросы падают сразу)
```

**Это означает:** API отвечает, но большинство запросов падают с ошибками.

---

## 🔍 Пошаговая диагностика (выполните по порядку!)

### Шаг 1: Проверьте, что все сервисы запущены

```bash
docker-compose ps
```

**Должны быть запущены:**
```
✅ music_recommend_api         Up
✅ music_recommend_clickhouse  Up
✅ music_recommend_redis       Up
✅ music_recommend_kafka       Up
✅ music_recommend_zookeeper   Up
```

**Если НЕ запущены:**
```bash
make restart
sleep 30
```

---

### Шаг 2: Проверьте логи API на ошибки

```bash
# Последние ошибки
docker-compose logs api --tail=50 | grep ERROR

# Или через make
make logs-errors
```

**Частые ошибки:**

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `ClickHouse client not connected` | БД недоступна | `make restart` |
| `Code: 60. DB::Exception: Table doesn't exist` | Таблицы не созданы | `make db-init` |
| `Code: 241` | Превышен лимит памяти | См. TROUBLESHOOTING_RECOMMENDATIONS.md |
| `Redis connection failed` | Redis недоступен | `docker-compose restart redis` |

---

### Шаг 3: Проверьте таблицы в БД

```bash
# Проверьте, что таблицы созданы
make db-tables
```

**Должны быть:**
```
✅ users
✅ tracks
✅ user_track_interactions
✅ user_track_matrix
```

**Если таблиц НЕТ:**
```bash
make db-init
sleep 10
```

---

### Шаг 4: Проверьте данные в БД

```bash
make db-stats
```

**Должно быть:**
```
users:                100000+
tracks:               50000+
interactions:         850000+
```

**Если данных НЕТ:**
```bash
make load-test-data-generate
# Это займет ~5-10 минут
```

---

### Шаг 5: Проверьте API вручную

```bash
# Root endpoint
curl http://localhost:8000/

# Health check
curl http://localhost:8000/api/v1/health

# Users list
curl http://localhost:8000/api/v1/users?limit=10

# Tracks list
curl http://localhost:8000/api/v1/tracks?limit=10
```

**Если возвращает ошибки 500:**
- Проверьте логи (Шаг 2)
- Проверьте таблицы (Шаг 3)
- Проверьте данные (Шаг 4)

---

## 🛠️ Типичные решения

### Решение 1: Полный рестарт (самое частое)

```bash
# 1. Остановите все
make down

# 2. Запустите заново
make up

# 3. Подождите 30 секунд
sleep 30

# 4. Создайте таблицы
make db-init

# 5. Проверьте
curl http://localhost:8000/api/v1/health

# 6. Запустите smoke test
make load-test-smoke
```

---

### Решение 2: Если данных нет

```bash
# 1. Проверьте данные
make db-stats

# 2. Если пусто - сгенерируйте
make load-test-data-generate

# 3. Подождите завершения (~5 минут)

# 4. Проверьте снова
make db-stats

# 5. Запустите smoke test
make load-test-smoke
```

---

### Решение 3: Проблема с ClickHouse памятью

Если видите `Code: 241`:

```bash
# Увеличьте память Docker в Docker Desktop:
# Settings → Resources → Memory: 8GB → 12-16GB

# Перезапустите Docker Desktop

# Перезапустите сервисы
make restart
```

См. детали: **load_tests/TROUBLESHOOTING_RECOMMENDATIONS.md**

---

## ⚡ Быстрая проверка готовности

После исправления проблем:

```bash
# 1. Базовая диагностика
make diagnose

# 2. Диагностический тест (1 минута)
make load-test-diagnostics

# 3. Smoke test (2 минуты)
make load-test-smoke
```

**Smoke test должен показать:**
```
✅ PASSED: API работает нормально!
• Процент ошибок:        < 10%
• Успешные проверки:     > 90%
```

---

## 📋 Чек-лист проверки

- [ ] Все контейнеры запущены (`docker-compose ps`)
- [ ] API доступен (`curl http://localhost:8000/`)
- [ ] ClickHouse подключен (`make db-tables`)
- [ ] Таблицы созданы (users, tracks, interactions)
- [ ] Данные сгенерированы (`make db-stats` показывает 1M+ записей)
- [ ] Нет ошибок в логах (`make logs-errors`)
- [ ] Smoke test проходит (`make load-test-smoke`)

---

## 💡 Рекомендуемый порядок действий СЕЙЧАС

Выполните эти команды по порядку в WSL терминале:

```bash
# 1. Полная диагностика
make diagnose

# 2. Если есть проблемы - рестарт
make restart
sleep 30

# 3. Проверьте таблицы
make db-tables

# 4. Если таблиц нет - создайте
make db-init

# 5. Проверьте данные
make db-stats

# 6. Если данных нет - сгенерируйте
# make load-test-data-generate  # Это займет ~5 минут!

# 7. Запустите диагностику
make load-test-diagnostics

# 8. Запустите smoke test
make load-test-smoke
```

---

## 📞 Получить помощь

Если проблема не решается:

1. Соберите диагностику:
```bash
make diagnose > diagnosis.txt
make logs-errors > errors.txt
make db-stats > db_stats.txt
```

2. Проверьте:
- **load_tests/DIAGNOSTICS_GUIDE.md** - полное руководство
- **load_tests/TROUBLESHOOTING_RECOMMENDATIONS.md** - проблемы с рекомендациями
- **tests/ASYNC_REVIEW.md** - проблемы с тестами

---

**Создано:** 2025-11-10  
**Цель:** Решить проблему 75% ошибок в smoke test  
**Статус:** Требуется диагностика системы

