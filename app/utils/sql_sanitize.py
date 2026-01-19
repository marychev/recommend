"""
Утилиты для безопасного формирования SQL запросов к ClickHouse.

Защита от SQL Injection для строковых параметров.
"""

import re
from typing import Any, Optional


def escape_string(value: str) -> str:
    """
    Экранирование строки для безопасного использования в SQL запросах ClickHouse.
    
    Экранирует:
    - Одинарные кавычки (') → ''
    - Обратные слэши (\\) → \\\\
    - Null байты
    
    Args:
        value: Строка для экранирования
        
    Returns:
        Экранированная строка
        
    Example:
        >>> escape_string("O'Reilly")
        "O''Reilly"
        >>> escape_string("test\\path")
        "test\\\\path"
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Убираем null байты
    value = value.replace('\x00', '')
    
    # Экранируем обратные слэши
    value = value.replace('\\', '\\\\')
    
    # Экранируем одинарные кавычки (ClickHouse использует '' для экранирования)
    value = value.replace("'", "''")
    
    return value


def safe_string(value: Optional[str]) -> str:
    """
    Создает безопасную строку для SQL запроса с кавычками.
    
    Args:
        value: Строка (может быть None)
        
    Returns:
        Экранированная строка в одинарных кавычках или пустая строка
        
    Example:
        >>> safe_string("Rock")
        "'Rock'"
        >>> safe_string("O'Reilly")
        "'O''Reilly'"
        >>> safe_string(None)
        "''"
    """
    if value is None:
        return "''"
    return f"'{escape_string(value)}'"


def safe_int(value: Any, default: int = 0) -> int:
    """
    Безопасное преобразование в int.
    
    Args:
        value: Значение для преобразования
        default: Значение по умолчанию при ошибке
        
    Returns:
        int значение
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_identifier(value: str) -> str:
    """
    Валидация идентификатора (имя таблицы, колонки).
    
    Разрешает только буквы, цифры и подчеркивания.
    
    Args:
        value: Идентификатор
        
    Returns:
        Проверенный идентификатор
        
    Raises:
        ValueError: Если идентификатор содержит недопустимые символы
    """
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value):
        raise ValueError(f"Invalid SQL identifier: {value}")
    return value


def build_where_clause(conditions: dict[str, Any]) -> str:
    """
    Безопасное построение WHERE clause.
    
    Args:
        conditions: Словарь {column_name: value}
        
    Returns:
        WHERE clause или пустая строка
        
    Example:
        >>> build_where_clause({"genre": "Rock", "artist": "Queen"})
        "WHERE genre = 'Rock' AND artist = 'Queen'"
        >>> build_where_clause({})
        ""
    """
    if not conditions:
        return ""
    
    clauses = []
    for column, value in conditions.items():
        # Валидируем имя колонки
        safe_column = safe_identifier(column)
        
        if value is None:
            continue
        elif isinstance(value, bool):
            clauses.append(f"{safe_column} = {1 if value else 0}")
        elif isinstance(value, (int, float)):
            clauses.append(f"{safe_column} = {value}")
        elif isinstance(value, str):
            clauses.append(f"{safe_column} = {safe_string(value)}")
        elif isinstance(value, (list, tuple)):
            # IN clause
            if all(isinstance(v, (int, float)) for v in value):
                values_str = ",".join(str(v) for v in value)
            else:
                values_str = ",".join(safe_string(str(v)) for v in value)
            clauses.append(f"{safe_column} IN ({values_str})")
    
    if not clauses:
        return ""
    
    return "WHERE " + " AND ".join(clauses)
