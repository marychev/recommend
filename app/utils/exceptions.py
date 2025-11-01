"""
Общие обработчики исключений и утилиты
"""
from fastapi import HTTPException, status


def entity_not_found(entity_type: str, entity_id: int) -> HTTPException:
    """
    Генерирует HTTPException для случая когда сущность не найдена

    Args:
        entity_type: Тип сущности (user, track, etc.)
        entity_id: ID сущности

    Returns:
        HTTPException с кодом 404
    """
    entity_names = {
        "user": "Пользователь",
        "track": "Трек",
        "event": "Событие"
    }
    name = entity_names.get(entity_type, entity_type.capitalize())

    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{name} с ID {entity_id} не найден"
    )


def database_error(operation: str, error: Exception) -> HTTPException:
    """
    Генерирует HTTPException для ошибок базы данных

    Args:
        operation: Описание операции (создание пользователя, получение трека)
        error: Исходное исключение

    Returns:
        HTTPException с кодом 500
    """
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Ошибка при {operation}: {str(error)}"
    )


def validation_error(message: str) -> HTTPException:
    """
    Генерирует HTTPException для ошибок валидации

    Args:
        message: Сообщение об ошибке

    Returns:
        HTTPException с кодом 400
    """
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message
    )

