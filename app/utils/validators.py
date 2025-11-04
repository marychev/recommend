"""
Утилиты для валидации данных
"""

from app.db.clickhouse import ClickHouseClient


def check_user_exists(clickhouse: ClickHouseClient, user_id: int) -> bool:
    result = clickhouse.execute(
        "SELECT count() FROM users WHERE user_id = {user_id:UInt32}",
        parameters={"user_id": user_id},
    )
    return result.result_rows[0][0] > 0


def check_track_exists(clickhouse: ClickHouseClient, track_id: int) -> bool:
    result = clickhouse.execute(
        "SELECT count() FROM tracks WHERE track_id = {track_id:UInt32}",
        parameters={"track_id": track_id},
    )
    return result.result_rows[0][0] > 0


def get_next_id(clickhouse: ClickHouseClient, table: str) -> int:
    result = clickhouse.execute(
        f"SELECT max({table[:-1]}_id) as max_id FROM {table}"
    )
    max_id = result.result_rows[0][0] if result.result_rows else 0
    return (max_id or 0) + 1
