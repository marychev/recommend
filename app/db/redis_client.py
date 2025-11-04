from typing import Optional
import redis.asyncio as redis

from app.config import settings


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
            print(
                f"✓ Подключение к Redis установлено: {settings.redis_host}:{settings.redis_port}"
            )
        except Exception as e:
            print(f"✗ Ошибка подключения к Redis: {e}")
            raise

    async def disconnect(self):
        """Отключение от Redis"""
        if self.redis:
            await self.redis.close()
            print("✓ Подключение к Redis закрыто")

    async def is_connected(self) -> bool:
        """Проверка подключения"""
        try:
            if self.redis:
                await self.redis.ping()
                return True
        except Exception:
            return False
        return False


redis_client = RedisClient()


def get_redis_client() -> RedisClient:
    return redis_client


async def connect_redis() -> bool:
    redis_connected = False
    try:
        print(
            f"\n🔴 Подключение к Redis "
            f"({settings.redis_host}:{settings.redis_port})..."
        )
        redis = get_redis_client()
        await redis.connect()
        redis_connected = True
        print("   ✅ Redis подключен успешно!")
    except Exception as exc:
        print(f"   ⚠️ Не удалось подключиться к Redis: {exc}")
        print("   💡 Запустите: docker-compose up -d redis")

    return redis_connected


async def shutdown_redis() -> None:
    """Отключение от Redis"""
    try:
        redis = get_redis_client()
        if await redis.is_connected():
            await redis.disconnect()
    except Exception as exc:
        print(f"⚠️ Ошибка при отключении от Redis: {exc}")

    print("✓ Приложение остановлено")
    print("=" * 60)
