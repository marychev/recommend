import pytest


class TestConstraintsAndValidation:
    """Тесты ограничений и валидации данных"""
    
    async def test_enum_constraint(
        self, 
        clickhouse_client, 
        create_test_schema,
        clean_tables,
        sample_users,
        sample_tracks
    ):
        """Тест ENUM ограничения для action_type"""
        from datetime import datetime
        
        # Вставляем пользователей и треки
        await clickhouse_client.insert(
            "users", 
            sample_users, 
            column_names=["user_id", "username", "email", "age", "country"]
        )
        await clickhouse_client.insert(
            "tracks", 
            sample_tracks, 
            column_names=[
                "track_id", "title", "artist", "album", 
                "genre", "duration_seconds", "release_year"
            ]
        )
        
        # Тест валидных значений ENUM
        valid_actions = ["play", "like", "dislike", "skip", "add_to_playlist", "share"]
        
        for action in valid_actions:
            valid_interaction = [[1, 1, action, 180, datetime.now()]]
            # Валидные значения должны вставляться успешно
            await clickhouse_client.insert(
                "user_track_interactions",
                valid_interaction,
                column_names=[
                    "user_id", "track_id", "action_type",
                    "listen_duration_seconds", "timestamp"
                ]
            )
        
        # Проверяем что все валидные значения вставились
        result = await clickhouse_client.execute_raw(
            "SELECT count() FROM user_track_interactions"
        )
        assert result[0][0] == len(valid_actions)
        
        # Попытка вставить через SQL с неправильным значением
        # должна вызвать ошибку
        with pytest.raises(Exception):
            await clickhouse_client.execute_raw("""
                INSERT INTO user_track_interactions 
                (user_id, track_id, action_type, listen_duration_seconds, timestamp)
                VALUES (1, 1, 'invalid_action', 180, now())
            """)

