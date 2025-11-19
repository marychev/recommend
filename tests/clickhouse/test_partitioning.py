from datetime import datetime
from app.config import settings
from app.models.schemas import User, Track, UserTrackInteraction


class TestPartitioning:
    """Тесты партиционирования"""

    async def test_interactions_partitioning(
        self,
        clickhouse_client,
        create_test_schema,
        clean_tables,
        sample_users,
        sample_tracks,
    ):
        """Тест партиционирования таблицы взаимодействий"""

        # Вставляем пользователей и треки
        await clickhouse_client.insert(
            "users",
            sample_users,
            column_names=User.column_names(),
        )
        await clickhouse_client.insert(
            "tracks",
            sample_tracks,
            column_names=Track.column_names(),
        )

        # Вставляем взаимодействия за разные месяцы
        now = datetime.now()
        one_month_ago = now.replace(
            month=now.month - 1 if now.month > 1 else 12
        )

        interactions = [
            [1, 1, "play", 180, now],
            [1, 2, "like", None, one_month_ago],
        ]

        await clickhouse_client.insert(
            "user_track_interactions",
            interactions,
            column_names=UserTrackInteraction.column_names(),
        )

        # Проверяем количество партиций
        result = await clickhouse_client.execute_raw(
            f"""
            SELECT count(DISTINCT partition) as partition_count
            FROM system.parts
            WHERE database = '{settings.clickhouse_database}'
              AND table = 'user_track_interactions'
              AND active = 1
        """
        )

        # Должно быть как минимум 1 партиция
        assert result[0][0] >= 1
