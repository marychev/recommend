"""
Сервис кэширования рекомендаций в Redis
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status

from app.services.cache_redis_client import get_redis_client
from app.config import settings


logger = logging.getLogger(__name__)

# TTL для кэша проверок существования (в секундах)
# 5 минут - достаточно для снижения нагрузки, но не слишком долго
EXISTS_CACHE_TTL = 300

# TTL для глобального кэша популярных треков (в секундах)
# 10 минут — популярные треки меняются нечасто
POPULAR_TRACKS_CACHE_TTL = 600


def get_cache_recommendations_ttl() -> int:
    return settings.recommendations_cache_ttl


def get_cache_key_recommendations(user_id: int, top_n: int, exclude_listened: bool) -> str:
    """Создать ключ для кэша рекомендаций"""
    return (
        f"recommendations:user:{user_id}:"
        f"top_n:{top_n}:exclude:{exclude_listened}"
    )


async def get_cached_recommendations(
    user_id: int, top_n: int = 10, exclude_listened: bool = True
) -> Any:
    """Получить рекомендации из кэша"""
    try:
        redis = get_redis_client()
        if not await redis.is_connected():
            logger.warning("Redis not connected, cache disabled")
            return

        cache_key = get_cache_key_recommendations(user_id, top_n, exclude_listened)
        cached_data = await redis.get(cache_key)

        if cached_data:
            logger.info(
                "Cache HIT for user_id=%s, top_n=%s, exclude_listened=%s",
                user_id, top_n, exclude_listened
            )
            data = json.loads(cached_data)

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

        logger.info(
            "Cache MISS for user_id=%s, top_n=%s, exclude_listened=%s",
            user_id, top_n, exclude_listened
        )
    except Exception as e:
        logger.error("Error getting cached recommendations: %s", e)


async def set_cached_recommendations(
    user_id: int,
    top_n: int,
    exclude_listened: bool,
    recommendations: Dict[str, Any],
    ttl: Optional[int] = None,
) -> bool:
    """Сохранить рекомендации в кэш"""
    try:
        if ttl is None:
            ttl = get_cache_recommendations_ttl()

        redis = get_redis_client()
        if not await redis.is_connected():
            logger.warning("Redis not connected, skipping cache")
            return False

        cache_key = get_cache_key_recommendations(user_id, top_n, exclude_listened)

        cache_data = recommendations.copy()

        if "generated_at" in cache_data:
            cache_data["generated_at"] = cache_data["generated_at"].isoformat()

        for rec in cache_data.get("recommendations", []):
            if "track" in rec and "created_at" in rec["track"]:
                rec["track"]["created_at"] = rec["track"][
                    "created_at"
                ].isoformat()

        cache_value = json.dumps(cache_data, ensure_ascii=False)
        await redis.set(cache_key, cache_value, ex=ttl)

        logger.info(
            "Cached recommendations for user_id=%s, top_n=%s, exclude_listened=%s (TTL=%s sec)",
            user_id, top_n, exclude_listened, ttl
        )

        return True

    except Exception as e:
        logger.error("Error caching recommendations: %s", e)
        return False


def _get_popular_cache_key(top_n: int, exclude_user_id: Optional[int]) -> str:
    """Ключ для глобального кэша популярных треков."""
    if exclude_user_id is not None:
        return f"popular_tracks:top_n:{top_n}:exclude_user:{exclude_user_id}"
    return f"popular_tracks:top_n:{top_n}"


async def get_cached_popular_tracks(top_n: int, exclude_user_id: Optional[int] = None) -> Any:
    """Получить популярные треки из глобального кэша."""
    try:
        redis = get_redis_client()
        if not await redis.is_connected():
            return None

        cache_key = _get_popular_cache_key(top_n, exclude_user_id)
        cached_data = await redis.get(cache_key)

        if cached_data:
            logger.debug("Popular tracks cache HIT: top_n=%s", top_n)
            return json.loads(cached_data)

        logger.debug("Popular tracks cache MISS: top_n=%s", top_n)
    except Exception as e:
        logger.error("Error getting cached popular tracks: %s", e)
    return None


async def set_cached_popular_tracks(
    top_n: int,
    tracks_data: list,
    exclude_user_id: Optional[int] = None,
) -> bool:
    """Сохранить популярные треки в глобальный кэш."""
    try:
        redis = get_redis_client()
        if not await redis.is_connected():
            return False

        cache_key = _get_popular_cache_key(top_n, exclude_user_id)
        cache_value = json.dumps(tracks_data, ensure_ascii=False, default=str)
        await redis.set(cache_key, cache_value, ex=POPULAR_TRACKS_CACHE_TTL)
        logger.debug("Cached popular tracks: top_n=%s (TTL=%ss)", top_n, POPULAR_TRACKS_CACHE_TTL)
        return True
    except Exception as e:
        logger.error("Error caching popular tracks: %s", e)
        return False


async def invalidate_cached_user_recommendations(user_id: int) -> bool:
    """Инвалидировать все кэшированные рекомендации для пользователя"""
    try:
        redis = get_redis_client()
        if not await redis.is_connected():
            return False

        pattern = f"recommendations:user:{user_id}:*"
        keys = await redis.keys(pattern)

        if keys:
            await redis.delete(*keys)
            logger.info(
                "Invalidated %s cached recommendations for user_id=%s (keys: %s)",
                len(keys),
                user_id,
                ", ".join(keys[:5]) + ("..." if len(keys) > 5 else "")
            )

        return True

    except Exception as e:
        logger.error("Error invalidating cache for user_id=%s: %s", user_id, e)
        return False


async def get_cache_stats() -> Dict[str, Any]:
    """Получить статистику кэша рекомендаций"""
    try:
        redis = get_redis_client()
        if not await redis.is_connected():
            return {"status": "disconnected"}

        pattern = "recommendations:user:*"
        keys = await redis.keys(pattern)

        return {
            "status": "connected",
            "cached_recommendations": len(keys),
            "ttl_seconds": get_cache_recommendations_ttl(),
        }

    except Exception as e:
        logger.error("Error getting cache stats: %s", e)
        return {"status": "error", "error": str(e)}


# ════════════════════════════════════════════════════════
# Кэширование проверок существования (exists_user/exists_track)
# Обобщённая реализация вместо дублирования для user/track
# ════════════════════════════════════════════════════════


def _get_exists_cache_key(entity_type: str, entity_id: int) -> str:
    return f"exists:{entity_type}:{entity_id}"


async def _exists_entity_cached(
    entity_type: str,
    entity_id: int,
    check_fn,
    not_found_detail: str,
) -> bool:
    """
    Обобщённая проверка существования сущности с кэшированием в Redis.

    Args:
        entity_type: Тип сущности ("user" или "track")
        entity_id: ID сущности
        check_fn: Async функция проверки в БД (вызывается без аргументов)
        not_found_detail: Текст ошибки 404
    """
    redis = get_redis_client()

    try:
        # Пытаемся получить из кэша
        try:
            cache_key = _get_exists_cache_key(entity_type, entity_id)
            cached = await redis.get(cache_key)

            if cached is not None:
                if cached == "1":
                    logger.debug("Cache hit: %s_id=%s exists", entity_type, entity_id)
                    return True
                else:
                    logger.debug("Cache hit: %s_id=%s does not exist", entity_type, entity_id)
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=not_found_detail,
                    )
        except HTTPException:
            raise
        except Exception:
            pass

        # Кэш промах — проверяем в БД
        logger.debug("Cache miss: checking %s_id=%s in DB", entity_type, entity_id)
        result = await check_fn()

        # Сохраняем в кэш
        try:
            cache_key = _get_exists_cache_key(entity_type, entity_id)
            await redis.set(cache_key, "1", ex=EXISTS_CACHE_TTL)
            logger.debug("Cached %s_id=%s exists=True", entity_type, entity_id)
        except Exception:
            pass

        return result

    except HTTPException:
        # Не найден — кэшируем отрицательный результат
        try:
            cache_key = _get_exists_cache_key(entity_type, entity_id)
            await redis.set(cache_key, "0", ex=EXISTS_CACHE_TTL)
            logger.debug("Cached %s_id=%s exists=False", entity_type, entity_id)
        except Exception:
            pass
        raise
    except Exception as e:
        logger.warning("Cache error for %s_id=%s, falling back to DB: %s", entity_type, entity_id, e)
        return await check_fn()


async def exists_user_cached(user_id: int, clickhouse_client) -> bool:
    """Проверить существование пользователя с кэшированием в Redis"""
    return await _exists_entity_cached(
        entity_type="user",
        entity_id=user_id,
        check_fn=lambda: clickhouse_client.exists_user(user_id),
        not_found_detail=f"Пользователь с ID {user_id} не найден",
    )


async def exists_track_cached(track_id: int, clickhouse_client) -> bool:
    """Проверить существование трека с кэшированием в Redis"""
    return await _exists_entity_cached(
        entity_type="track",
        entity_id=track_id,
        check_fn=lambda: clickhouse_client.exists_track(track_id),
        not_found_detail=f"Трек с ID {track_id} не найден",
    )


async def _invalidate_exists_cache(entity_type: str, entity_id: int) -> bool:
    """Обобщённая инвалидация кэша проверки существования"""
    try:
        redis = get_redis_client()
        if not await redis.is_connected():
            return False

        cache_key = _get_exists_cache_key(entity_type, entity_id)
        await redis.delete(cache_key)
        logger.debug("Invalidated exists cache for %s_id=%s", entity_type, entity_id)
        return True
    except Exception as e:
        logger.error("Error invalidating %s exists cache: %s", entity_type, e)
        return False


async def invalidate_user_exists_cache(user_id: int) -> bool:
    """Инвалидировать кэш проверки существования пользователя"""
    return await _invalidate_exists_cache("user", user_id)


async def invalidate_track_exists_cache(track_id: int) -> bool:
    """Инвалидировать кэш проверки существования трека"""
    return await _invalidate_exists_cache("track", track_id)
