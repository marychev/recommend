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


async def process_event_async(event: UserTrackInteraction, clickhouse_client):
    """
    Отправка события в очередь для батчинга перед отправкой в Kafka
    С fallback на прямой INSERT в ClickHouse если очередь/Kafka недоступны

    Преимущества батчинга:
    - Меньше запросов к Kafka (100 событий в одном запросе)
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

        logger.debug(
            "Событие добавлено в очередь: "
            "user=%s, track=%s, action=%s, queue_size=%s",
            event.user_id,
            event.track_id,
            event.action_type,
            queue.get_queue_size(),
        )
    except Exception as e:
        logger.warning("Ошибка добавления события в очередь: %s. Пробуем fallback.", e)
        # Fallback 1: пытаемся отправить напрямую в Kafka
        try:
            success = await send_event(event_dict)
            if not success:
                raise Exception("send_event вернул False")
        except Exception as kafka_error:
            logger.warning("Fallback отправка в Kafka не удалась: %s. Используем прямой INSERT в ClickHouse.", kafka_error)
            # Fallback 2: прямой INSERT в ClickHouse (как в users/tracks)
            try:
                await clickhouse_client.save_event_buffered(event, event.timestamp)
                logger.debug(
                    "Событие сохранено в ClickHouse через fallback: user=%s, track=%s",
                    event.user_id,
                    event.track_id,
                )
            except Exception as fallback_error:
                logger.error("Fallback INSERT в ClickHouse также не удался: %s", fallback_error)


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
        timestamp = event.timestamp if event.timestamp else datetime.now()

        # Оптимизация: проверяем существование пользователя и трека параллельно
        # с таймаутом для избежания блокировки при высокой нагрузке
        # Используем return_exceptions=True для обработки ошибок без блокировки
        try:
            user_check, track_check = await asyncio.wait_for(
                asyncio.gather(
                    exists_user_cached(event.user_id, clickhouse),
                    exists_track_cached(event.track_id, clickhouse),
                    return_exceptions=True,
                ),
                timeout=5.0  # Таймаут 5 секунд для проверок существования
            )
        except asyncio.TimeoutError:
            # Если проверка заняла слишком долго, логируем предупреждение и продолжаем
            # (события могут быть валидными, но проверка заняла слишком много времени)
            logger.warning(
                "Таймаут при проверке существования user_id=%s, track_id=%s. Продолжаем обработку.",
                event.user_id,
                event.track_id,
            )
            user_check = True  # Предполагаем что существует
            track_check = True

        def _handle_exception_500_(
            check: Union[bool, BaseException], who: str
        ) -> None:
            # asyncio.gather с return_exceptions=True может вернуть BaseException
            # но мы обрабатываем только Exception (HTTPException наследуется от Exception)
            if isinstance(check, Exception):
                if isinstance(check, HTTPException):
                    raise check
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ошибка при проверке %s: %s" % (who, str(check)),
                )

        # Обрабатываем исключения
        # asyncio.gather с return_exceptions=True может вернуть BaseException,
        # но функция обрабатывает только Exception, что безопасно
        _handle_exception_500_(user_check, "пользователя")
        _handle_exception_500_(track_check, "трека")

        # Best practice: отправляем в Kafka, Consumer запишет в ClickHouse батчами
        # Убрали синхронный INSERT в ClickHouse для быстрого ответа клиенту
        interaction = UserTrackInteraction(
            user_id=event.user_id,
            track_id=event.track_id,
            action_type=event.action_type,
            listen_duration_seconds=event.listen_duration_seconds,
            timestamp=timestamp,
        )

        # Отправляем в Kafka с fallback (асинхронно, не блокирует ответ)
        # Передаем clickhouse_client для fallback на прямой INSERT
        background_tasks.add_task(process_event_async, interaction, clickhouse)

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
