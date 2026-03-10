"""
Обработчик событий для Kafka Consumer

Обрабатывает события из Kafka для:
- Обновления метрик в Redis (счетчики проигрываний, лайков и т.д.)
- Логирования событий для аналитики
- Мониторинга активности пользователей
"""

import logging
from typing import Dict, Any
from datetime import datetime

from app.services.cache_redis_client import get_redis_client
from app.models.schemas.action_type import ActionType

logger = logging.getLogger(__name__)

# TTL для аналитических метрик в Redis
ANALYTICS_TTL_7_DAYS = 86400 * 7
ANALYTICS_TTL_30_DAYS = 86400 * 30


async def process_event_handler(event: Dict[str, Any]) -> None:
    """
    Обработчик событий из Kafka

    Обновляет метрики в Redis и логирует события для аналитики.
    Не обновляет user_track_matrix (это делает MATERIALIZED VIEW автоматически).

    Args:
        event: Событие взаимодействия пользователя с треком
    """
    try:
        redis_client = get_redis_client()
        if not await redis_client.is_connected():
            logger.warning("Redis недоступен, пропускаем обработку события")
            return

        user_id = event.get("user_id")
        track_id = event.get("track_id")
        action_type = event.get("action_type")

        if not all([user_id, track_id, action_type]):
            logger.warning("Неполное событие: %s", event)
            return

        await update_analytics_metrics(
            redis_client, int(user_id), int(track_id), action_type
        )

        logger.debug(
            "Событие обработано: user=%s, track=%s, action=%s",
            user_id,
            track_id,
            action_type,
        )

    except Exception as e:
        logger.error(
            "Ошибка обработки события: %s",
            e,
            extra={"event": event},
            exc_info=True,
        )


async def update_analytics_metrics(
    redis_client, user_id: int, track_id: int, action_type: str
) -> None:
    """
    Обновить метрики аналитики в Redis

    Обновляет счетчики:
    - Общее количество действий по типам
    - Популярность треков
    - Активность пользователей

    Args:
        redis_client: Redis клиент (RedisClient)
        user_id: ID пользователя
        track_id: ID трека
        action_type: Тип действия
    """
    try:
        if redis_client.redis is None:
            return

        redis = redis_client.redis

        # Счетчики по типам действий (глобальные)
        action_key = f"analytics:action:{action_type}:count"
        await redis.incr(action_key)
        await redis.expire(action_key, ANALYTICS_TTL_7_DAYS)

        # Популярность треков (счетчик проигрываний)
        if action_type == ActionType.PLAY.value:
            track_plays_key = f"analytics:track:{track_id}:plays"
            await redis.incr(track_plays_key)
            await redis.expire(track_plays_key, ANALYTICS_TTL_30_DAYS)

        # Лайки треков
        if action_type == ActionType.LIKE.value:
            track_likes_key = f"analytics:track:{track_id}:likes"
            await redis.incr(track_likes_key)
            await redis.expire(track_likes_key, ANALYTICS_TTL_30_DAYS)

        # Активность пользователя
        user_activity_key = f"analytics:user:{user_id}:activity"
        await redis.incr(user_activity_key)
        await redis.expire(user_activity_key, ANALYTICS_TTL_7_DAYS)

        # Последняя активность пользователя
        user_last_activity_key = f"analytics:user:{user_id}:last_activity"
        await redis.set(
            user_last_activity_key,
            datetime.now().isoformat(),
            ex=ANALYTICS_TTL_7_DAYS,
        )

    except Exception as e:
        logger.error(
            "Ошибка обновления метрик: %s",
            e,
            extra={
                "user_id": user_id,
                "track_id": track_id,
                "action_type": action_type,
            },
        )
