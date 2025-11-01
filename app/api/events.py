"""
API эндпоинты для работы с событиями
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, BackgroundTasks

from app.models.schemas import UserTrackInteraction, UserTrackInteractionCreate
from app.db.clickhouse import get_clickhouse_client

router = APIRouter()


async def process_event_async(event: UserTrackInteraction):
    """
    TODO: Отправка события в Kafka для дальнейшей обработки
    """
    # Здесь будет отправка в Kafka
    print(f"📨 Событие отправлено в Kafka: user={event.user_id}, track={event.track_id}, action={event.action_type}")


@router.post(
    "/events",
    response_model=UserTrackInteraction,
    status_code=status.HTTP_201_CREATED,
    summary="Отправить событие",
    description="Принимает событие взаимодействия пользователя с треком"
)
async def create_event(
    event: UserTrackInteractionCreate,
    background_tasks: BackgroundTasks
):
    """
    Создание события взаимодействия пользователя с треком
    События обрабатываются асинхронно через Kafka и сохраняются в ClickHouse.
    
    Пример запроса:
    ```json
    {
        "user_id": 1001,
        "track_id": 12345,
        "action_type": "play",
        "listen_duration_seconds": 180
    }
    ```
    
    Типы действий:
    - `play` - Прослушивание трека
    - `like` - Лайк трека
    - `dislike` - Дизлайк трека
    - `skip` - Пропуск трека
    - `add_to_playlist` - Добавление в плейлист
    - `share` - Поделиться треком
    """
    clickhouse = get_clickhouse_client()
    
    try:
        # Проверяем существование пользователя
        user_check = await clickhouse.execute_raw(
            "SELECT count() FROM users WHERE user_id = {user_id:UInt32}",
            parameters={"user_id": event.user_id}
        )
        if user_check[0][0] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользователь с ID {event.user_id} не найден"
            )
        
        # Проверяем существование трека
        track_check = await clickhouse.execute_raw(
            "SELECT count() FROM tracks WHERE track_id = {track_id:UInt32}",
            parameters={"track_id": event.track_id}
        )
        if track_check[0][0] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Трек с ID {event.track_id} не найден"
            )
        
        # Устанавливаем timestamp если не указан
        timestamp = event.timestamp if event.timestamp else datetime.now()
        
        # Сохраняем событие в ClickHouse
        await clickhouse.insert(
            "user_track_interactions",
            [[
                event.user_id,
                event.track_id,
                event.action_type.value,
                event.listen_duration_seconds,
                timestamp
            ]],
            column_names=["user_id", "track_id", "action_type", "listen_duration_seconds", "timestamp"]
        )
        
        interaction = UserTrackInteraction(
            user_id=event.user_id,
            track_id=event.track_id,
            action_type=event.action_type,
            listen_duration_seconds=event.listen_duration_seconds,
            timestamp=timestamp
        )
        
        # Добавляем задачу в фон для отправки в Kafka
        background_tasks.add_task(process_event_async, interaction)
        return interaction
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании события: {str(e)}"
        )


@router.get(
    "/events/user/{user_id}",
    response_model=List[UserTrackInteraction],
    summary="История событий пользователя",
    description="Возвращает историю взаимодействий пользователя с треками"
)
async def get_user_events(
    user_id: int,
    limit: int = 100,
    offset: int = 0
):
    """
    Получение истории событий для конкретного пользователя
    """
    clickhouse = get_clickhouse_client()
    
    try:
        # Проверяем существование пользователя
        user_check = await clickhouse.execute_raw(
            "SELECT count() FROM users WHERE user_id = {user_id:UInt32}",
            parameters={"user_id": user_id}
        )
        if user_check[0][0] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользователь с ID {user_id} не найден"
            )
        
        result = await clickhouse.execute_raw(
            f"""
            SELECT user_id, track_id, action_type, listen_duration_seconds, timestamp
            FROM user_track_interactions
            WHERE user_id = {{user_id:UInt32}}
            ORDER BY timestamp DESC
            LIMIT {limit} OFFSET {offset}
            """,
            parameters={"user_id": user_id}
        )
        
        events = []
        for row in result:
            events.append(UserTrackInteraction(
                user_id=row[0],
                track_id=row[1],
                action_type=row[2],
                listen_duration_seconds=row[3],
                timestamp=row[4]
            ))
        
        return events
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении событий: {str(e)}"
        )


@router.get(
    "/events/track/{track_id}",
    response_model=List[UserTrackInteraction],
    summary="История событий трека",
    description="Возвращает историю взаимодействий с треком"
)
async def get_track_events(
    track_id: int,
    limit: int = 100,
    offset: int = 0
):
    """
    Получение истории событий для конкретного трека
    """
    clickhouse = get_clickhouse_client()
    
    try:
        # Проверяем существование трека
        track_check = await clickhouse.execute_raw(
            "SELECT count() FROM tracks WHERE track_id = {track_id:UInt32}",
            parameters={"track_id": track_id}
        )
        if track_check[0][0] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Трек с ID {track_id} не найден"
            )
        
        result = await clickhouse.execute_raw(
            f"""
            SELECT user_id, track_id, action_type, listen_duration_seconds, timestamp
            FROM user_track_interactions
            WHERE track_id = {{track_id:UInt32}}
            ORDER BY timestamp DESC
            LIMIT {limit} OFFSET {offset}
            """,
            parameters={"track_id": track_id}
        )
        
        events = []
        for row in result:
            events.append(UserTrackInteraction(
                user_id=row[0],
                track_id=row[1],
                action_type=row[2],
                listen_duration_seconds=row[3],
                timestamp=row[4]
            ))
        
        return events
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении событий: {str(e)}"
        )
