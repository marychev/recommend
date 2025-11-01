import pytest
from datetime import datetime, timedelta



class TestPerformance:
    """Тесты производительности"""
    
    async def test_bulk_insert_performance(
        self, 
        clickhouse_client, 
        create_test_schema, 
        clean_tables
    ):
        """Тест производительности массовой вставки"""
        import time
        
        # Генерируем большое количество данных
        data = [[i, f"user{i}", f"user{i}@test.com", 25, "Russia"] 
                for i in range(1000)]
        columns = ["user_id", "username", "email", "age", "country"]
        
        start_time = time.time()
        await clickhouse_client.insert("users", data, column_names=columns)
        end_time = time.time()
        
        elapsed = end_time - start_time
        
        # Проверяем, что вставка выполнена быстро (< 2 секунд)
        assert elapsed < 2.0
        
        # Проверяем количество записей
        result = await clickhouse_client.execute_raw("SELECT count() FROM users")
        assert result[0][0] == 1000
    
    async def test_query_performance(
        self, 
        clickhouse_client, 
        create_test_schema, 
        clean_tables
    ):
        """Тест производительности запросов"""
        import time
        
        # Вставляем данные
        data = [[i, f"user{i}", f"user{i}@test.com", 25, "Russia"] 
                for i in range(1000)]
        columns = ["user_id", "username", "email", "age", "country"]
        await clickhouse_client.insert("users", data, column_names=columns)
        
        # Тестируем скорость запроса
        start_time = time.time()
        result = await clickhouse_client.execute_raw(
            "SELECT count() FROM users WHERE age >= 25"
        )
        end_time = time.time()
        
        elapsed = end_time - start_time
        
        # Запрос должен выполниться быстро (< 0.5 секунд)
        assert elapsed < 0.5
        assert result[0][0] == 1000

