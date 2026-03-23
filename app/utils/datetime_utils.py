from datetime import datetime

CLICKHOUSE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def format_datetime_ch(value: datetime) -> str:
    """Форматировать datetime в строку, совместимую с ClickHouse DateTime."""
    return value.strftime(CLICKHOUSE_DATETIME_FORMAT)
