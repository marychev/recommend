import json
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime

from aiokafka.errors import KafkaError

from app.kafka.client import get_kafka_producer
from app.kafka.constants import (
    PRODUCER_START_TIMEOUT_EVENTS,
    PRODUCER_START_TIMEOUT_BATCH,
    PRODUCER_START_TIMEOUT_QUICK,
)
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
    # Создаем копию, чтобы не изменять оригинальный словарь
    serializable_event = {}
    
    for key, value in event.items():
        # Конвертируем datetime в ISO string
        if isinstance(value, datetime):
            serializable_event[key] = value.isoformat()
        else:
            serializable_event[key] = value

    return json.dumps(serializable_event, ensure_ascii=False).encode("utf-8")


def _get_message_and_key(
    data: Dict[str, Any], key_field: str = "user_id"
) -> tuple[bytes, bytes]:
    """Сериализовать данные и извлечь ключ для партиционирования Kafka"""
    message = serialize_event(data)
    key = str(data.get(key_field, "")).encode("utf-8")
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
        producer = await get_kafka_producer(start_timeout=PRODUCER_START_TIMEOUT_EVENTS)
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
        producer = await get_kafka_producer(start_timeout=PRODUCER_START_TIMEOUT_BATCH)
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


async def send_user(user: Dict[str, Any]) -> bool:
    """
    Отправить пользователя в Kafka

    Args:
        user: Словарь с данными пользователя
            - user_id: int
            - username: str
            - email: str
            - age: int
            - country: str
            - created_at: datetime

    Returns:
        bool: True если успешно отправлено, False если ошибка
    """
    try:
        producer = await get_kafka_producer(start_timeout=PRODUCER_START_TIMEOUT_QUICK)
        message, key = _get_message_and_key(user, key_field="user_id")

        await producer.send(
            settings.kafka_topic_users, value=message, key=key
        )

        logger.debug(
            "User sent to Kafka: user_id=%s, username=%s",
            user.get("user_id"),
            user.get("username"),
        )

        return True

    except (KafkaError, asyncio.TimeoutError, ConnectionError) as e:
        logger.warning(
            "Kafka недоступен для отправки пользователя: %s", e
        )
        return False
    except Exception as e:
        logger.error(
            "Unexpected error sending user to Kafka: %s",
            e,
            extra={"user": user},
        )
        return False


async def send_track(track: Dict[str, Any]) -> bool:
    """
    Отправить трек в Kafka

    Args:
        track: Словарь с данными трека
            - track_id: int
            - title: str
            - artist: str
            - album: str
            - genre: str
            - duration_seconds: int
            - release_year: int
            - created_at: datetime

    Returns:
        bool: True если успешно отправлено, False если ошибка
    """
    try:
        producer = await get_kafka_producer(start_timeout=PRODUCER_START_TIMEOUT_QUICK)
        message, key = _get_message_and_key(track, key_field="track_id")

        await producer.send(
            settings.kafka_topic_tracks, value=message, key=key
        )

        logger.debug(
            "Track sent to Kafka: track_id=%s, title=%s",
            track.get("track_id"),
            track.get("title"),
        )

        return True

    except (KafkaError, asyncio.TimeoutError, ConnectionError) as e:
        logger.warning(
            "Kafka недоступен для отправки трека: %s", e
        )
        return False
    except Exception as e:
        logger.error(
            "Unexpected error sending track to Kafka: %s",
            e,
            extra={"track": track},
        )
        return False
