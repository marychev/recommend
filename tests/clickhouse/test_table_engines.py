class TestTableEngines:
    """Тесты движков таблиц"""
    
    def test_users_table_engine(self, clickhouse_client, create_test_schema):
        """Тест движка таблицы users"""
        from app.config import settings
        
        result = clickhouse_client.execute(f"""
            SELECT engine 
            FROM system.tables 
            WHERE database = '{settings.clickhouse_database}' 
              AND name = 'users'
        """)
        
        assert len(result.result_rows) == 1
        assert "MergeTree" in result.result_rows[0][0]
    
    def test_matrix_table_engine(self, clickhouse_client, create_test_schema):
        """Тест движка таблицы user_track_matrix"""
        from app.config import settings
        
        result = clickhouse_client.execute(f"""
            SELECT engine 
            FROM system.tables 
            WHERE database = '{settings.clickhouse_database}' 
              AND name = 'user_track_matrix'
        """)
        
        assert len(result.result_rows) == 1
        assert "ReplacingMergeTree" in result.result_rows[0][0]

