"""
Сервис для атомарной генерации уникальных ID.

Использует Redis INCR для гарантии уникальности ID даже при параллельных запросах.
При недоступности Redis использует fallback на timestamp-based ID.
"""

import time
import logging
from typing import Optional

from app.services.cache_redis_client import get_redis_client

logger = logging.getLogger(__name__)


# Префикс для ключей счетчиков ID в Redis
ID_COUNTER_PREFIX = "id_counter"


async def get_next_id(table: str, field: str, fallback_max_id: Optional[int] = None) -> int:
    """
    Получить следующий уникальный ID для таблицы.
    
    Использует атомарный Redis INCR для гарантии уникальности.
    При недоступности Redis использует fallback.
    
    Args:
        table: Имя таблицы (users, tracks, etc.)
        field: Имя поля ID (user_id, track_id, etc.)
        fallback_max_id: Текущий максимальный ID из БД (для инициализации счетчика)
        
    Returns:
        Уникальный ID (int)
        
    Example:
        >>> user_id = await get_next_id("users", "user_id", fallback_max_id=1000)
        >>> print(user_id)  # 1001 (или следующий уникальный)
    """
    redis = get_redis_client()
    counter_key = f"{ID_COUNTER_PREFIX}:{table}:{field}"
    
    try:
        # Проверяем подключение к Redis
        if not await redis.is_connected():
            logger.debug("Redis недоступен, используем fallback для ID")
            return _generate_fallback_id(fallback_max_id)
        
        # Проверяем, инициализирован ли счетчик
        current_value = await redis.get(counter_key)
        
        if current_value is None:
            # Счетчик не инициализирован - нужно его создать
            # Если есть fallback_max_id, используем его как начальное значение
            if fallback_max_id is not None and fallback_max_id > 0:
                # Используем SETNX для атомарной инициализации
                initialized = await redis.setnx(counter_key, str(fallback_max_id))
                if initialized:
                    logger.info(
                        "Счетчик ID инициализирован: %s = %s (из БД)",
                        counter_key, fallback_max_id
                    )
            # Если SETNX вернул False, другой процесс уже инициализировал счетчик
        
        # Атомарный инкремент - гарантирует уникальность даже при параллельных запросах
        new_id = await redis.incr(counter_key)
        
        if new_id is not None:
            logger.debug("Сгенерирован ID через Redis: %s = %s", counter_key, new_id)
            return new_id
        else:
            # Если incr вернул None, Redis отключился
            return _generate_fallback_id(fallback_max_id)
            
    except Exception as e:
        logger.warning("Ошибка генерации ID через Redis: %s. Используем fallback.", e)
        return _generate_fallback_id(fallback_max_id)


def _generate_fallback_id(max_id: Optional[int] = None) -> int:
    """
    Генерация fallback ID когда Redis недоступен.
    
    Использует timestamp + случайную компоненту для минимизации коллизий.
    
    Args:
        max_id: Максимальный известный ID из БД
        
    Returns:
        ID на основе timestamp (может быть коллизия при высокой нагрузке)
    """
    # Используем миллисекунды timestamp
    timestamp_part = int(time.time() * 1000) % 10_000_000_000
    
    # Если известен max_id и он больше timestamp_part, используем max_id + 1
    if max_id is not None and max_id >= timestamp_part:
        fallback_id = max_id + 1
    else:
        fallback_id = timestamp_part
    
    logger.warning(
        "Используется fallback ID: %s (Redis недоступен, возможны коллизии)",
        fallback_id
    )
    return fallback_id


async def sync_id_counter_from_db(table: str, field: str, max_id: int) -> bool:
    """
    Синхронизировать счетчик ID с текущим максимальным значением из БД.
    
    Используется при старте приложения для инициализации счетчиков.
    
    Args:
        table: Имя таблицы
        field: Имя поля ID
        max_id: Текущий максимальный ID из БД
        
    Returns:
        True если синхронизация успешна
    """
    redis = get_redis_client()
    counter_key = f"{ID_COUNTER_PREFIX}:{table}:{field}"
    
    try:
        if not await redis.is_connected():
            return False
        
        # Получаем текущее значение счетчика
        current_value = await redis.get(counter_key)
        current_int = int(current_value) if current_value else 0
        
        # Если max_id из БД больше, обновляем счетчик
        if max_id > current_int:
            await redis.set(counter_key, str(max_id))
            logger.info(
                "Счетчик ID синхронизирован: %s = %s (было %s)",
                counter_key, max_id, current_int
            )
        
        return True
        
    except Exception as e:
        logger.error("Ошибка синхронизации счетчика ID: %s", e)
        return False
