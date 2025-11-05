"""
Сервис кэширования рекомендаций в Redis
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.services.cache_redis_client import get_redis_client

logger = logging.getLogger(__name__)

# TTL для кэша рекомендаций (в секундах)
RECOMMENDATIONS_CACHE_TTL = 3600  # 1 час


def _get_cache_key(user_id: int, top_n: int, exclude_listened: bool) -> str:
    """
    Создать ключ для кэша рекомендаций

    Args:
        user_id: ID пользователя
        top_n: Количество рекомендаций
        exclude_listened: Исключить прослушанные треки

    Returns:
        str: Ключ для Redis
    """
    return (
        f"recommendations:user:{user_id}:"
        f"top_n:{top_n}:exclude:{exclude_listened}"
    )


async def get_cached_recommendations(
    user_id: int, top_n: int = 10, exclude_listened: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Получить рекомендации из кэша

    Args:
        user_id: ID пользователя
        top_n: Количество рекомендаций
        exclude_listened: Исключить прослушанные

    Returns:
        dict | None: Рекомендации или None если не в кэше
    """
    try:
        redis = get_redis_client()

        if not await redis.is_connected():
            logger.warning("Redis not connected, cache disabled")
            return None

        cache_key = _get_cache_key(user_id, top_n, exclude_listened)
        cached_data = await redis.get(cache_key)

        if cached_data:
            logger.debug("Cache hit for user_id=%s, top_n=%s", user_id, top_n)
            # Десериализуем JSON
            data = json.loads(cached_data)

            # Конвертируем ISO строки обратно в datetime
            if "generated_at" in data:
                data["generated_at"] = datetime.fromisoformat(
                    data["generated_at"]
                )

            for rec in data.get("recommendations", []):
                if "track" in rec and "created_at" in rec["track"]:
                    rec["track"]["created_at"] = datetime.fromisoformat(
                        rec["track"]["created_at"]
                    )

            return data

        logger.debug("Cache miss for user_id=%s", user_id)
        return None

    except Exception as e:
        logger.error("Error getting cached recommendations: %s", e)
        return None


async def set_cached_recommendations(
    user_id: int,
    top_n: int,
    exclude_listened: bool,
    recommendations: Dict[str, Any],
    ttl: int = RECOMMENDATIONS_CACHE_TTL,
) -> bool:
    """
    Сохранить рекомендации в кэш

    Args:
        user_id: ID пользователя
        top_n: Количество рекомендаций
        exclude_listened: Исключить прослушанные
        recommendations: Данные рекомендаций
        ttl: Время жизни кэша в секундах

    Returns:
        bool: True если успешно закэшировано
    """
    try:
        redis = get_redis_client()

        if not await redis.is_connected():
            logger.warning("Redis not connected, skipping cache")
            return False

        cache_key = _get_cache_key(user_id, top_n, exclude_listened)

        # Создаем копию для сериализации
        cache_data = recommendations.copy()

        # Конвертируем datetime в ISO строки
        if "generated_at" in cache_data:
            cache_data["generated_at"] = cache_data["generated_at"].isoformat()

        for rec in cache_data.get("recommendations", []):
            if "track" in rec and "created_at" in rec["track"]:
                rec["track"]["created_at"] = rec["track"][
                    "created_at"
                ].isoformat()

        # Сериализуем в JSON
        cache_value = json.dumps(cache_data, ensure_ascii=False)

        # Сохраняем с TTL
        await redis.set(cache_key, cache_value, ex=ttl)

        logger.debug(
            "Cached recommendations for user_id=%s (TTL=%s)", user_id, ttl
        )

        return True

    except Exception as e:
        logger.error("Error caching recommendations: %s", e)
        return False


async def invalidate_user_recommendations(user_id: int) -> bool:
    """
    Инвалидировать все кэшированные рекомендации для пользователя

    Используется когда пользователь выполняет новые действия
    (слушает треки, ставит лайки и т.д.)

    Args:
        user_id: ID пользователя

    Returns:
        bool: True если успешно инвалидировано
    """
    try:
        redis = get_redis_client()

        if not await redis.is_connected():
            return False

        # Ищем все ключи для этого пользователя
        pattern = f"recommendations:user:{user_id}:*"
        keys = await redis.keys(pattern)

        if keys:
            await redis.delete(*keys)
            logger.info(
                "Invalidated %s cached recommendations for user_id=%s",
                len(keys),
                user_id,
            )

        return True

    except Exception as e:
        logger.error("Error invalidating cache for user_id=%s: %s", user_id, e)
        return False


async def get_cache_stats() -> Dict[str, Any]:
    """
    Получить статистику кэша рекомендаций

    Returns:
        dict: Статистика кэша
    """
    try:
        redis = get_redis_client()

        if not await redis.is_connected():
            return {"status": "disconnected"}

        # Подсчитываем количество закэшированных рекомендаций
        pattern = "recommendations:user:*"
        keys = await redis.keys(pattern)

        return {
            "status": "connected",
            "cached_recommendations": len(keys),
            "ttl_seconds": RECOMMENDATIONS_CACHE_TTL,
        }

    except Exception as e:
        logger.error("Error getting cache stats: %s", e)
        return {"status": "error", "error": str(e)}
