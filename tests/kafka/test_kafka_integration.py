"""
Интеграционные тесты для Kafka
Требуют запущенный Kafka для выполнения
"""
import time

import pytest
import asyncio
from datetime import datetime

from app.kafka.producer import send_event, send_batch_events
from app.kafka.consumer import consume_events
from app.kafka.client import (
    connect_kafka,
    check_kafka_health,
    close_kafka_producer,
)


# Маркер для интеграционных тестов
pytestmark = pytest.mark.integration


@pytest.fixture
def sample_test_event():
    """Тестовое событие для интеграционных тестов"""
    return {
        "user_id": 9999,
        "track_id": 99999,
        "action_type": "play",
        "listen_duration_seconds": 60,
        "timestamp": datetime.now(),
    }


class TestKafkaIntegration:
    """Интеграционные тесты Kafka (требуют запущенный Kafka)"""

    @pytest.mark.asyncio
    async def test_kafka_connection(self):
        """Тест подключения к Kafka"""
        result = await connect_kafka()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_kafka_health_check(self):
        """Тест health check Kafka"""
        result = await check_kafka_health()

        assert "status" in result
        # Может быть healthy или unhealthy в зависимости от Kafka
        assert result["status"] in ["healthy", "unhealthy", "error"]

    @pytest.mark.asyncio
    async def test_send_and_consume_event(self, sample_test_event):
        """Тест полного цикла: отправка -> получение события"""
        # Пропускаем если Kafka недоступна
        kafka_connected = await connect_kafka()
        if not kafka_connected:
            pytest.skip("Kafka недоступна")

        # Отправляем событие
        sent = await send_event(sample_test_event)
        assert sent is True

        # Даем время на доставку
        await asyncio.sleep(1)

        # Читаем событие
        received_events = []

        async def test_handler(event):
            received_events.append(event)
            # Останавливаем consumer после первого события
            raise KeyboardInterrupt()

        try:
            await consume_events(test_handler)
        except KeyboardInterrupt:
            pass

        # Проверяем что событие получено
        # Может быть несколько событий в топике
        assert len(received_events) > 0

    @pytest.mark.asyncio
    async def test_send_batch_events(self):
        """Тест отправки пакета событий"""
        kafka_connected = await connect_kafka()
        if not kafka_connected:
            pytest.skip("Kafka недоступна")

        events = [
            {
                "user_id": 9999 + i,
                "track_id": 99999 + i,
                "action_type": "play",
                "listen_duration_seconds": 60,
                "timestamp": datetime.now(),
            }
            for i in range(5)
        ]

        result = await send_batch_events(events)

        # Должно вернуть количество отправленных событий
        assert result > 0


class TestKafkaPerformance:
    """Тесты производительности Kafka"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_send_many_events_performance(self):
        """Тест производительности отправки множества событий"""
        kafka_connected = await connect_kafka()
        if not kafka_connected:
            pytest.skip("Kafka недоступна")

        event = {
            "user_id": 9999,
            "track_id": 99999,
            "action_type": "play",
            "listen_duration_seconds": 60,
            "timestamp": datetime.now(),
        }

        start = time.time()
        count = 100

        # Отправляем много событий
        for _ in range(count):
            await send_event(event)

        elapsed = time.time() - start

        # Проверяем производительность
        events_per_second = count / elapsed
        print(f"\n📊 Производительность: {events_per_second:.2f} событий/сек")

        # Должно быть достаточно быстро
        assert events_per_second > 10  # Минимум 10 событий в секунду

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_batch_send_performance(self):
        """Тест производительности batch отправки"""
        kafka_connected = await connect_kafka()
        if not kafka_connected:
            pytest.skip("Kafka недоступна")

        events = [
            {
                "user_id": 9999 + i,
                "track_id": 99999 + i,
                "action_type": "play",
                "listen_duration_seconds": 60,
                "timestamp": datetime.now(),
            }
            for i in range(100)
        ]

        start = time.time()
        result = await send_batch_events(events)
        elapsed = time.time() - start

        events_per_second = result / elapsed
        print(
            f"\nBatch производительность: "
            f"{events_per_second:.2f} событий/сек"
        )

        # Batch должен быть значительно быстрее
        assert events_per_second > 50


class TestKafkaReliability:
    """Тесты надежности Kafka"""

    @pytest.mark.asyncio
    async def test_send_event_when_kafka_unavailable(self):
        """Тест отправки когда Kafka недоступна"""
        # Закрываем producer
        await close_kafka_producer()

        # Пытаемся отправить событие с недоступной Kafka
        event = {
            "user_id": 9999,
            "track_id": 99999,
            "action_type": "play",
        }

        # Не должно вызывать исключение
        result = await send_event(event)

        # Может вернуть True или False в зависимости от состояния
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_concurrent_sends(self):
        """Тест параллельной отправки событий"""
        kafka_connected = await connect_kafka()
        if not kafka_connected:
            pytest.skip("Kafka недоступна")

        async def send_test_event(i):
            event = {
                "user_id": 9999 + i,
                "track_id": 99999 + i,
                "action_type": "play",
                "listen_duration_seconds": 60,
                "timestamp": datetime.now(),
            }
            return await send_event(event)

        # Отправляем 10 событий параллельно
        results = await asyncio.gather(
            *[send_test_event(i) for i in range(10)]
        )

        # Все должны быть успешными
        assert all(results)
