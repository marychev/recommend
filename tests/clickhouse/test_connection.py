import pytest

from asynch import connect

from app.config import settings


class TestClickHouseConnection:
    """Тесты подключения к ClickHouse (Async версия)"""

    @pytest.mark.asyncio
    async def test_connection_success(self, clickhouse_client):
        """Тест успешного подключения"""
        assert await clickhouse_client.is_connected()

    def test_connection_parameters(self):
        """Тест параметров подключения из конфигурации"""
        assert settings.clickhouse_host is not None
        assert settings.clickhouse_port > 0
        assert settings.clickhouse_database is not None

    @pytest.mark.asyncio
    async def test_simple_query(self, clickhouse_client):
        """Тест выполнения простого запроса"""
        result = await clickhouse_client.execute_raw("SELECT 1 as num")
        assert result is not None
        assert len(result) == 1
        assert result[0][0] == 1

    @pytest.mark.asyncio
    async def test_database_exists(self, clickhouse_client):
        """Тест существования тестовой базы данных"""
        result = await clickhouse_client.execute_raw(
            f"SELECT name FROM system.databases WHERE name = '{settings.clickhouse_database}'"
        )
        assert len(result) == 1
        assert result[0][0] == settings.clickhouse_database

    @pytest.mark.asyncio
    async def test_connection_with_wrong_credentials(self):
        """Тест подключения с неправильными учетными данными"""

        with pytest.raises(Exception):
            await connect(
                host=settings.clickhouse_host,
                port=settings.clickhouse_port,
                user="wrong_user",
                password="wrong_password",
            )

    @pytest.mark.asyncio
    async def test_multiple_queries(self, clickhouse_client):
        """Тест выполнения нескольких запросов подряд"""
        results = []
        for i in range(5):
            result = await clickhouse_client.execute_raw(f"SELECT {i} as num")
            results.append(result[0][0])

        assert results == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_query_with_parameters(self, clickhouse_client):
        """Тест запроса с параметрами"""
        test_value = 42
        result = await clickhouse_client.execute_raw(
            f"SELECT {test_value} as num"
        )
        assert result[0][0] == test_value

    @pytest.mark.asyncio
    async def test_disconnect_and_reconnect(self, clickhouse_client):
        """Тест отключения и переподключения"""
        # Проверяем, что подключены
        assert await clickhouse_client.is_connected()

        # Отключаемся
        await clickhouse_client.disconnect()
        assert not await clickhouse_client.is_connected()

        # Переподключаемся
        await clickhouse_client.connect()
        assert await clickhouse_client.is_connected()
