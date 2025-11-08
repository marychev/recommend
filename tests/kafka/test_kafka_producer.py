"""
Тесты для Kafka producer (app/kafka/producer.py)
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from datetime import datetime
from aiokafka.errors import KafkaError

from app.kafka.producer import serialize_event, send_event, send_batch_events


class TestSerializeEvent:
    """Тесты для serialize_event()"""

    def test_serialize_event_basic(self, sample_event):
        """Тест базовой сериализации события"""
        result = serialize_event(sample_event)

        assert isinstance(result, bytes)
        assert b"user_id" in result
        assert b"1001" in result
        assert b"track_id" in result
        assert b"12345" in result

    def test_serialize_event_with_datetime(self):
        """Тест сериализации события с datetime"""
        event = {
            "user_id": 1001,
            "timestamp": datetime(2025, 11, 5, 12, 30, 0),
        }

        result = serialize_event(event)

        assert b"2025-11-05T12:30:00" in result

    def test_serialize_event_with_russian_text(self):
        """Тест сериализации с русским текстом"""
        event = {
            "user_id": 1001,
            "description": "Прослушивание трека",
        }

        result = serialize_event(event)

        # Проверяем что русский текст закодирован правильно
        assert isinstance(result, bytes)
        assert "Прослушивание".encode("utf-8") in result

    def test_serialize_event_empty(self):
        """Тест сериализации пустого события"""
        event = {}

        result = serialize_event(event)

        assert result == b"{}"

    def test_serialize_event_with_nested_objects(self):
        """Тест сериализации с вложенными объектами"""
        event = {
            "user_id": 1001,
            "metadata": {"source": "mobile", "version": "1.0"},
        }

        result = serialize_event(event)

        assert b"metadata" in result
        assert b"source" in result
        assert b"mobile" in result


class TestSendEvent:
    """Тесты для send_event()"""

    @pytest.mark.asyncio
    @patch("app.kafka.producer.get_kafka_producer")
    async def test_send_event_success(
        self, mock_get_producer, mock_kafka_producer, sample_event
    ):
        """Тест успешной отправки события"""
        mock_get_producer.return_value = mock_kafka_producer

        result = await send_event(sample_event)

        assert result is True
        mock_kafka_producer.send.assert_called_once()

        # Проверяем аргументы вызова
        call_args = mock_kafka_producer.send.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    @patch("app.kafka.producer.get_kafka_producer")
    async def test_send_event_with_correct_key(
        self, mock_get_producer, mock_kafka_producer, sample_event
    ):
        """Тест отправки события с правильным ключом (user_id)"""
        mock_get_producer.return_value = mock_kafka_producer

        await send_event(sample_event)

        call_kwargs = mock_kafka_producer.send.call_args[1]
        assert call_kwargs["key"] == b"1001"

    @pytest.mark.asyncio
    @patch("app.kafka.producer.get_kafka_producer")
    async def test_send_event_without_user_id(
        self, mock_get_producer, mock_kafka_producer
    ):
        """Тест отправки события без user_id"""
        mock_get_producer.return_value = mock_kafka_producer

        event = {"track_id": 12345, "action_type": "play"}

        await send_event(event)

        call_kwargs = mock_kafka_producer.send.call_args[1]
        # Ключ должен быть пустой строкой
        assert call_kwargs["key"] == b""

    @pytest.mark.asyncio
    @patch("app.kafka.producer.get_kafka_producer")
    async def test_send_event_kafka_error(
        self, mock_get_producer, mock_kafka_producer, sample_event
    ):
        """Тест обработки ошибки Kafka при отправке"""
        mock_get_producer.return_value = mock_kafka_producer
        mock_kafka_producer.send.side_effect = KafkaError("Send failed")

        result = await send_event(sample_event)

        assert result is False

    @pytest.mark.asyncio
    @patch("app.kafka.producer.get_kafka_producer")
    async def test_send_event_unexpected_error(
        self, mock_get_producer, mock_kafka_producer, sample_event
    ):
        """Тест обработки неожиданной ошибки"""
        mock_get_producer.return_value = mock_kafka_producer
        mock_kafka_producer.send.side_effect = Exception("Unexpected error")

        result = await send_event(sample_event)

        assert result is False

    @pytest.mark.asyncio
    @patch("app.kafka.producer.get_kafka_producer")
    async def test_send_event_to_correct_topic(
        self, mock_get_producer, mock_kafka_producer, sample_event
    ):
        """Тест отправки в правильный топик"""
        mock_get_producer.return_value = mock_kafka_producer

        await send_event(sample_event)

        call_args = mock_kafka_producer.send.call_args[0]
        # Первый аргумент - это топик
        from app.config import settings

        assert call_args[0] == settings.kafka_topic_events


class TestSendBatchEvents:
    """Тесты для send_batch_events()"""

    @pytest.mark.asyncio
    @patch("app.kafka.producer.get_kafka_producer")
    async def test_send_batch_events_success(
        self, mock_get_producer, mock_kafka_producer, sample_events_batch
    ):
        """Тест успешной отправки пакета событий"""
        mock_get_producer.return_value = mock_kafka_producer

        # Мокируем batch
        mock_batch = Mock()
        mock_batch.append = Mock(return_value=Mock())  # Не None = успех
        mock_batch.__len__ = Mock(return_value=len(sample_events_batch))
        mock_kafka_producer.create_batch.return_value = mock_batch

        result = await send_batch_events(sample_events_batch)

        assert result == len(sample_events_batch)
        mock_kafka_producer.send_batch.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.kafka.producer.get_kafka_producer")
    async def test_send_batch_events_empty_list(
        self, mock_get_producer, mock_kafka_producer
    ):
        """Тест отправки пустого пакета"""
        mock_get_producer.return_value = mock_kafka_producer

        mock_batch = Mock()
        mock_batch.__len__ = Mock(return_value=0)
        mock_kafka_producer.create_batch.return_value = mock_batch

        _ = await send_batch_events([])

        # Не должно вызывать send_batch для пустого пакета
        mock_kafka_producer.send_batch.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.kafka.producer.get_kafka_producer")
    async def test_send_batch_events_multiple_batches(
        self, mock_get_producer, mock_kafka_producer
    ):
        """Тест отправки когда нужно несколько batch"""
        mock_get_producer.return_value = mock_kafka_producer

        # Симулируем что batch заполняется после 2 событий
        mock_batch = Mock()
        append_results = [Mock(), None, Mock()]  # None = batch полон
        mock_batch.append = Mock(side_effect=append_results)
        mock_batch.__len__ = Mock(return_value=2)
        mock_kafka_producer.create_batch.return_value = mock_batch

        events = [
            {"user_id": 1, "track_id": 1},
            {"user_id": 2, "track_id": 2},
            {"user_id": 3, "track_id": 3},
        ]

        _ = await send_batch_events(events)

        # Должно вызвать send_batch несколько раз
        assert mock_kafka_producer.send_batch.call_count >= 1

    @pytest.mark.asyncio
    @patch("app.kafka.producer.get_kafka_producer")
    async def test_send_batch_events_kafka_error(
        self, mock_get_producer, mock_kafka_producer, sample_events_batch
    ):
        """Тест обработки ошибки Kafka"""
        mock_get_producer.return_value = mock_kafka_producer
        mock_kafka_producer.create_batch.side_effect = KafkaError(
            "Batch error"
        )

        result = await send_batch_events(sample_events_batch)

        assert result == 0  # Вернет 0 при ошибке

    @pytest.mark.asyncio
    @patch("app.kafka.producer.get_kafka_producer")
    async def test_send_batch_events_unexpected_error(
        self, mock_get_producer, mock_kafka_producer, sample_events_batch
    ):
        """Тест обработки неожиданной ошибки"""
        mock_get_producer.return_value = mock_kafka_producer
        mock_kafka_producer.create_batch.side_effect = Exception(
            "Unexpected error"
        )

        result = await send_batch_events(sample_events_batch)

        assert result == 0
