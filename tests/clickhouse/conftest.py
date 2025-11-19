"""
Фикстуры для тестов ClickHouse (Async версия с aiochclient)
"""

import pytest
import pytest_asyncio
from datetime import datetime
from aiohttp import ClientSession
from aiochclient import ChClient
from app.db.clickhouse import ClickHouseClient
from app.config import settings


# Модульная фикстура для создания тестовой БД (один раз для всей сессии)
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Создает тестовую БД перед всеми тестами"""
    import asyncio

    async def create_db():
        test_db = "music_recommend_test"
        async with ClientSession() as session:
            url = (
                f"http://{settings.clickhouse_host}:{settings.clickhouse_port}"
            )
            client = ChClient(
                session,
                url=url,
                user=settings.clickhouse_user,
                password=settings.clickhouse_password,
            )
            await client.execute(f"CREATE DATABASE IF NOT EXISTS {test_db}")
            print(f"\n✓ Тестовая БД '{test_db}' готова")

    asyncio.run(create_db())
    yield

    # Очистка после всех тестов
    async def drop_db():
        test_db = "music_recommend_test"
        async with ClientSession() as session:
            url = (
                f"http://{settings.clickhouse_host}:{settings.clickhouse_port}"
            )
            client = ChClient(
                session,
                url=url,
                user=settings.clickhouse_user,
                password=settings.clickhouse_password,
            )
            await client.execute(f"DROP DATABASE IF EXISTS {test_db}")
            print(f"\n✓ Тестовая БД '{test_db}' удалена")

    asyncio.run(drop_db())


@pytest_asyncio.fixture(scope="function")
async def clickhouse_client():
    """
    Создает асинхронный клиент ClickHouse для тестов
    """
    client = ClickHouseClient()

    original_db = settings.clickhouse_database

    try:
        # Используем тестовую БД
        settings.clickhouse_database = "music_recommend_test"
        await client.connect()

        yield client

    finally:
        if client.client:
            await client.disconnect()
        settings.clickhouse_database = original_db


@pytest_asyncio.fixture(scope="function")
async def clean_tables(clickhouse_client):
    """
    Очищает таблицы перед каждым тестом
    """
    tables = [
        "users",
        "tracks",
        "user_track_interactions",
        "user_track_matrix",
    ]

    for table in tables:
        try:
            await clickhouse_client.client.execute(
                f"TRUNCATE TABLE IF EXISTS {table}"
            )
        except Exception:
            pass

    yield

    # Очистка после теста
    for table in tables:
        try:
            await clickhouse_client.client.execute(
                f"TRUNCATE TABLE IF EXISTS {table}"
            )
        except Exception:
            pass


@pytest_asyncio.fixture(scope="function")
async def create_test_schema(clickhouse_client):
    """
    Создает схему БД для тестов
    """
    # Создаем таблицу пользователей
    await clickhouse_client.client.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id UInt32,
            username String,
            email String,
            age UInt8,
            country String,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY user_id
    """
    )

    # Создаем таблицу треков
    await clickhouse_client.client.execute(
        """
        CREATE TABLE IF NOT EXISTS tracks (
            track_id UInt32,
            title String,
            artist String,
            album String,
            genre String,
            duration_seconds UInt16,
            release_year UInt16,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY track_id
    """
    )

    # Создаем таблицу взаимодействий
    await clickhouse_client.client.execute(
        """
        CREATE TABLE IF NOT EXISTS user_track_interactions (
            user_id UInt32,
            track_id UInt32,
            action_type Enum8(
                'play' = 1,
                'like' = 2,
                'dislike' = 3,
                'skip' = 4,
                'add_to_playlist' = 5,
                'share' = 6
            ),
            listen_duration_seconds Nullable(UInt16),
            timestamp DateTime,
            date Date MATERIALIZED toDate(timestamp)
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (user_id, timestamp, track_id)
    """
    )

    # Создаем таблицу матрицы
    await clickhouse_client.client.execute(
        """
        CREATE TABLE IF NOT EXISTS user_track_matrix (
            user_id UInt32,
            track_id UInt32,
            implicit_rating Float32,
            last_interaction DateTime,
            interaction_count UInt16
        ) ENGINE = ReplacingMergeTree(last_interaction)
        ORDER BY (user_id, track_id)
    """
    )

    yield


NOW = datetime.now()


@pytest.fixture
def sample_users():
    """
    Возвращает тестовые данные пользователей
    """
    return [
        [1, "user1", "user1@test.com", 25, "Russia", NOW],
        [2, "user2", "user2@test.com", 30, "USA", NOW],
        [3, "user3", "user3@test.com", 22, "Germany", NOW],
    ]


@pytest.fixture
def sample_tracks():
    """
    Возвращает тестовые данные треков
    """
    return [
        [1, "Track 1", "Artist 1", "Album 1", "Rock", 180, 2020, NOW],
        [2, "Track 2", "Artist 2", "Album 2", "Pop", 200, 2021, NOW],
        [3, "Track 3", "Artist 1", "Album 3", "Rock", 220, 2022, NOW],
    ]


@pytest.fixture
def sample_interactions():
    """
    Возвращает тестовые данные взаимодействий
    """

    return [
        [1, 1, "play", 180, NOW],
        [1, 2, "like", None, NOW],
        [2, 1, "play", 90, NOW],
        [2, 3, "skip", 30, NOW],
        [3, 2, "play", 200, NOW],
    ]
