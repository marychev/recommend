from typing import Optional
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Глобальные экземпляры
_kafka_producer: Optional[AIOKafkaProducer] = None
_kafka_consumer: Optional[AIOKafkaConsumer] = None


async def get_kafka_producer() -> AIOKafkaProducer:
    global _kafka_producer

    if _kafka_producer is None:
        _kafka_producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            # Сериализация в JSON будет в producer.py
            value_serializer=None,
            compression_type="gzip",  # Сжатие для экономии
            acks="all",  # Надежная доставка
            retries=3,  # Повторные попытки
            request_timeout_ms=30000,
        )
        await _kafka_producer.start()
        logger.info(
            f"✅ Kafka Producer запущен: "
            f"{settings.kafka_bootstrap_servers}"
        )

    return _kafka_producer


async def get_kafka_consumer(
    topic: str, group_id: Optional[str] = None
) -> AIOKafkaConsumer:
    if group_id is None:
        group_id = settings.kafka_consumer_group

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=group_id,
        # Десериализация в consumer.py
        value_deserializer=None,
        auto_offset_reset="earliest",  # Читать с начала
        enable_auto_commit=True,
        auto_commit_interval_ms=5000,
    )

    await consumer.start()
    logger.info(f"✅ Kafka Consumer запущен: topic={topic}, group={group_id}")

    return consumer


async def close_kafka_producer():
    """Закрыть Kafka Producer"""
    global _kafka_producer

    if _kafka_producer is not None:
        try:
            await _kafka_producer.stop()
            logger.info("Kafka Producer stopped")
        except Exception as e:
            logger.error("Error stopping Kafka Producer: %s", e)
        finally:
            _kafka_producer = None


async def close_kafka_consumer(consumer: AIOKafkaConsumer):
    """
    Закрыть Kafka Consumer

    Args:
        consumer: Экземпляр consumer для закрытия
    """
    if consumer is not None:
        try:
            await consumer.stop()
            logger.info("Kafka Consumer stopped")
        except Exception as e:
            logger.error("Error stopping Kafka Consumer: %s", e)


async def check_kafka_health() -> dict:
    try:
        producer = await get_kafka_producer()

        # Проверяем что producer подключен
        if producer._sender is not None:
            return {
                "status": "healthy",
                "bootstrap_servers": settings.kafka_bootstrap_servers,
                "topic": settings.kafka_topic_events,
            }
        else:
            return {"status": "unhealthy", "error": "Producer not connected"}
    except KafkaError as e:
        logger.error("Kafka health check failed: %s", e)
        return {"status": "unhealthy", "error": str(e)}
    except Exception as e:
        logger.error("Unexpected error in Kafka health check: %s", e)
        return {"status": "error", "error": str(e)}


async def connect_kafka() -> bool:
    kafka_connected = False
    try:
        await get_kafka_producer()
        kafka_connected = True
        print("Kafka Producer подключен")
    except Exception as e:
        logger.warning("Kafka unavailable: %s", e)
        print("Kafka недоступна (события не будут отправляться)")
    return kafka_connected
