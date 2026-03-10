"""
Утилиты для валидации данных

Проверки существования сущностей реализованы в:
- app/services/cache.py — exists_entity_cached() (с Redis-кэшированием)
- app/db/clickhouse.py — exists_user(), exists_track() (прямой запрос)

Генерация ID:
- app/utils/id_generator.py — get_next_id() (атомарный через Redis INCR)
"""
