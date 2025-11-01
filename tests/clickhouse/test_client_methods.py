import pytest
from app.db.clickhouse import ClickHouseClient


class TestClickHouseClientMethods:
    """Тесты методов клиента ClickHouse"""
    
    def test_execute_method(self, clickhouse_client):
        """Тест метода execute"""
        result = clickhouse_client.execute("SELECT 'test' as value")
        assert result is not None
        assert result.result_rows[0][0] == "test"
    
    def test_insert_method(self, clickhouse_client, create_test_schema, clean_tables):
        """Тест метода insert"""
        data = [[1, "test_user", "test@test.com", 25, "Russia"]]
        columns = ["user_id", "username", "email", "age", "country"]
        
        clickhouse_client.insert("users", data, column_names=columns)
        
        # Проверяем вставку
        result = clickhouse_client.execute("SELECT count() FROM users")
        assert result.result_rows[0][0] == 1
    
    def test_client_not_connected_error(self):
        """Тест ошибки при работе с неподключенным клиентом"""
        client = ClickHouseClient()
        
        with pytest.raises(RuntimeError, match="ClickHouse client not connected"):
            client.execute("SELECT 1")
        
        with pytest.raises(RuntimeError, match="ClickHouse client not connected"):
            client.insert("users", [[1, "test"]])

