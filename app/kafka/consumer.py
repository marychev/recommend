import json
import logging
import asyncio
from typing import Dict, Any, Callable, Awaitable, Optional
from datetime import datetime

from aiokafka.errors import KafkaError

from app.kafka.client import get_kafka_consumer, close_kafka_consumer
from app.config import settings

logger = logging.getLogger(__name__)


def deserialize_event(message: bytes) -> Dict[str, Any]:
    """
    Десериализовать событие из JSON байтов

    Args:
        message: Байты сообщения

    Returns:
        dict: Десериализованное событие
    """
    event = json.loads(message.decode("utf-8"))

    # Конвертируем ISO string обратно в datetime
    if "timestamp" in event and isinstance(event["timestamp"], str):
        try:
            event["timestamp"] = datetime.fromisoformat(event["timestamp"])
        except ValueError:
            logger.warning("Failed to parse timestamp: %s", event["timestamp"])

    return event


async def consume_events(
    handler: Callable[[Dict[str, Any]], Awaitable[None]],
    topic: Optional[str] = None,
    group_id: Optional[str] = None,
):
    """
    Запустить consumer для обработки событий

    Args:
        handler: Async функция-обработчик событий
        topic: Топик для подписки (по умолчанию из конфига)
        group_id: ID группы (по умолчанию из конфига)

    Example:
        ```python
        async def process_event(event: dict):
            print(f"Обработка события: {event}")

        await consume_events(process_event)
        ```
    """
    if not topic:
        topic = settings.kafka_topic_events

    consumer = None
    try:
        consumer = await get_kafka_consumer(topic, group_id)

        logger.info("Начинаем слушать события из Kafka: topic=%s", topic)

        async for message in consumer:
            try:
                # Десериализуем событие
                event = deserialize_event(message.value)

                logger.debug(
                    "Получено сообщение из Kafka: topic=%s, key=%s",
                    topic,
                    message.key.decode('utf-8') if message.key else None,
                )

                # Обрабатываем событие
                await handler(event)

            except json.JSONDecodeError as e:
                logger.error(
                    "Event deserialization error: %s",
                    e,
                    extra={"raw_message": message.value},
                )
            except Exception as e:
                logger.error(
                    "Event processing error: %s",
                    e,
                    extra={"event": event if "event" in locals() else None},
                )
                # Продолжаем обработку остальных событий

    except asyncio.CancelledError:
        # Нормальная отмена - не логируем как ошибку
        logger.debug("Consumer cancelled")
        raise
    except KafkaError as e:
        error_str = str(e)
        # CoordinatorNotAvailableError - это временная ошибка при старте Kafka
        # Consumer автоматически переподключится
        if "CoordinatorNotAvailable" in error_str or "15" in error_str:
            logger.warning(
                "Kafka Coordinator еще не готов (это нормально при старте): %s. Consumer переподключится автоматически.",
                e
            )
        else:
            logger.error("Kafka consumer error: %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected consumer error: %s", e)
        raise
    finally:
        if consumer is not None:
            try:
                await close_kafka_consumer(consumer)
            except Exception as e:
                logger.debug("Error closing consumer in finally: %s", e)


async def start_background_consumer(
    handler: Callable[[Dict[str, Any]], Awaitable[None]],
):
    """
    Запустить consumer в фоновом режиме

    Args:
        handler: Async функция-обработчик событий

    Returns:
        asyncio.Task: Задача consumer
    """
    task = asyncio.create_task(consume_events(handler, None, None))
    logger.info("Background Kafka consumer запущен")
    return task
