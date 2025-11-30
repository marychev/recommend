from datetime import datetime
from typing import List
import asyncio
from fastapi import APIRouter, HTTPException, status, BackgroundTasks

from app.models.schemas import UserTrackInteraction, UserTrackInteractionCreate
from app.models.schemas.action_type import ActionType
from app.db.clickhouse import get_clickhouse_client
from app.kafka.producer import send_event
from app.services.cache import invalidate_user_recommendations

router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


async def process_event_async(event: UserTrackInteraction):
    """
    Отправка события в Kafka для дальнейшей обработки

    Kafka используется для:
    - Асинхронной обработки событий
    - Real-time аналитики
    - Обновления материализованных представлений
    - Расчета метрик в реальном времени
    """
    try:
        # Преобразуем Pydantic модель в словарь
        event_dict = {
            "user_id": event.user_id,
            "track_id": event.track_id,
            "action_type": (
                event.action_type.value
                if hasattr(event.action_type, "value")
                else event.action_type
            ),
            "listen_duration_seconds": event.listen_duration_seconds,
            "timestamp": event.timestamp,
        }

        # Отправляем в Kafka
        success = await send_event(event_dict)

        if success:
            print(
                f"✅ Событие отправлено в Kafka: "
                f"user={event.user_id}, track={event.track_id}, "
                f"action={event.action_type}"
            )
        else:
            print(
                "⚠️  Не удалось отправить событие в Kafka "
                "(событие сохранено в ClickHouse)"
            )
    except Exception as e:
        print(f"❌ Ошибка отправки в Kafka: {e}")


async def _get_user_track_interaction_bu_row(row: tuple) -> UserTrackInteraction:
    return UserTrackInteraction(
        user_id=row[0],
        track_id=row[1],
        action_type=row[2],
        listen_duration_seconds=row[3],
        timestamp=row[4],
    )


@router.post(
    "",
    response_model=UserTrackInteraction,
    status_code=status.HTTP_201_CREATED,
    summary="Отправить событие",
    description="Принимает событие взаимодействия пользователя с треком",
)
async def create_event(
    event: UserTrackInteractionCreate, background_tasks: BackgroundTasks
):
    """
    Создание события взаимодействия пользователя с треком

    **Типы действий** (ActionType enum):
    - `play` (вес: +1.0) - Прослушивание трека
    - `like` (вес: +3.0) - Лайк трека
    - `dislike` (вес: -3.0) - Дизлайк трека
    - `skip` (вес: -0.5) - Пропуск трека
    - `add_to_playlist` (вес: +2.0) - Добавление в плейлист
    - `share` (вес: +2.5) - Поделиться треком

    > Веса используются для расчета неявного рейтинга в системе рекомендаций.
    > Получить все типы действий программно: `GET /api/v1/events/action-types`
    """
    clickhouse = get_clickhouse_client()

    try:
        # Оптимизация: проверяем существование пользователя и трека параллельно
        # для уменьшения задержек
        timestamp = event.timestamp if event.timestamp else datetime.now()
        
        # Проверяем существование параллельно (быстрее чем последовательно)
        user_check, track_check = await asyncio.gather(
            clickhouse.execute_raw(
                f"SELECT 1 FROM users WHERE user_id = {event.user_id} LIMIT 1"
            ),
            clickhouse.execute_raw(
                f"SELECT 1 FROM tracks WHERE track_id = {event.track_id} LIMIT 1"
            ),
            return_exceptions=True
        )
        
        # Проверяем результаты
        if isinstance(user_check, Exception) or not user_check or len(user_check) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользователь с ID {event.user_id} не найден",
            )
        
        if isinstance(track_check, Exception) or not track_check or len(track_check) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Трек с ID {event.track_id} не найден",
            )

        await clickhouse.save_event(event, timestamp)

        interaction = UserTrackInteraction(
            user_id=event.user_id,
            track_id=event.track_id,
            action_type=event.action_type,
            listen_duration_seconds=event.listen_duration_seconds,
            timestamp=timestamp,
        )

        # Добавляем задачи в фон
        background_tasks.add_task(process_event_async, interaction)
        
        # Инвалидируем кэш только для значимых действий
        # play и skip не должны сразу инвалидировать кэш
        if event.action_type in [ActionType.LIKE, ActionType.DISLIKE, ActionType.ADD_TO_PLAYLIST, ActionType.SHARE]:
            print(f"🗑️  Инвалидация кэша для пользователя {event.user_id} из-за действия {event.action_type}")
            background_tasks.add_task(
                invalidate_user_recommendations, event.user_id
            )
        else:
            print(f"✅ Кэш НЕ инвалидируется для пользователя {event.user_id} из-за действия {event.action_type}")

        return interaction

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании события: {str(e)}",
        )


@router.get(
    "/user/{user_id}",
    response_model=List[UserTrackInteraction],
    summary="История событий пользователя",
    description="Возвращает историю взаимодействий пользователя с треками",
)
async def get_user_events(user_id: int, limit: int = 100, offset: int = 0):
    """
    Получение истории событий для конкретного пользователя
    """
    clickhouse = get_clickhouse_client()

    try:
        _ = await clickhouse.exists_user(user_id)
        result = await clickhouse.execute_raw(
            f"""
            SELECT user_id, track_id, action_type,
                   listen_duration_seconds, timestamp
            FROM user_track_interactions
            WHERE user_id = {user_id}
            ORDER BY timestamp DESC
            LIMIT {limit} OFFSET {offset}
            """
        )

        return [
            _get_user_track_interaction_bu_row(row)
            for row in result
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении событий: {str(e)}"
        )


@router.get(
    "/track/{track_id}",
    response_model=List[UserTrackInteraction],
    summary="История событий трека",
    description="Возвращает историю взаимодействий с треком",
)
async def get_track_events(track_id: int, limit: int = 100, offset: int = 0):
    """
    Получение истории событий для конкретного трека
    """
    clickhouse = get_clickhouse_client()

    try:
        _ = await clickhouse.exists_track(track_id)
        result = await clickhouse.execute_raw(
            f"""
            SELECT user_id, track_id, action_type,
                   listen_duration_seconds, timestamp
            FROM user_track_interactions
            WHERE track_id = {track_id}
            ORDER BY timestamp DESC
            LIMIT {limit} OFFSET {offset}
            """
        )

        return [
            _get_user_track_interaction_bu_row(row)
            for row in result
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении событий трека: {str(e)}",
        )


@router.get(
    "/action-types",
    response_model=dict,
    summary="Получить типы действий",
    description=(
        "Возвращает все доступные типы действий " "с их описанием и весами"
    ),
)
async def get_action_types():
    """
    Получение информации о всех типах действий

    Возвращает словарь с типами действий, их описаниями и весами
    для расчета неявного рейтинга в системе рекомендаций.

    **Пример ответа:**
    ```json
    {
        "play": {
            "description": "Прослушивание трека",
            "weight": 1.0
        },
        "like": {
            "description": "Лайк трека",
            "weight": 3.0
        }
    }
    ```

    **Применение:**
    - Документация для разработчиков
    - Динамическое построение UI
    - Валидация на клиенте
    - Расчет рейтингов
    """
    return ActionType.get_all_with_info()
