import pytest


class TestDBSchema:
    """Тесты схемы базы данных"""
    
    async def test_db_exists(self, clickhouse_client):
        """Тест существования базы данных"""
        from app.config import settings
        
        result = await clickhouse_client.execute_raw(
            f"SELECT name FROM system.databases WHERE name = '{settings.clickhouse_database}'"
        )
        
        assert len(result) == 1
    
    async def test_tables_exist(self, clickhouse_client, create_test_schema):
        """Тест существования всех необходимых таблиц"""
        from app.config import settings
        
        expected_tables = [
            "users",
            "tracks",
            "user_track_interactions",
            "user_track_matrix"
        ]
        
        for table in expected_tables:
            result = await clickhouse_client.execute_raw(
                f"EXISTS TABLE {settings.clickhouse_database}.{table}"
            )
            assert result[0][0] == 1, f"Таблица {table} не существует"
    
    async def test_users_table_structure(self, clickhouse_client, create_test_schema):
        """Тест структуры таблицы users"""
        result = await clickhouse_client.execute_raw(
            "DESCRIBE TABLE users"
        )
        
        columns = {row[0]: row[1] for row in result}
        
        assert "user_id" in columns
        assert "username" in columns
        assert "email" in columns
        assert "age" in columns
        assert "country" in columns
        assert "created_at" in columns
        
        assert "UInt32" in columns["user_id"]
        assert "String" in columns["username"]
    
    async def test_tracks_table_structure(self, clickhouse_client, create_test_schema):
        """Тест структуры таблицы tracks"""
        result = await clickhouse_client.execute_raw(
            "DESCRIBE TABLE tracks"
        )
        
        columns = {row[0]: row[1] for row in result}
        
        assert "track_id" in columns
        assert "title" in columns
        assert "artist" in columns
        assert "album" in columns
        assert "genre" in columns
        assert "duration_seconds" in columns
        assert "release_year" in columns
        
        assert "UInt32" in columns["track_id"]
        assert "String" in columns["title"]
    
    async def test_interactions_table_structure(
        self, 
        clickhouse_client, 
        create_test_schema
    ):
        """Тест структуры таблицы user_track_interactions"""
        result = await clickhouse_client.execute_raw(
            "DESCRIBE TABLE user_track_interactions"
        )
        
        columns = {row[0]: row[1] for row in result}
        
        assert "user_id" in columns
        assert "track_id" in columns
        assert "action_type" in columns
        assert "listen_duration_seconds" in columns
        assert "timestamp" in columns
        
        assert "Enum8" in columns["action_type"]
        assert "DateTime" in columns["timestamp"]
