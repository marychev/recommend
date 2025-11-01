import pytest


class TestDBSchema:
    """Тесты схемы базы данных"""
    
    def test_db_exists(self, clickhouse_client):
        """Тест существования базы данных"""
        from app.config import settings
        
        result = clickhouse_client.execute(
            "SELECT name FROM system.databases WHERE name = {db:String}",
            parameters={"db": settings.clickhouse_database}
        )
        
        assert len(result.result_rows) == 1
    
    def test_tables_exist(self, clickhouse_client, create_test_schema):
        """Тест существования всех необходимых таблиц"""
        from app.config import settings
        
        expected_tables = [
            "users",
            "tracks",
            "user_track_interactions",
            "user_track_matrix"
        ]
        
        for table in expected_tables:
            result = clickhouse_client.execute(
                f"EXISTS TABLE {settings.clickhouse_database}.{table}"
            )
            assert result.result_rows[0][0] == 1, f"Таблица {table} не существует"
    
    def test_users_table_structure(self, clickhouse_client, create_test_schema):
        """Тест структуры таблицы users"""
        result = clickhouse_client.execute(
            "DESCRIBE TABLE users"
        )
        
        columns = {row[0]: row[1] for row in result.result_rows}
        
        assert "user_id" in columns
        assert "username" in columns
        assert "email" in columns
        assert "age" in columns
        assert "country" in columns
        assert "created_at" in columns
        
        assert "UInt32" in columns["user_id"]
        assert "String" in columns["username"]
    
    def test_tracks_table_structure(self, clickhouse_client, create_test_schema):
        """Тест структуры таблицы tracks"""
        result = clickhouse_client.execute(
            "DESCRIBE TABLE tracks"
        )
        
        columns = {row[0]: row[1] for row in result.result_rows}
        
        assert "track_id" in columns
        assert "title" in columns
        assert "artist" in columns
        assert "album" in columns
        assert "genre" in columns
        assert "duration_seconds" in columns
        assert "release_year" in columns
        
        assert "UInt32" in columns["track_id"]
        assert "String" in columns["title"]
    
    def test_interactions_table_structure(
        self, 
        clickhouse_client, 
        create_test_schema
    ):
        """Тест структуры таблицы user_track_interactions"""
        result = clickhouse_client.execute(
            "DESCRIBE TABLE user_track_interactions"
        )
        
        columns = {row[0]: row[1] for row in result.result_rows}
        
        assert "user_id" in columns
        assert "track_id" in columns
        assert "action_type" in columns
        assert "listen_duration_seconds" in columns
        assert "timestamp" in columns
        
        assert "Enum8" in columns["action_type"]
        assert "DateTime" in columns["timestamp"]
