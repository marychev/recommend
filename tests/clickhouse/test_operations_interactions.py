from tests.clickhouse.test_complex_queries import (
    USER_COLUMN_NAMES,
    TRACK_COLUMN_NAMES,
    INTERACTION_COLUMN_NAMES,
)


class TestInteractionsOperations:
    """Тесты операций с таблицей взаимодействий"""

    async def test_insert(
        self,
        clickhouse_client,
        create_test_schema,
        clean_tables,
        sample_users,
        sample_tracks,
        sample_interactions,
    ):
        """Тест вставки взаимодействий"""
        # Сначала вставляем пользователей и треки
        await clickhouse_client.insert(
            "users",
            sample_users,
            column_names=USER_COLUMN_NAMES,
        )
        await clickhouse_client.insert(
            "tracks",
            sample_tracks,
            column_names=TRACK_COLUMN_NAMES,
        )

        # Вставляем взаимодействия
        await clickhouse_client.insert(
            "user_track_interactions",
            sample_interactions,
            column_names=INTERACTION_COLUMN_NAMES,
        )

        result = await clickhouse_client.execute_raw(
            "SELECT count() FROM user_track_interactions"
        )
        assert result[0][0] == len(sample_interactions)

    async def test_select_by_user(
        self,
        clickhouse_client,
        create_test_schema,
        clean_tables,
        sample_users,
        sample_tracks,
        sample_interactions,
    ):
        """Тест выборки взаимодействий пользователя"""
        # Подготовка данных
        await clickhouse_client.insert(
            "users",
            sample_users,
            column_names=USER_COLUMN_NAMES,
        )
        await clickhouse_client.insert(
            "tracks",
            sample_tracks,
            column_names=TRACK_COLUMN_NAMES,
        )
        await clickhouse_client.insert(
            "user_track_interactions",
            sample_interactions,
            column_names=INTERACTION_COLUMN_NAMES,
        )

        # Проверка
        result = await clickhouse_client.execute_raw(
            "SELECT count() FROM user_track_interactions WHERE user_id = 1"
        )
        assert result[0][0] == 2

    async def test_aggregation(
        self,
        clickhouse_client,
        create_test_schema,
        clean_tables,
        sample_users,
        sample_tracks,
        sample_interactions,
    ):
        """Тест агрегации взаимодействий"""
        # Подготовка данных
        await clickhouse_client.insert(
            "users",
            sample_users,
            column_names=USER_COLUMN_NAMES,
        )
        await clickhouse_client.insert(
            "tracks",
            sample_tracks,
            column_names=TRACK_COLUMN_NAMES,
        )
        await clickhouse_client.insert(
            "user_track_interactions",
            sample_interactions,
            column_names=INTERACTION_COLUMN_NAMES,
        )

        # Группировка по пользователям
        result = await clickhouse_client.execute_raw(
            """
            SELECT user_id, count() as interaction_count 
            FROM user_track_interactions 
            GROUP BY user_id 
            ORDER BY user_id
        """
        )

        assert len(result) == 3
        assert result[0][1] == 2  # user 1 has 2 interactions
        assert result[1][1] == 2  # user 2 has 2 interactions
        assert result[2][1] == 1  # user 3 has 1 interaction
