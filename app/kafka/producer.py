import json
import logging
from typing import Dict, Any
from datetime import datetime

from aiokafka.errors import KafkaError

from app.kafka.client import get_kafka_producer
from app.config import settings

logger = logging.getLogger(__name__)


def serialize_event(event: Dict[str, Any]) -> bytes:
    """
    Сериализовать событие в JSON байты

    Args:
        event: Словарь события

    Returns:
        bytes: Сериализованное событие
    """
    # Конвертируем datetime в ISO string
    if "timestamp" in event and isinstance(event["timestamp"], datetime):
        event["timestamp"] = event["timestamp"].isoformat()

    return json.dumps(event, ensure_ascii=False).encode("utf-8")


def _get_message_and_key(event: Dict[str, Any]) -> tuple[bytes, bytes]:
    """Используем user_id как ключ для партиционирования"""
    message = serialize_event(event)
    key = str(event.get("user_id", "")).encode("utf-8")
    return message, key


async def send_event(event: Dict[str, Any]) -> bool:
    """
    Отправить событие в Kafka

    Args:
        event: Словарь с данными события
            - user_id: int
            - track_id: int
            - action_type: str
            - listen_duration_seconds: int
            - timestamp: datetime

    Returns:
        bool: True если успешно отправлено
    """
    try:
        # Используем таймаут для запуска producer
        producer = await get_kafka_producer(start_timeout=10.0)
        message, key = _get_message_and_key(event)

        await producer.send(
            settings.kafka_topic_events, value=message, key=key
        )

        logger.debug(
            "Event sent to Kafka: user_id=%s, track_id=%s, action=%s",
            event.get("user_id"),
            event.get("track_id"),
            event.get("action_type"),
        )

        return True

    except KafkaError as e:
        logger.error(
            "Failed to send event to Kafka: %s", e, extra={"event": event}
        )
        return False
    except Exception as e:
        logger.error(
            "Unexpected error sending event to Kafka: %s",
            e,
            extra={"event": event},
        )
        return False


async def send_batch_events(events: list[Dict[str, Any]]) -> int:
    """
    Отправить пакет событий в Kafka

    Args:
        events: Список словарей событий

    Returns:
        int: Количество успешно отправленных событий
    """
    success_count = 0

    try:
        # Используем таймаут для запуска producer
        producer = await get_kafka_producer(start_timeout=10.0)
        batch = producer.create_batch()
        batch_size = 0  # Счетчик событий в текущем batch

        for event in events:
            message, key = _get_message_and_key(event)

            # Добавляем в batch
            metadata = batch.append(key=key, value=message, timestamp=None)

            if metadata is None:
                # Batch полон, отправляем текущий batch
                if batch_size > 0:
                    await producer.send_batch(
                        batch, settings.kafka_topic_events, partition=0
                    )
                    success_count += batch_size

                # Создаем новый batch и добавляем текущее событие
                batch = producer.create_batch()
                batch.append(key=key, value=message, timestamp=None)
                batch_size = 1
            else:
                # Событие успешно добавлено в batch
                batch_size += 1

        # Отправляем оставшиеся события
        if batch_size > 0:
            await producer.send_batch(
                batch, settings.kafka_topic_events, partition=0
            )
            success_count += batch_size

        logger.info("Batch events sent to Kafka: count=%s", success_count)

        return success_count

    except KafkaError as e:
        logger.error("Failed to send batch to Kafka: %s", e)
        return success_count
    except Exception as e:
        logger.error("Unexpected error sending batch to Kafka: %s", e)
        return success_count
