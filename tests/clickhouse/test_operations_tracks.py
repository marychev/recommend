from tests.clickhouse.test_complex_queries import TRACK_COLUMN_NAMES


class TestTracksOperations:
    """Тесты операций с таблицей треков"""

    async def test_insert_tracks(
        self,
        clickhouse_client,
        create_test_schema,
        clean_tables,
        sample_tracks,
    ):
        """Тест вставки треков"""
        await clickhouse_client.insert(
            "tracks", sample_tracks, column_names=TRACK_COLUMN_NAMES
        )

        result = await clickhouse_client.execute_raw(
            "SELECT count() FROM tracks"
        )
        assert result[0][0] == len(sample_tracks)

    async def test_select_tracks_by_genre(
        self,
        clickhouse_client,
        create_test_schema,
        clean_tables,
        sample_tracks,
    ):
        """Тест выборки треков по жанру"""
        await clickhouse_client.insert(
            "tracks", sample_tracks, column_names=TRACK_COLUMN_NAMES
        )

        result = await clickhouse_client.execute_raw(
            "SELECT title FROM tracks WHERE genre = 'Rock' ORDER BY track_id"
        )

        assert len(result) == 2
        assert result[0][0] == "Track 1"
        assert result[1][0] == "Track 3"

    async def test_select_tracks_by_artist(
        self,
        clickhouse_client,
        create_test_schema,
        clean_tables,
        sample_tracks,
    ):
        """Тест выборки треков по исполнителю"""
        await clickhouse_client.insert(
            "tracks", sample_tracks, column_names=TRACK_COLUMN_NAMES
        )

        result = await clickhouse_client.execute_raw(
            "SELECT count() FROM tracks WHERE artist = 'Artist 1'"
        )

        assert result[0][0] == 2
