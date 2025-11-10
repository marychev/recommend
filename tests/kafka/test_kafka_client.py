import pytest
from unittest.mock import patch, Mock
from aiokafka.errors import KafkaError
import app.kafka.client as client_module

from app.kafka.client import (
    get_kafka_producer,
    get_kafka_consumer,
    close_kafka_producer,
    close_kafka_consumer,
    check_kafka_health,
    connect_kafka
)


class TestGetKafkaProducer:
    """Тесты для get_kafka_producer()"""

    @pytest.mark.asyncio
    @patch("app.kafka.client.AIOKafkaProducer")
    async def test_get_kafka_producer_creates_new_instance(
        self, mock_producer_class, mock_kafka_producer
    ):
        """Тест создания нового producer"""
        # Очищаем глобальный producer

        client_module._kafka_producer = None

        mock_producer_class.return_value = mock_kafka_producer

        producer = await get_kafka_producer()

        assert producer is not None
        mock_producer_class.assert_called_once()
        mock_kafka_producer.start.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.kafka.client.AIOKafkaProducer")
    async def test_get_kafka_producer_returns_existing_instance(
        self, mock_producer_class, mock_kafka_producer
    ):
        """Тест возврата существующего producer (singleton)"""

        client_module._kafka_producer = mock_kafka_producer

        producer = await get_kafka_producer()

        assert producer == mock_kafka_producer
        # Не должен создавать новый
        mock_producer_class.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.kafka.client.AIOKafkaProducer")
    async def test_get_kafka_producer_with_correct_config(
        self, mock_producer_class, mock_kafka_producer
    ):
        """Тест правильной конфигурации producer"""

        client_module._kafka_producer = None

        mock_producer_class.return_value = mock_kafka_producer

        await get_kafka_producer()

        # Проверяем параметры
        call_kwargs = mock_producer_class.call_args[1]
        assert call_kwargs["compression_type"] == "gzip"
        assert call_kwargs["acks"] == "all"
        # assert call_kwargs["max_in_flight_requests_per_connection"] == 5
        assert call_kwargs["retries"] == 3
        assert call_kwargs["request_timeout_ms"] == 30000


class TestGetKafkaConsumer:
    """Тесты для get_kafka_consumer()"""

    @pytest.mark.asyncio
    @patch("app.kafka.client.AIOKafkaConsumer")
    async def test_get_kafka_consumer_with_topic(
        self, mock_consumer_class, mock_kafka_consumer
    ):
        """Тест создания consumer для топика"""
        mock_consumer_class.return_value = mock_kafka_consumer

        consumer = await get_kafka_consumer("test_topic")

        assert consumer is not None
        mock_consumer_class.assert_called_once()
        mock_kafka_consumer.start.assert_called_once()

        # Проверяем что топик передан
        call_args = mock_consumer_class.call_args[0]
        assert "test_topic" in call_args

    @pytest.mark.asyncio
    @patch("app.kafka.client.AIOKafkaConsumer")
    async def test_get_kafka_consumer_with_custom_group_id(
        self, mock_consumer_class, mock_kafka_consumer
    ):
        """Тест создания consumer с кастомной группой"""
        mock_consumer_class.return_value = mock_kafka_consumer

        await get_kafka_consumer("test_topic", group_id="custom_group")

        call_kwargs = mock_consumer_class.call_args[1]
        assert call_kwargs["group_id"] == "custom_group"

    @pytest.mark.asyncio
    @patch("app.kafka.client.AIOKafkaConsumer")
    async def test_get_kafka_consumer_with_correct_config(
        self, mock_consumer_class, mock_kafka_consumer
    ):
        """Тест правильной конфигурации consumer"""
        mock_consumer_class.return_value = mock_kafka_consumer

        await get_kafka_consumer("test_topic")

        call_kwargs = mock_consumer_class.call_args[1]
        assert call_kwargs["auto_offset_reset"] == "earliest"
        assert call_kwargs["enable_auto_commit"] is True
        assert call_kwargs["auto_commit_interval_ms"] == 5000


class TestCloseKafkaProducer:
    """Тесты для close_kafka_producer()"""

    @pytest.mark.asyncio
    async def test_close_kafka_producer_when_exists(self, mock_kafka_producer):
        """Тест закрытия существующего producer"""

        client_module._kafka_producer = mock_kafka_producer

        await close_kafka_producer()

        mock_kafka_producer.stop.assert_called_once()
        assert client_module._kafka_producer is None

    @pytest.mark.asyncio
    async def test_close_kafka_producer_when_none(self):
        """Тест закрытия когда producer = None"""

        client_module._kafka_producer = None

        # Не должно вызывать исключений
        await close_kafka_producer()
        assert client_module._kafka_producer is None

    @pytest.mark.asyncio
    async def test_close_kafka_producer_handles_exception(
        self, mock_kafka_producer
    ):
        """Тест обработки исключения при закрытии"""

        client_module._kafka_producer = mock_kafka_producer
        mock_kafka_producer.stop.side_effect = Exception("Stop error")

        # Не должно пробрасывать исключение
        await close_kafka_producer()
        assert client_module._kafka_producer is None


class TestCloseKafkaConsumer:
    """Тесты для close_kafka_consumer()"""

    @pytest.mark.asyncio
    async def test_close_kafka_consumer_when_exists(self, mock_kafka_consumer):
        """Тест закрытия существующего consumer"""
        await close_kafka_consumer(mock_kafka_consumer)
        mock_kafka_consumer.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_kafka_consumer_when_none(self):
        """Тест закрытия когда consumer = None"""
        # Не должно вызывать исключений
        await close_kafka_consumer(None)

    @pytest.mark.asyncio
    async def test_close_kafka_consumer_handles_exception(
        self, mock_kafka_consumer
    ):
        """Тест обработки исключения при закрытии consumer"""
        mock_kafka_consumer.stop.side_effect = Exception("Stop error")

        # Не должно пробрасывать исключение
        await close_kafka_consumer(mock_kafka_consumer)


class TestCheckKafkaHealth:
    """Тесты для check_kafka_health()"""

    @pytest.mark.asyncio
    @patch("app.kafka.client.get_kafka_producer")
    async def test_check_kafka_health_when_healthy(
        self, mock_get_producer, mock_kafka_producer
    ):
        """Тест health check для здорового Kafka"""
        mock_kafka_producer._sender = Mock()
        mock_get_producer.return_value = mock_kafka_producer

        result = await check_kafka_health()

        assert result["status"] == "healthy"
        assert "bootstrap_servers" in result
        assert "topic" in result

    @pytest.mark.asyncio
    @patch("app.kafka.client.get_kafka_producer")
    async def test_check_kafka_health_when_not_connected(
        self, mock_get_producer, mock_kafka_producer
    ):
        """Тест health check когда producer не подключен"""
        mock_kafka_producer._sender = None
        mock_get_producer.return_value = mock_kafka_producer

        result = await check_kafka_health()

        assert result["status"] == "unhealthy"
        assert "error" in result

    @pytest.mark.asyncio
    @patch("app.kafka.client.get_kafka_producer")
    async def test_check_kafka_health_when_kafka_error(
        self, mock_get_producer
    ):
        """Тест health check при ошибке Kafka"""
        mock_get_producer.side_effect = KafkaError("Connection failed")

        result = await check_kafka_health()

        assert result["status"] == "unhealthy"
        assert "error" in result

    @pytest.mark.asyncio
    @patch("app.kafka.client.get_kafka_producer")
    async def test_check_kafka_health_when_unexpected_error(
        self, mock_get_producer
    ):
        """Тест health check при неожиданной ошибке"""
        mock_get_producer.side_effect = Exception("Unexpected error")

        result = await check_kafka_health()

        assert result["status"] == "error"
        assert "error" in result


class TestConnectKafka:
    """Тесты для connect_kafka()"""

    @pytest.mark.asyncio
    @patch("app.kafka.client.get_kafka_producer")
    async def test_connect_kafka_success(
        self, mock_get_producer, mock_kafka_producer
    ):
        """Тест успешного подключения к Kafka"""
        mock_get_producer.return_value = mock_kafka_producer

        result = await connect_kafka()

        assert result is True
        mock_get_producer.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.kafka.client.get_kafka_producer")
    async def test_connect_kafka_failure(self, mock_get_producer):
        """Тест неудачного подключения к Kafka"""
        mock_get_producer.side_effect = Exception("Connection failed")

        result = await connect_kafka()

        assert result is False
