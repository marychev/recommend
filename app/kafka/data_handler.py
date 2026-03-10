"""
Универсальный обработчик данных из Kafka для записи в ClickHouse

Обрабатывает:
- users - пользователи
- tracks - треки
- events - события взаимодействий

Все данные записываются в ClickHouse батчами для оптимизации.
Использует переиспользуемый BatchBuffer для буферизации.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.db.clickhouse import get_clickhouse_client
from app.models.schemas import User, Track, UserTrackInteraction
from app.services.cache_redis_client import get_redis_client
from app.kafka.event_handler import update_analytics_metrics
from app.utils.batch_buffer import BatchBuffer
from app.kafka.constants import (
    DATA_HANDLER_BATCH_SIZE,
    DATA_HANDLER_FLUSH_INTERVAL,
)

logger = logging.getLogger(__name__)


class KafkaDataHandler:
    """Обработчик данных из Kafka с батчингом для ClickHouse"""

    # Маппинг имен буферов на реальные имена таблиц в ClickHouse
    BUFFER_TO_TABLE = {
        'users': 'users',
        'tracks': 'tracks',
        'events': 'user_track_interactions',
    }

    # Маппинг буферов на column_names для INSERT
    BUFFER_TO_COLUMNS = {
        'users': User.column_names,
        'tracks': Track.column_names,
        'events': UserTrackInteraction.column_names,
    }

    def __init__(self, batch_size: int = DATA_HANDLER_BATCH_SIZE, flush_interval: float = DATA_HANDLER_FLUSH_INTERVAL):
        """
        Args:
            batch_size: Размер батча для записи в ClickHouse
            flush_interval: Интервал автоматического flush в секундах
        """
        self._buffer = BatchBuffer(
            tables=['users', 'tracks', 'events'],
            batch_size=batch_size,
            flush_interval=flush_interval,
            flush_callback=self._flush_to_clickhouse,
            name="KafkaDataHandler",
        )

    async def _flush_to_clickhouse(self, buffer_name: str, records: List[List[Any]]) -> None:
        """Callback для записи данных в ClickHouse."""
        clickhouse = get_clickhouse_client()

        table_name = self.BUFFER_TO_TABLE.get(buffer_name, buffer_name)

        column_getter = self.BUFFER_TO_COLUMNS.get(buffer_name)
        column_names = column_getter() if column_getter else None

        await clickhouse.insert(table_name, records, column_names)

        logger.info(
            "Батч INSERT из Kafka: buffer=%s, table=%s, records=%s",
            buffer_name, table_name, len(records)
        )

    async def handle_user(self, user_data: Dict[str, Any]) -> None:
        """Обработать пользователя из Kafka"""
        try:
            await self._buffer.add('users', [
                user_data['user_id'],
                user_data['username'],
                user_data.get('email', ''),
                user_data.get('age', 0),
                user_data.get('country', ''),
                self._parse_datetime(user_data.get('created_at')),
            ])
        except Exception as e:
            logger.error("Ошибка обработки пользователя: %s", e, extra={"user": user_data})

    async def handle_track(self, track_data: Dict[str, Any]) -> None:
        """Обработать трек из Kafka"""
        try:
            await self._buffer.add('tracks', [
                track_data['track_id'],
                track_data['title'],
                track_data['artist'],
                track_data.get('album', ''),
                track_data.get('genre', ''),
                track_data.get('duration_seconds', 0),
                track_data.get('release_year', 0),
                self._parse_datetime(track_data.get('created_at')),
            ])
        except Exception as e:
            logger.error("Ошибка обработки трека: %s", e, extra={"track": track_data})

    async def handle_event(self, event_data: Dict[str, Any]) -> None:
        """Обработать событие из Kafka"""
        try:
            # Обновляем метрики в Redis (единая реализация из event_handler)
            redis_client = get_redis_client()
            user_id = event_data.get("user_id")
            track_id = event_data.get("track_id")
            action_type = event_data.get("action_type")

            if all([user_id, track_id, action_type]):
                await update_analytics_metrics(
                    redis_client, int(user_id), int(track_id), str(action_type)
                )

            # Преобразуем action_type в значение для ClickHouse
            if isinstance(action_type, str):
                action_value = action_type
            elif hasattr(action_type, 'value'):
                action_value = action_type.value
            else:
                action_value = str(action_type)

            await self._buffer.add('events', [
                event_data['user_id'],
                event_data['track_id'],
                action_value,
                event_data.get('listen_duration_seconds'),
                self._parse_datetime(event_data.get('timestamp')),
            ])
        except Exception as e:
            logger.error("Ошибка обработки события: %s", e, extra={"event": event_data})

    async def start_periodic_flush(self) -> None:
        """Запустить периодический flush"""
        await self._buffer.start()

    async def stop_periodic_flush(self) -> None:
        """Остановить периодический flush и сбросить все буферы"""
        await self._buffer.stop()

    def _parse_datetime(self, value: Any) -> datetime:
        """Парсинг datetime из различных форматов"""
        if value is None:
            return datetime.now()
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return datetime.now()
        return datetime.now()


# Глобальный обработчик
_data_handler: Optional[KafkaDataHandler] = None


def get_data_handler() -> KafkaDataHandler:
    """Получить глобальный обработчик данных"""
    global _data_handler
    if _data_handler is None:
        _data_handler = KafkaDataHandler(
            batch_size=DATA_HANDLER_BATCH_SIZE,
            flush_interval=DATA_HANDLER_FLUSH_INTERVAL
        )
    return _data_handler


async def process_kafka_message(topic: str, message: Dict[str, Any]) -> None:
    """
    Универсальный обработчик сообщений из Kafka

    Args:
        topic: Название топика (users, tracks, user_track_events)
        message: Десериализованное сообщение
    """
    handler = get_data_handler()

    if topic == "users":
        await handler.handle_user(message)
    elif topic == "tracks":
        await handler.handle_track(message)
    elif topic == "user_track_events":
        await handler.handle_event(message)
    else:
        logger.warning("Неизвестный топик: %s", topic)
