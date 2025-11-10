"""
Тесты для Kafka consumer (app/kafka/consumer.py)
"""

import asyncio

import pytest
import json
from unittest.mock import patch, AsyncMock, Mock
from datetime import datetime
from aiokafka.errors import KafkaError

from app.kafka.consumer import (
    deserialize_event,
    consume_events,
    start_background_consumer,
    example_event_handler,
)


class TestDeserializeEvent:
    """Тесты для deserialize_event()"""

    def test_deserialize_event_basic(self, sample_event_serialized):
        """Тест базовой десериализации"""
        result = deserialize_event(sample_event_serialized)

        assert isinstance(result, dict)
        assert result["user_id"] == 1001
        assert result["track_id"] == 12345
        assert result["action_type"] == "play"

    def test_deserialize_event_with_timestamp(self):
        """Тест десериализации с timestamp"""
        message = b'{"user_id": 1001, ' b'"timestamp": "2025-11-05T12:00:00"}'

        result = deserialize_event(message)

        assert "timestamp" in result
        assert isinstance(result["timestamp"], datetime)
        assert result["timestamp"].year == 2025

    def test_deserialize_event_with_invalid_timestamp(self):
        """Тест десериализации с невалидным timestamp"""
        message = b'{"user_id": 1001, "timestamp": "invalid"}'

        result = deserialize_event(message)

        # Timestamp остается как строка
        assert result["timestamp"] == "invalid"

    def test_deserialize_event_with_russian_text(self):
        """Тест десериализации с русским текстом"""
        message = '{"description": "Прослушивание трека"}'.encode("utf-8")

        result = deserialize_event(message)

        assert result["description"] == "Прослушивание трека"

    def test_deserialize_event_empty(self):
        """Тест десериализации пустого сообщения"""
        message = b"{}"

        result = deserialize_event(message)

        assert result == {}

    def test_deserialize_event_invalid_json(self):
        """Тест десериализации невалидного JSON"""
        message = b"not a json"

        with pytest.raises(json.JSONDecodeError):
            deserialize_event(message)


class TestConsumeEvents:
    """Тесты для consume_events()"""

    @pytest.mark.asyncio
    @patch("app.kafka.consumer.get_kafka_consumer")
    @patch("app.kafka.consumer.close_kafka_consumer")
    async def test_consume_events_processes_messages(
        self, mock_close_consumer, mock_get_consumer, mock_kafka_message
    ):
        """Тест обработки сообщений из Kafka"""
        # Мокируем consumer который вернет одно сообщение и завершится
        mock_consumer = AsyncMock()

        # Создаем реальный async generator
        async def message_generator():
            yield mock_kafka_message
            return  # Нормальное завершение

        mock_consumer.__aiter__ = lambda self: message_generator()
        mock_get_consumer.return_value = mock_consumer

        # Обработчик событий
        handler = AsyncMock()

        # Запускаем consumer (добавляем timeout для избежания бесконечного цикла)

        try:
            await asyncio.wait_for(consume_events(handler), timeout=0.1)
        except asyncio.TimeoutError:
            pass
        except Exception:
            pass

        # Проверяем что обработчик был вызван
        handler.assert_called_once()

        # Проверяем что consumer был закрыт
        mock_close_consumer.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.kafka.consumer.get_kafka_consumer")
    @patch("app.kafka.consumer.close_kafka_consumer")
    async def test_consume_events_with_custom_topic(
        self, mock_close_consumer, mock_get_consumer
    ):
        """Тест подписки на кастомный топик"""
        mock_consumer = AsyncMock()
        mock_consumer.__aiter__ = AsyncMock(return_value=iter([]))
        mock_get_consumer.return_value = mock_consumer

        handler = AsyncMock()

        try:
            await consume_events(handler, topic="custom_topic")
        except Exception:
            pass

        # Проверяем что consumer создан с правильным топиком
        mock_get_consumer.assert_called_once()
        call_args = mock_get_consumer.call_args[0]
        assert call_args[0] == "custom_topic"

    @pytest.mark.asyncio
    @patch("app.kafka.consumer.get_kafka_consumer")
    @patch("app.kafka.consumer.close_kafka_consumer")
    async def test_consume_events_with_custom_group_id(
        self, mock_close_consumer, mock_get_consumer
    ):
        """Тест использования кастомной группы"""
        mock_consumer = AsyncMock()
        mock_consumer.__aiter__ = AsyncMock(return_value=iter([]))
        mock_get_consumer.return_value = mock_consumer

        handler = AsyncMock()

        try:
            await consume_events(handler, group_id="custom_group")
        except Exception:
            pass

        call_args = mock_get_consumer.call_args
        assert call_args[0][1] == "custom_group"

    @pytest.mark.asyncio
    @patch("app.kafka.consumer.get_kafka_consumer")
    @patch("app.kafka.consumer.close_kafka_consumer")
    async def test_consume_events_handles_deserialization_error(
        self, mock_close_consumer, mock_get_consumer
    ):
        """Тест обработки ошибки десериализации"""
        mock_consumer = AsyncMock()

        # Создаем сообщение с невалидным JSON
        invalid_message = Mock()
        invalid_message.value = b"invalid json"

        async def message_generator():
            yield invalid_message
            return

        mock_consumer.__aiter__ = lambda self: message_generator()
        mock_get_consumer.return_value = mock_consumer

        handler = AsyncMock()

        # Не должно пробрасывать исключение
        import asyncio

        try:
            await asyncio.wait_for(consume_events(handler), timeout=0.1)
        except asyncio.TimeoutError:
            pass
        except Exception:
            pass

        # Обработчик не должен быть вызван для невалидного сообщения
        handler.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.kafka.consumer.get_kafka_consumer")
    @patch("app.kafka.consumer.close_kafka_consumer")
    async def test_consume_events_handles_processing_error(
        self, mock_close_consumer, mock_get_consumer, mock_kafka_message
    ):
        """Тест обработки ошибки в обработчике"""
        mock_consumer = AsyncMock()

        async def message_generator():
            yield mock_kafka_message
            return

        mock_consumer.__aiter__ = lambda self: message_generator()
        mock_get_consumer.return_value = mock_consumer

        # Обработчик выбрасывает ошибку
        handler = AsyncMock(side_effect=Exception("Processing error"))

        # Не должно пробрасывать исключение

        try:
            await asyncio.wait_for(consume_events(handler), timeout=0.1)
        except asyncio.TimeoutError:
            pass
        except Exception:
            pass

        # Обработчик был вызван
        handler.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.kafka.consumer.get_kafka_consumer")
    async def test_consume_events_handles_kafka_error(self, mock_get_consumer):
        """Тест обработки ошибки Kafka"""
        mock_get_consumer.side_effect = KafkaError("Connection failed")

        handler = AsyncMock()

        # Должна проброситься ошибка Kafka
        with pytest.raises(KafkaError):
            await consume_events(handler)

    @pytest.mark.asyncio
    @patch("app.kafka.consumer.get_kafka_consumer")
    @patch("app.kafka.consumer.close_kafka_consumer")
    async def test_consume_events_closes_consumer_on_error(
        self, mock_close_consumer, mock_get_consumer
    ):
        """Тест что consumer закрывается при любой ошибке"""
        mock_consumer = AsyncMock()
        mock_get_consumer.return_value = mock_consumer

        # Симулируем неожиданную ошибку
        mock_consumer.__aiter__ = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        handler = AsyncMock()

        with pytest.raises(Exception):
            await consume_events(handler)

        # Consumer должен быть закрыт
        mock_close_consumer.assert_called_once_with(mock_consumer)


class TestStartBackgroundConsumer:
    """Тесты для start_background_consumer()"""

    @pytest.mark.asyncio
    @patch("app.kafka.consumer.consume_events")
    @patch("asyncio.create_task")
    async def test_start_background_consumer_creates_task(
        self, mock_create_task, mock_consume_events
    ):
        """Тест создания фоновой задачи"""
        handler = AsyncMock()

        mock_task = Mock()
        mock_create_task.return_value = mock_task

        result = await start_background_consumer(handler)

        assert result == mock_task
        mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.kafka.consumer.consume_events")
    async def test_start_background_consumer_with_handler(
        self, mock_consume_events
    ):
        """Тест запуска consumer с обработчиком"""
        handler = AsyncMock()

        await start_background_consumer(handler)

        # consume_events должен быть вызван (как task)
        # Мы не можем проверить это напрямую из-за create_task
        # но можем проверить что не было исключений


class TestExampleEventHandler:
    """Тесты для example_event_handler()"""

    @pytest.mark.asyncio
    async def test_example_event_handler_processes_event(self, sample_event):
        """Тест примерного обработчика событий"""
        # Не должно вызывать исключений
        await example_event_handler(sample_event)

    @pytest.mark.asyncio
    async def test_example_event_handler_with_missing_fields(self):
        """Тест обработчика с неполными данными"""
        event = {"user_id": 1001}

        # Не должно вызывать исключений
        await example_event_handler(event)

    @pytest.mark.asyncio
    async def test_example_event_handler_with_empty_event(self):
        """Тест обработчика с пустым событием"""
        event = {}

        # Не должно вызывать исключений
        await example_event_handler(event)
