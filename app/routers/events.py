from datetime import datetime
from typing import List, Union
import asyncio
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from app.services.event_queue import get_event_queue
from app.kafka.producer import send_event

from app.models.schemas import UserTrackInteraction, UserTrackInteractionCreate
from app.models.schemas.action_type import ActionType
from app.db.clickhouse import get_clickhouse_client
from app.services.cache import (
    invalidate_cached_user_recommendations,
    exists_user_cached,
    exists_track_cached,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


async def process_event_async(event: UserTrackInteraction):
    """
    Отправка события в очередь для батчинга перед отправкой в Kafka

    Преимущества батчинга:
    - Меньше запросов к Kafka (50 событий в одном запросе)
    - Лучшая пропускная способность
    - Меньше нагрузка на Kafka broker

    Kafka используется для:
    - Асинхронной обработки событий
    - Real-time аналитики
    - Обновления материализованных представлений
    - Расчета метрик в реальном времени
    """
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
        "timestamp": (
            event.timestamp.isoformat()
            if hasattr(event.timestamp, "isoformat")
            else str(event.timestamp)
        ),
    }

    try:
        # Добавляем в очередь (быстро, не блокирует)
        # Очередь автоматически отправляет батчами
        queue = get_event_queue()
        await queue.add_event(event_dict)

        logger.info(
            "Событие добавлено в очередь: "
            "user=%s, track=%s, "
            "action=%s, queue_size=%s",
            event.user_id,
            event.track_id,
            event.action_type,
            queue.get_queue_size(),
        )
    except Exception as e:
        logger.error("Ошибка добавления события в очередь: %s", e)
        # Fallback: пытаемся отправить напрямую в Kafka
        try:
            await send_event(event_dict)
        except Exception as fallback_error:
            logger.error(
                "Fallback отправка в Kafka также не удалась: %s",
                fallback_error,
            )


async def _get_user_track_interaction_bu_row(
    row: tuple,
) -> UserTrackInteraction:
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
        # с кэшированием в Redis для уменьшения нагрузки на БД
        timestamp = event.timestamp if event.timestamp else datetime.now()

        # Проверяем существование параллельно с кэшированием (быстрее чем последовательно)
        user_check, track_check = await asyncio.gather(
            exists_user_cached(event.user_id, clickhouse),
            exists_track_cached(event.track_id, clickhouse),
            return_exceptions=True,
        )

        def _handle_exception_500_(
            check: Union[bool, Exception], who: str
        ) -> None:
            if isinstance(check, Exception):
                if isinstance(check, HTTPException):
                    raise check
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка при проверке %s: %s" % (who, str(check)),
                )

        # Обрабатываем исключения
        _handle_exception_500_(user_check, "пользователя")
        _handle_exception_500_(track_check, "трека")

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
        if event.action_type in [
            ActionType.LIKE,
            ActionType.DISLIKE,
            ActionType.ADD_TO_PLAYLIST,
            ActionType.SHARE,
        ]:
            logger.info(
                "Инвалидация кэша для пользователя %s из-за действия %s",
                event.user_id,
                event.action_type,
            )
            background_tasks.add_task(
                invalidate_cached_user_recommendations, event.user_id
            )
        else:
            logger.info(
                "Кэш НЕ инвалидируется для пользователя %s из-за действия %s",
                event.user_id,
                event.action_type,
            )

        return interaction

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании события: %s" % str(e),
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
        _ = await exists_user_cached(user_id, clickhouse)
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

        return [_get_user_track_interaction_bu_row(r) for r in result]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении событий: {e}",
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
        _ = await exists_track_cached(track_id, clickhouse)
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

        return [_get_user_track_interaction_bu_row(r) for r in result]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении событий трека: %s" % str(e),
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
