from fastapi import HTTPException, status


def entity_not_found(entity_type: str, entity_id: int) -> HTTPException:
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
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Ошибка при {operation}: {str(error)}"
    )


def validation_error(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message
    )

