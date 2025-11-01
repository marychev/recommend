import pytest
from app.db.clickhouse import ClickHouseClient
from app.config import settings


class TestClickHouseConnection:
    """Тесты подключения к ClickHouse"""
    
    def test_connection_success(self, clickhouse_client):
        """Тест успешного подключения"""
        assert clickhouse_client.is_connected()
    
    def test_connection_parameters(self):
        """Тест параметров подключения из конфигурации"""
        assert settings.clickhouse_host is not None
        assert settings.clickhouse_port > 0
        assert settings.clickhouse_database is not None
    
    def test_simple_query(self, clickhouse_client):
        """Тест выполнения простого запроса"""
        result = clickhouse_client.execute("SELECT 1 as num")
        assert result is not None
        assert len(result.result_rows) == 1
        assert result.result_rows[0][0] == 1
    
    def test_database_exists(self, clickhouse_client):
        """Тест существования тестовой базы данных"""
        result = clickhouse_client.execute(
            f"SELECT name FROM system.databases WHERE name = '{settings.clickhouse_database}'"
        )
        assert len(result.result_rows) == 1
        assert result.result_rows[0][0] == settings.clickhouse_database
    
    def test_connection_with_wrong_credentials(self):
        """Тест подключения с неправильными учетными данными"""
        import clickhouse_connect
        
        with pytest.raises(Exception):
            clickhouse_connect.get_client(
                host=settings.clickhouse_host,
                port=settings.clickhouse_port,
                username="wrong_user",
                password="wrong_password"
            )
    
    def test_multiple_queries(self, clickhouse_client):
        """Тест выполнения нескольких запросов подряд"""
        results = []
        for i in range(5):
            result = clickhouse_client.execute(f"SELECT {i} as num")
            results.append(result.result_rows[0][0])
        
        assert results == [0, 1, 2, 3, 4]
    
    def test_query_with_parameters(self, clickhouse_client):
        """Тест запроса с параметрами"""
        result = clickhouse_client.execute(
            "SELECT {value:UInt32} as num",
            parameters={"value": 42}
        )
        assert result.result_rows[0][0] == 42
    
    def test_disconnect_and_reconnect(self, clickhouse_client):
        """Тест отключения и переподключения"""
        # Отключаемся
        clickhouse_client.disconnect()
        assert not clickhouse_client.is_connected()
        
        # Переподключаемся
        clickhouse_client.connect()
        assert clickhouse_client.is_connected()
        
        # Проверяем работоспособность
        result = clickhouse_client.execute("SELECT 1")
        assert result.result_rows[0][0] == 1
