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


# TTL для кэша рекомендаций (в секундах) Теперь конфигурируется через settings
def get_cache_recommendations_ttl() -> int:
    """Получить TTL для кэша рекомендаций из конфигурации"""
    return settings.recommendations_cache_ttl


def get_cache_key_recommendations(user_id: int, top_n: int, exclude_listened: bool) -> str:
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
) -> Any:
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
            return

        cache_key = get_cache_key_recommendations(user_id, top_n, exclude_listened)
        cached_data = await redis.get(cache_key)

        if cached_data:
            logger.debug("Cache hit for user_id=%s, top_n=%s", user_id, top_n)
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
        return

    except Exception as e:
        logger.error("Error getting cached recommendations: %s", e)
        return


async def set_cached_recommendations(
    user_id: int,
    top_n: int,
    exclude_listened: bool,
    recommendations: Dict[str, Any],
    ttl: Optional[int] = None,
) -> bool:
    """
    Сохранить рекомендации в кэш

    Args:
        user_id: ID пользователя
        top_n: Количество рекомендаций
        exclude_listened: Исключить прослушанные
        recommendations: Данные рекомендаций
        ttl: Время жизни кэша в секундах (если None, используется из настроек)

    Returns:
        bool: True если успешно закэшировано
    """
    try:
        if ttl is None:
            ttl = get_cache_recommendations_ttl()
        
        redis = get_redis_client()
        if not await redis.is_connected():
            logger.warning("Redis not connected, skipping cache")
            return False

        cache_key = get_cache_key_recommendations(user_id, top_n, exclude_listened)

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

        cache_value = json.dumps(cache_data, ensure_ascii=False)
        await redis.set(cache_key, cache_value, ex=ttl)

        logger.debug(
            "Cached recommendations for user_id=%s (TTL=%s)", user_id, ttl
        )

        return True

    except Exception as e:
        logger.error("Error caching recommendations: %s", e)
        return False


async def invalidate_cached_user_recommendations(user_id: int) -> bool:
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
            "ttl_seconds": get_cache_recommendations_ttl(),
        }

    except Exception as e:
        logger.error("Error getting cache stats: %s", e)
        return {"status": "error", "error": str(e)}


# ════════════════════════════════════════════════════════
# Кэширование проверок существования (exists_user/exists_track)
# ════════════════════════════════════════════════════════


def _get_user_exists_cache_key(user_id: int) -> str:
    """Создать ключ для кэша проверки существования пользователя"""
    return f"exists:user:{user_id}"


def _get_track_exists_cache_key(track_id: int) -> str:
    """Создать ключ для кэша проверки существования трека"""
    return f"exists:track:{track_id}"


async def exists_user_cached(user_id: int, clickhouse_client) -> bool:
    """
    Проверить существование пользователя с кэшированием в Redis
    
    Args:
        user_id: ID пользователя
        clickhouse_client: Клиент ClickHouse
    
    Returns:
        bool: True если пользователь существует, иначе выбрасывает HTTPException
    """
    try:
        redis = get_redis_client()
        
        # Пытаемся получить из кэша (если Redis доступен)
        try:
            cache_key = _get_user_exists_cache_key(user_id)
            cached = await redis.get(cache_key)
            
            if cached is not None:
                # "1" = существует, "0" = не существует
                if cached == "1":
                    logger.debug("Cache hit: user_id=%s exists", user_id)
                    return True
                else:
                    # Не существует - выбрасываем исключение
                    logger.debug("Cache hit: user_id=%s does not exist", user_id)
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Пользователь с ID {user_id} не найден",
                    )
        except Exception:
            # Redis недоступен или ошибка - продолжаем без кэша
            pass
        
        # Кэш промах или Redis недоступен - проверяем в БД
        logger.debug("Cache miss: checking user_id=%s in DB", user_id)
        result = await clickhouse_client.exists_user(user_id)
        
        # Сохраняем в кэш (если Redis доступен, игнорируем ошибки)
        try:
            cache_key = _get_user_exists_cache_key(user_id)
            # exists_user выбрасывает HTTPException если не найден, поэтому result всегда True
            await redis.set(cache_key, "1", ex=EXISTS_CACHE_TTL)
            logger.debug("Cached user_id=%s exists=True", user_id)
        except Exception:
            pass  # Игнорируем ошибки кэширования
        
        return result
        
    except HTTPException:
        # Если пользователь не найден, кэшируем это тоже (игнорируем ошибки)
        try:
            cache_key = _get_user_exists_cache_key(user_id)
            await redis.set(cache_key, "0", ex=EXISTS_CACHE_TTL)
            logger.debug("Cached user_id=%s exists=False", user_id)
        except Exception:
            pass  # Игнорируем ошибки кэширования
        raise
    except Exception as e:
        # Если ошибка кэширования, просто делаем запрос к БД
        logger.warning("Cache error for user_id=%s, falling back to DB: %s", user_id, e)
        return await clickhouse_client.exists_user(user_id)


async def exists_track_cached(track_id: int, clickhouse_client) -> bool:
    """
    Проверить существование трека с кэшированием в Redis
    
    Args:
        track_id: ID трека
        clickhouse_client: Клиент ClickHouse
    
    Returns:
        bool: True если трек существует, иначе выбрасывает HTTPException
    """
    try:
        redis = get_redis_client()
        
        # Пытаемся получить из кэша (если Redis доступен)
        try:
            cache_key = _get_track_exists_cache_key(track_id)
            cached = await redis.get(cache_key)
            
            if cached is not None:
                # "1" = существует, "0" = не существует
                if cached == "1":
                    logger.debug("Cache hit: track_id=%s exists", track_id)
                    return True
                else:
                    # Не существует - выбрасываем исключение
                    logger.debug("Cache hit: track_id=%s does not exist", track_id)
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Трек с ID {track_id} не найден",
                    )
        except Exception:
            # Redis недоступен или ошибка - продолжаем без кэша
            pass
        
        # Кэш промах или Redis недоступен - проверяем в БД
        logger.debug("Cache miss: checking track_id=%s in DB", track_id)
        result = await clickhouse_client.exists_track(track_id)
        
        # Сохраняем в кэш (если Redis доступен, игнорируем ошибки)
        try:
            cache_key = _get_track_exists_cache_key(track_id)
            # exists_track выбрасывает HTTPException если не найден, поэтому result всегда True
            await redis.set(cache_key, "1", ex=EXISTS_CACHE_TTL)
            logger.debug("Cached track_id=%s exists=True", track_id)
        except Exception:
            pass  # Игнорируем ошибки кэширования
        
        return result
        
    except HTTPException:
        # Если трек не найден, кэшируем это тоже (игнорируем ошибки)
        try:
            cache_key = _get_track_exists_cache_key(track_id)
            await redis.set(cache_key, "0", ex=EXISTS_CACHE_TTL)
            logger.debug("Cached track_id=%s exists=False", track_id)
        except Exception:
            pass  # Игнорируем ошибки кэширования
        raise
    except Exception as e:
        # Если ошибка кэширования, просто делаем запрос к БД
        logger.warning("Cache error for track_id=%s, falling back to DB: %s", track_id, e)
        return await clickhouse_client.exists_track(track_id)


async def invalidate_user_exists_cache(user_id: int) -> bool:
    """
    Инвалидировать кэш проверки существования пользователя
    
    Используется при создании/удалении пользователя
    
    Args:
        user_id: ID пользователя
    
    Returns:
        bool: True если успешно инвалидировано
    """
    try:
        redis = get_redis_client()
        if not await redis.is_connected():
            return False
        
        cache_key = _get_user_exists_cache_key(user_id)
        await redis.delete(cache_key)
        logger.debug("Invalidated exists cache for user_id=%s", user_id)
        return True
    except Exception as e:
        logger.error("Error invalidating user exists cache: %s", e)
        return False


async def invalidate_track_exists_cache(track_id: int) -> bool:
    """
    Инвалидировать кэш проверки существования трека
    
    Используется при создании/удалении трека
    
    Args:
        track_id: ID трека
    
    Returns:
        bool: True если успешно инвалидировано
    """
    try:
        redis = get_redis_client()
        if not await redis.is_connected():
            return False
        
        cache_key = _get_track_exists_cache_key(track_id)
        await redis.delete(cache_key)
        logger.debug("Invalidated exists cache for track_id=%s", track_id)
        return True
    except Exception as e:
        logger.error("Error invalidating track exists cache: %s", e)
        return False
