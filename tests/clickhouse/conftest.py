"""
Фикстуры для тестов ClickHouse
"""
import pytest
from app.db.clickhouse import ClickHouseClient
from app.config import settings


@pytest.fixture(scope="session")
def clickhouse_client():
    """
    Создает клиент ClickHouse для тестов
    """
    # Сохраняем оригинальную БД
    original_db = settings.clickhouse_database
    test_db = "music_recommend_test"
    
    # Сначала подключаемся к default БД для создания тестовой
    client = ClickHouseClient()
    
    try:
        # Подключаемся без указания БД
        settings.clickhouse_database = "default"
        client.connect()
        
        # Создаем тестовую БД
        client.client.command(f"CREATE DATABASE IF NOT EXISTS {test_db}")
        print(f"✓ Тестовая база данных '{test_db}' создана")
        
        # Переподключаемся к тестовой БД
        client.disconnect()
        settings.clickhouse_database = test_db
        client.connect()
        
        yield client
        
    finally:
        # Очищаем тестовую БД после всех тестов
        try:
            client.client.command(f"DROP DATABASE IF EXISTS {test_db}")
            print(f"✓ Тестовая база данных '{test_db}' удалена")
        except Exception as e:
            print(f"⚠ Не удалось удалить тестовую БД: {e}")
        
        client.disconnect()
        settings.clickhouse_database = original_db


@pytest.fixture(scope="function")
def clean_tables(clickhouse_client):
    """
    Очищает таблицы перед каждым тестом
    """
    tables = ["users", "tracks", "user_track_interactions", "user_track_matrix"]
    
    for table in tables:
        try:
            clickhouse_client.client.command(f"TRUNCATE TABLE IF EXISTS {table}")
        except Exception:
            pass
    
    yield
    
    # Очистка после теста
    for table in tables:
        try:
            clickhouse_client.client.command(f"TRUNCATE TABLE IF EXISTS {table}")
        except Exception:
            pass


@pytest.fixture(scope="session")
def create_test_schema(clickhouse_client):
    """
    Создает схему БД для тестов
    """
    # Создаем таблицу пользователей
    clickhouse_client.client.command("""
        CREATE TABLE IF NOT EXISTS users (
            user_id UInt32,
            username String,
            email String,
            age UInt8,
            country String,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY user_id
    """)
    
    # Создаем таблицу треков
    clickhouse_client.client.command("""
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
    """)
    
    # Создаем таблицу взаимодействий
    clickhouse_client.client.command("""
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
    """)
    
    # Создаем таблицу матрицы
    clickhouse_client.client.command("""
        CREATE TABLE IF NOT EXISTS user_track_matrix (
            user_id UInt32,
            track_id UInt32,
            implicit_rating Float32,
            last_interaction DateTime,
            interaction_count UInt16
        ) ENGINE = ReplacingMergeTree(last_interaction)
        ORDER BY (user_id, track_id)
    """)
    
    yield
    
    # Схема будет удалена вместе с БД в clickhouse_client fixture


@pytest.fixture
def sample_users():
    """
    Возвращает тестовые данные пользователей
    """
    return [
        [1, "user1", "user1@test.com", 25, "Russia"],
        [2, "user2", "user2@test.com", 30, "USA"],
        [3, "user3", "user3@test.com", 22, "Germany"],
    ]


@pytest.fixture
def sample_tracks():
    """
    Возвращает тестовые данные треков
    """
    return [
        [1, "Track 1", "Artist 1", "Album 1", "Rock", 180, 2020],
        [2, "Track 2", "Artist 2", "Album 2", "Pop", 200, 2021],
        [3, "Track 3", "Artist 1", "Album 3", "Rock", 220, 2022],
    ]


@pytest.fixture
def sample_interactions():
    """
    Возвращает тестовые данные взаимодействий
    """
    from datetime import datetime
    now = datetime.now()
    
    return [
        [1, 1, "play", 180, now],
        [1, 2, "like", None, now],
        [2, 1, "play", 90, now],
        [2, 3, "skip", 30, now],
        [3, 2, "play", 200, now],
    ]

