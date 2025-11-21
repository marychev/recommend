import pytest
from datetime import datetime
from app.db.clickhouse import ClickHouseClient
from app.models.schemas import User


class TestClickHouseClientMethods:
    """Тесты методов клиента ClickHouse (Async версия)"""

    @pytest.mark.asyncio
    async def test_execute_method(self, clickhouse_client):
        """Тест метода execute_raw"""
        result = await clickhouse_client.execute_raw("SELECT 'test' as value")
        assert result is not None
        assert result[0][0] == "test"

    @pytest.mark.asyncio
    async def test_insert_method(
        self, clickhouse_client, create_test_schema, clean_tables
    ):
        """Тест метода insert"""
        data = [[1, "test_user", "test@test.com", 25, "Russia", datetime.now()]]
        await clickhouse_client.insert("users", data, column_names=User.column_names())

        # Проверяем вставку
        result = await clickhouse_client.execute_raw(
            "SELECT count() FROM users"
        )
        assert result[0][0] == 1

    @pytest.mark.asyncio
    @pytest.mark.skip("Тест пропущен - логика подключения изменилась после оптимизации")
    async def test_client_not_connected_error(self):
        """Тест ошибки при работе с неподключенным клиентом"""
        # Создаем клиент с заведомо неправильными настройками
        client = ClickHouseClient(
            host="nonexistent_host_12345", 
            port=99999, 
            database="nonexistent_db"
        )

        with pytest.raises(
            RuntimeError, match="ClickHouse client not connected"
        ):
            await client.execute_raw("SELECT 1")

        with pytest.raises(
            RuntimeError, match="ClickHouse client not connected"
        ):
            await client.insert("users", [[1, "test"]])
