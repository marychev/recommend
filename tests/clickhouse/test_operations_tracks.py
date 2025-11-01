import pytest
from datetime import datetime, timedelta


class TestTracksOperations:
    """Тесты операций с таблицей треков"""
    
    def test_insert_tracks(
        self, 
        clickhouse_client, 
        create_test_schema, 
        clean_tables, 
        sample_tracks
    ):
        """Тест вставки треков"""
        columns = [
            "track_id", "title", "artist", "album", 
            "genre", "duration_seconds", "release_year"
        ]
        
        clickhouse_client.insert("tracks", sample_tracks, column_names=columns)
        
        result = clickhouse_client.execute("SELECT count() FROM tracks")
        assert result.result_rows[0][0] == len(sample_tracks)
    
    def test_select_tracks_by_genre(
        self, 
        clickhouse_client, 
        create_test_schema, 
        clean_tables, 
        sample_tracks
    ):
        """Тест выборки треков по жанру"""
        columns = [
            "track_id", "title", "artist", "album", 
            "genre", "duration_seconds", "release_year"
        ]
        clickhouse_client.insert("tracks", sample_tracks, column_names=columns)
        
        result = clickhouse_client.execute(
            "SELECT title FROM tracks WHERE genre = 'Rock' ORDER BY track_id"
        )
        
        assert len(result.result_rows) == 2
        assert result.result_rows[0][0] == "Track 1"
        assert result.result_rows[1][0] == "Track 3"
    
    def test_select_tracks_by_artist(
        self, 
        clickhouse_client, 
        create_test_schema, 
        clean_tables, 
        sample_tracks
    ):
        """Тест выборки треков по исполнителю"""
        columns = [
            "track_id", "title", "artist", "album", 
            "genre", "duration_seconds", "release_year"
        ]
        clickhouse_client.insert("tracks", sample_tracks, column_names=columns)
        
        result = clickhouse_client.execute(
            "SELECT count() FROM tracks WHERE artist = 'Artist 1'"
        )
        
        assert result.result_rows[0][0] == 2
