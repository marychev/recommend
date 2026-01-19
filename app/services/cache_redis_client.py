"""
Сервис для работы с Redis (кэширование)
"""

from typing import Optional
import redis.asyncio as redis

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """Подключение к Redis"""
        try:
            self.redis = await redis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
                password=(
                    settings.redis_password
                    if settings.redis_password
                    else None
                ),
                encoding="utf-8",
                decode_responses=True,
            )
            await self.redis.ping()
            logger.info(
                "Подключение к Redis установлено: %s:%s",
                settings.redis_host, settings.redis_port
            )
        except Exception as e:
            logger.error("Ошибка подключения к Redis: %s", e)
            raise

    async def disconnect(self):
        """Отключение от Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("Подключение к Redis закрыто")

    async def is_connected(self) -> bool:
        """Проверка подключения"""
        try:
            if self.redis:
                await self.redis.ping()
                return True
        except Exception:
            return False
        return False

    async def get(self, key: str) -> Optional[str]:
        """Получить значение по ключу"""
        if self.redis:
            return await self.redis.get(key)
        return None

    async def set(
        self, key: str, value: str, ex: Optional[int] = None
    ) -> bool:
        """
        Установить значение по ключу

        Args:
            key: Ключ
            value: Значение
            ex: TTL в секундах
        """
        if self.redis:
            await self.redis.set(key, value, ex=ex)
            return True
        return False

    async def delete(self, *keys: str) -> int:
        """Удалить ключи"""
        if self.redis:
            return await self.redis.delete(*keys)
        return 0

    async def keys(self, pattern: str) -> list:
        """Найти ключи по паттерну"""
        if self.redis:
            return await self.redis.keys(pattern)
        return []

    async def incr(self, key: str) -> Optional[int]:
        """
        Атомарный инкремент счетчика.
        
        Используется для генерации уникальных ID без race condition.
        
        Args:
            key: Ключ счетчика
            
        Returns:
            Новое значение счетчика или None если Redis недоступен
        """
        if self.redis:
            return await self.redis.incr(key)
        return None

    async def setnx(self, key: str, value: str) -> bool:
        """
        Установить значение только если ключ не существует (атомарно).
        
        Args:
            key: Ключ
            value: Значение
            
        Returns:
            True если значение установлено, False если ключ уже существовал
        """
        if self.redis:
            return await self.redis.setnx(key, value)
        return False


# Глобальный экземпляр клиента
redis_client = RedisClient()


def get_redis_client() -> RedisClient:
    """Получить экземпляр Redis клиента"""
    return redis_client


async def connect_redis() -> bool:
    """Подключение к Redis при старте приложения"""
    redis_connected = False
    try:
        logger.info(
            "Подключение к Redis (%s:%s)...",
            settings.redis_host, settings.redis_port
        )
        redis = get_redis_client()
        await redis.connect()
        redis_connected = True
        logger.info("Redis подключен успешно!")
    except Exception as exc:
        logger.warning("Не удалось подключиться к Redis: %s", exc)
        logger.info("Запустите: docker-compose up -d redis")

    return redis_connected


async def shutdown_redis() -> None:
    """Отключение от Redis при остановке приложения"""
    try:
        redis = get_redis_client()
        if await redis.is_connected():
            await redis.disconnect()
    except Exception as exc:
        logger.warning("Ошибка при отключении от Redis: %s", exc)

    logger.info("Приложение остановлено")
    logger.info("=" * 60)
