# 🔍 Быстрая справка: Проверка индексов в ClickHouse

## ❌ Частая ошибка

```
Code: 60. DB::Exception: Unknown table expression identifier 'sys'
```

**Причина:** Использовано `sys` вместо `system`

**Неправильно:**
```sql
FROM sys.data_skipping_indices  -- ❌ Ошибка!
```

**Правильно:**
```sql
FROM system.data_skipping_indices  -- ✅ Правильно
```

## ✅ Правильные команды для проверки индексов

### Через Makefile (рекомендуется)
```bash
make db-indexes  # Добавить индексы
```

### Вручную через Docker
```bash
docker exec music_recommend_clickhouse clickhouse-client --query "
    SELECT 
        table,
        name as index_name,
        type,
        expr as index_expression,
        granularity
    FROM system.data_skipping_indices
    WHERE database = 'music_recommend'
    ORDER BY table, name
"
```

### Проверка конкретного индекса
```bash
docker exec music_recommend_clickhouse clickhouse-client --query "
    SELECT count() > 0
    FROM system.data_skipping_indices
    WHERE database = 'music_recommend'
      AND table = 'user_track_matrix'
      AND name = 'idx_implicit_rating'
"
```

## 📝 Важно

- ✅ Используйте `system` (не `sys`)
- ✅ Все системные таблицы в ClickHouse находятся в схеме `system`
- ✅ Скрипт `scripts/safe_add_indexes.sh` автоматически использует правильный синтаксис

