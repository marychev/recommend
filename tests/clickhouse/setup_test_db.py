"""
Скрипт для создания тестовой базы данных ClickHouse
"""

import asyncio
from asynch import connect
from app.config import settings


async def setup_test_database():
    """Создает тестовую БД если её нет"""
    test_db = "music_recommend_test"

    try:
        # Подключаемся к default БД
        conn = await connect(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            user=settings.clickhouse_user,
            password=settings.clickhouse_password,
            database="default",
        )

        async with conn.cursor() as cursor:
            # Создаем тестовую БД
            await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {test_db}")
            print(f"✓ Тестовая база данных '{test_db}' готова")

        await conn.close()
        return True

    except Exception as e:
        print(f"✗ Ошибка создания тестовой БД: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(setup_test_database())
    exit(0 if success else 1)
