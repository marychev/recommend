"""
Тесты операций с данными в ClickHouse
"""
import pytest
from datetime import datetime, timedelta


class TestComplexQueries:
    """Тесты сложных запросов"""
    
    async def test_join_users_and_interactions(
        self, 
        clickhouse_client, 
        create_test_schema, 
        clean_tables,
        sample_users,
        sample_tracks,
        sample_interactions
    ):
        """Тест JOIN запроса пользователей и взаимодействий"""
        # Подготовка данных
        await clickhouse_client.insert(
            "users", 
            sample_users, 
            column_names=["user_id", "username", "email", "age", "country"]
        )
        await clickhouse_client.insert(
            "tracks", 
            sample_tracks, 
            column_names=[
                "track_id", "title", "artist", "album", 
                "genre", "duration_seconds", "release_year"
            ]
        )
        await clickhouse_client.insert(
            "user_track_interactions",
            sample_interactions,
            column_names=[
                "user_id", "track_id", "action_type",
                "listen_duration_seconds", "timestamp"
            ]
        )
        
        # JOIN запрос
        result = await clickhouse_client.execute_raw("""
            SELECT 
                u.username,
                count() as interaction_count
            FROM user_track_interactions i
            JOIN users u ON i.user_id = u.user_id
            GROUP BY u.username
            ORDER BY interaction_count DESC
        """)
        
        assert len(result) == 3
        assert result[0][1] == 2  # max interactions
    
    async def test_join_tracks_and_interactions(
        self, 
        clickhouse_client, 
        create_test_schema, 
        clean_tables,
        sample_users,
        sample_tracks,
        sample_interactions
    ):
        """Тест JOIN запроса треков и взаимодействий"""
        # Подготовка данных
        await clickhouse_client.insert(
            "users", 
            sample_users, 
            column_names=["user_id", "username", "email", "age", "country"]
        )
        await clickhouse_client.insert(
            "tracks", 
            sample_tracks, 
            column_names=[
                "track_id", "title", "artist", "album", 
                "genre", "duration_seconds", "release_year"
            ]
        )
        await clickhouse_client.insert(
            "user_track_interactions",
            sample_interactions,
            column_names=[
                "user_id", "track_id", "action_type",
                "listen_duration_seconds", "timestamp"
            ]
        )
        
        # JOIN запрос
        result = await clickhouse_client.execute_raw("""
            SELECT 
                t.title,
                t.artist,
                count() as play_count
            FROM user_track_interactions i
            JOIN tracks t ON i.track_id = t.track_id
            WHERE i.action_type = 'play'
            GROUP BY t.title, t.artist
            ORDER BY play_count DESC
        """)
        
        # 2 уникальных трека: Track 1 (2 раза), Track 2 (1 раз)
        assert len(result) == 2
        # Проверяем что Track 1 имеет больше прослушиваний
        assert result[0][2] == 2  # Track 1 - 2 plays
        assert result[1][2] == 1  # Track 2 - 1 play
    
    async def test_window_functions(
        self, 
        clickhouse_client, 
        create_test_schema, 
        clean_tables,
        sample_users,
        sample_tracks,
        sample_interactions
    ):
        """Тест оконных функций"""
        # Подготовка данных
        await clickhouse_client.insert(
            "users", 
            sample_users, 
            column_names=["user_id", "username", "email", "age", "country"]
        )
        await clickhouse_client.insert(
            "tracks", 
            sample_tracks, 
            column_names=[
                "track_id", "title", "artist", "album", 
                "genre", "duration_seconds", "release_year"
            ]
        )
        await clickhouse_client.insert(
            "user_track_interactions",
            sample_interactions,
            column_names=[
                "user_id", "track_id", "action_type",
                "listen_duration_seconds", "timestamp"
            ]
        )
        
        # Запрос с оконной функцией
        result = await clickhouse_client.execute_raw("""
            SELECT 
                user_id,
                track_id,
                row_number() OVER (PARTITION BY user_id ORDER BY timestamp) as rn
            FROM user_track_interactions
            ORDER BY user_id, rn
        """)
        
        assert len(result) == len(sample_interactions)

