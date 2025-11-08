"""
Фикстуры для тестирования Kafka
"""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime


@pytest.fixture
def mock_kafka_producer():
    """Мок Kafka Producer"""
    producer = AsyncMock()
    producer.start = AsyncMock()
    producer.stop = AsyncMock()
    producer.send = AsyncMock()
    producer.create_batch = Mock()
    producer._sender = Mock()  # Для health check
    return producer


@pytest.fixture
def mock_kafka_consumer():
    """Мок Kafka Consumer"""
    consumer = AsyncMock()
    consumer.start = AsyncMock()
    consumer.stop = AsyncMock()
    return consumer


@pytest.fixture
def sample_event():
    """Пример события для тестирования"""
    return {
        "user_id": 1001,
        "track_id": 12345,
        "action_type": "play",
        "listen_duration_seconds": 180,
        "timestamp": datetime(2025, 11, 5, 12, 0, 0),
    }


@pytest.fixture
def sample_event_serialized():
    """Пример сериализованного события"""
    return (
        b'{"user_id": 1001, "track_id": 12345, '
        b'"action_type": "play", "listen_duration_seconds": 180, '
        b'"timestamp": "2025-11-05T12:00:00"}'
    )


@pytest.fixture
def sample_events_batch():
    """Пакет событий для тестирования"""
    return [
        {
            "user_id": 1001,
            "track_id": 12345,
            "action_type": "play",
            "listen_duration_seconds": 180,
            "timestamp": datetime(2025, 11, 5, 12, 0, 0),
        },
        {
            "user_id": 1002,
            "track_id": 12346,
            "action_type": "like",
            "listen_duration_seconds": 0,
            "timestamp": datetime(2025, 11, 5, 12, 1, 0),
        },
        {
            "user_id": 1003,
            "track_id": 12347,
            "action_type": "skip",
            "listen_duration_seconds": 30,
            "timestamp": datetime(2025, 11, 5, 12, 2, 0),
        },
    ]


@pytest.fixture
def mock_kafka_message():
    """Мок сообщения из Kafka"""
    message = Mock()
    message.value = (
        b'{"user_id": 1001, "track_id": 12345, '
        b'"action_type": "play", "listen_duration_seconds": 180, '
        b'"timestamp": "2025-11-05T12:00:00"}'
    )
    message.key = b"1001"
    message.offset = 0
    message.partition = 0
    return message
