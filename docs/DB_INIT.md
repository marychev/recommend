# 📊 Инициализация базы данных

## Проблема

При повторном запуске `make db-init` или `make quickstart` возникала ошибка:
```
Code: 44. DB::Exception: Cannot add index idx_track_id: index with this name already exists
```

**Причина**: В ClickHouse команда `ALTER TABLE ADD INDEX` не поддерживает `IF NOT EXISTS`, поэтому при повторном выполнении SQL скрипта возникала ошибка.

## Решение

Создан **идемпотентный** скрипт `scripts/safe_db_init.sh`, который:

1. ✅ Создает таблицы с `IF NOT EXISTS` (безопасно)
2. ✅ Проверяет существование индексов перед добавлением
3. ✅ Создает материализованные представления с `IF NOT EXISTS`
4. ✅ Можно запускать многократно без ошибок

## Использование

### Безопасная инициализация (рекомендуется)

```bash
# Через Makefile
make db-init

# Или напрямую
bash scripts/safe_db_init.sh
```

### Полный сброс БД (удаляет все данные!)

```bash
# Пересоздать контейнер и таблицы
make db-reset

# Или напрямую
bash scripts/docker-reset-clickhouse.sh
```

## Что делает safe_db_init.sh

1. **Проверяет** что контейнер ClickHouse запущен
2. **Создает** базу данных `music_recommend` (если нет)
3. **Создает таблицы** (если нет):
   - `users` - пользователи
   - `tracks` - треки
   - `user_track_interactions` - взаимодействия
   - `user_recommendations` - рекомендации
   - `user_track_matrix` - матрица для collaborative filtering

4. **Создает материализованные представления** (если нет):
   - `track_statistics_mv` - статистика треков
   - `user_statistics_mv` - статистика пользователей
   - `user_track_matrix_mv` - автообновление матрицы

5. **Проверяет и добавляет индексы** (только если их нет):
   - `idx_track_id` - индекс по track_id
   - `idx_action_type` - индекс по типу действия

6. **Создает представления** (views):
   - `popular_tracks` - популярные треки
   - `similar_users` - похожие пользователи

## Проверка результата

```bash
# Список таблиц
make db-tables

# Статистика по таблицам
make db-stats

# Подключиться к БД
make db-shell
```

## Troubleshooting

### Ошибка: "Container not running"

```bash
# Запустите ClickHouse
make up-clickhouse

# Подождите 10-15 секунд
sleep 15

# Попробуйте снова
make db-init
```

### Проверка индексов

```sql
-- В clickhouse-client
SELECT 
    table, 
    name, 
    type, 
    expr 
FROM system.data_skipping_indices 
WHERE database = 'music_recommend';
```

### Проверка материализованных представлений

```sql
-- В clickhouse-client
SELECT 
    name, 
    engine,
    create_table_query
FROM system.tables
WHERE database = 'music_recommend' 
  AND engine LIKE '%MaterializedView%';
```

## Преимущества нового подхода

| Старый способ | Новый способ |
|---------------|--------------|
| ❌ Ошибка при повторном запуске | ✅ Безопасно запускать многократно |
| ❌ Прерывание при существующих индексах | ✅ Проверка перед добавлением |
| ❌ Нужно вручную очищать БД | ✅ Идемпотентность |
| ⚠️ Сложно диагностировать | ✅ Понятный вывод с эмодзи |

## Связанные команды Makefile

```bash
make db-init         # Инициализация БД (идемпотентно)
make db-reset        # Полный сброс БД
make db-shell        # Открыть clickhouse-client
make db-tables       # Показать таблицы
make db-stats        # Статистика таблиц
make quickstart      # Запуск всего проекта
```

## См. также

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Решение проблем
- [PORTS.md](PORTS.md) - Информация о портах
- [RUN_TESTS.md](RUN_TESTS.md) - Запуск тестов

