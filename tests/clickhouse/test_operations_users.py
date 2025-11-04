import pytest
from datetime import datetime, timedelta


class TestUsersOperations:
    """Тесты операций с таблицей пользователей"""

    async def test_insert_single_user(
        self, clickhouse_client, create_test_schema, clean_tables
    ):
        """Тест вставки одного пользователя"""
        data = [[1, "john_doe", "john@test.com", 25, "Russia"]]
        columns = ["user_id", "username", "email", "age", "country"]

        await clickhouse_client.insert("users", data, column_names=columns)

        result = await clickhouse_client.execute_raw(
            "SELECT user_id, username, email FROM users WHERE user_id = 1"
        )

        assert len(result) == 1
        assert result[0][0] == 1
        assert result[0][1] == "john_doe"
        assert result[0][2] == "john@test.com"

    async def test_insert_multiple_users(
        self, clickhouse_client, create_test_schema, clean_tables, sample_users
    ):
        """Тест вставки нескольких пользователей"""
        columns = ["user_id", "username", "email", "age", "country"]

        await clickhouse_client.insert(
            "users", sample_users, column_names=columns
        )

        result = await clickhouse_client.execute_raw(
            "SELECT count() FROM users"
        )
        assert result[0][0] == len(sample_users)

    async def test_select_users_with_filter(
        self, clickhouse_client, create_test_schema, clean_tables, sample_users
    ):
        """Тест выборки пользователей с фильтром"""
        columns = ["user_id", "username", "email", "age", "country"]
        await clickhouse_client.insert(
            "users", sample_users, column_names=columns
        )

        result = await clickhouse_client.execute_raw(
            "SELECT username FROM users WHERE age >= 25 ORDER BY age"
        )

        assert len(result) == 2
        assert result[0][0] == "user1"
        assert result[1][0] == "user2"

    async def test_select_users_with_aggregation(
        self, clickhouse_client, create_test_schema, clean_tables, sample_users
    ):
        """Тест агрегирующего запроса"""
        columns = ["user_id", "username", "email", "age", "country"]
        await clickhouse_client.insert(
            "users", sample_users, column_names=columns
        )

        result = await clickhouse_client.execute_raw(
            "SELECT avg(age) as avg_age, count() as cnt FROM users"
        )

        assert result[0][1] == 3  # count
        assert result[0][0] == pytest.approx(25.67, rel=0.1)  # avg
