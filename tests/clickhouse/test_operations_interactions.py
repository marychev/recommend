import pytest
from datetime import datetime, timedelta


class TestInteractionsOperations:
    """Тесты операций с таблицей взаимодействий"""
    
    def test_insert(
        self, 
        clickhouse_client, 
        create_test_schema, 
        clean_tables, 
        sample_users,
        sample_tracks,
        sample_interactions
    ):
        """Тест вставки взаимодействий"""
        # Сначала вставляем пользователей и треки
        clickhouse_client.insert(
            "users", 
            sample_users, 
            column_names=["user_id", "username", "email", "age", "country"]
        )
        clickhouse_client.insert(
            "tracks", 
            sample_tracks, 
            column_names=[
                "track_id", "title", "artist", "album", 
                "genre", "duration_seconds", "release_year"
            ]
        )
        
        # Вставляем взаимодействия
        clickhouse_client.insert(
            "user_track_interactions",
            sample_interactions,
            column_names=[
                "user_id", "track_id", "action_type",
                "listen_duration_seconds", "timestamp"
            ]
        )
        
        result = clickhouse_client.execute(
            "SELECT count() FROM user_track_interactions"
        )
        assert result.result_rows[0][0] == len(sample_interactions)
    
    def test_select_by_user(
        self, 
        clickhouse_client, 
        create_test_schema, 
        clean_tables,
        sample_users,
        sample_tracks,
        sample_interactions
    ):
        """Тест выборки взаимодействий пользователя"""
        # Подготовка данных
        clickhouse_client.insert(
            "users", 
            sample_users, 
            column_names=["user_id", "username", "email", "age", "country"]
        )
        clickhouse_client.insert(
            "tracks", 
            sample_tracks, 
            column_names=[
                "track_id", "title", "artist", "album", 
                "genre", "duration_seconds", "release_year"
            ]
        )
        clickhouse_client.insert(
            "user_track_interactions",
            sample_interactions,
            column_names=[
                "user_id", "track_id", "action_type",
                "listen_duration_seconds", "timestamp"
            ]
        )
        
        # Проверка
        result = clickhouse_client.execute(
            "SELECT count() FROM user_track_interactions WHERE user_id = 1"
        )
        assert result.result_rows[0][0] == 2
    
    def test_aggregation(
        self, 
        clickhouse_client, 
        create_test_schema, 
        clean_tables,
        sample_users,
        sample_tracks,
        sample_interactions
    ):
        """Тест агрегации взаимодействий"""
        # Подготовка данных
        clickhouse_client.insert(
            "users", 
            sample_users, 
            column_names=["user_id", "username", "email", "age", "country"]
        )
        clickhouse_client.insert(
            "tracks", 
            sample_tracks, 
            column_names=[
                "track_id", "title", "artist", "album", 
                "genre", "duration_seconds", "release_year"
            ]
        )
        clickhouse_client.insert(
            "user_track_interactions",
            sample_interactions,
            column_names=[
                "user_id", "track_id", "action_type",
                "listen_duration_seconds", "timestamp"
            ]
        )
        
        # Группировка по пользователям
        result = clickhouse_client.execute("""
            SELECT user_id, count() as interaction_count 
            FROM user_track_interactions 
            GROUP BY user_id 
            ORDER BY user_id
        """)
        
        assert len(result.result_rows) == 3
        assert result.result_rows[0][1] == 2  # user 1 has 2 interactions
        assert result.result_rows[1][1] == 2  # user 2 has 2 interactions
        assert result.result_rows[2][1] == 1  # user 3 has 1 interaction

