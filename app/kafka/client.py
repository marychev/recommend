from typing import Optional
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError
import logging
import asyncio

from app.config import settings
from app.kafka.constants import (
    PRODUCER_START_TIMEOUT_DEFAULT,
    PRODUCER_REQUEST_TIMEOUT_MS,
    CLIENT_STOP_TIMEOUT,
    CONSUMER_AUTO_COMMIT_INTERVAL_MS,
    CONNECT_KAFKA_MAX_RETRIES,
    CONNECT_KAFKA_BASE_DELAY_NORMAL,
    CONNECT_KAFKA_BASE_DELAY_FAST,
)

logger = logging.getLogger(__name__)

# Глобальные экземпляры
_kafka_producer: Optional[AIOKafkaProducer] = None
_kafka_consumer: Optional[AIOKafkaConsumer] = None


async def get_kafka_producer(start_timeout: float = PRODUCER_START_TIMEOUT_DEFAULT) -> AIOKafkaProducer:
    """
    Получить или создать Kafka Producer

    Если producer уже создан, возвращает его.
    Если producer был закрыт или не подключен, создает новый.

    Args:
        start_timeout: Таймаут для запуска producer в секундах (по умолчанию 5 секунд)
                       Это не request_timeout_ms, а таймаут для операции start()
    """
    global _kafka_producer

    if _kafka_producer is not None:
        try:
            # Проверяем, что producer все еще активен
            if _kafka_producer._sender is not None:
                return _kafka_producer

            # Producer существует, но не подключен - пересоздаем
            logger.warning("Kafka Producer не подключен, пересоздаем...")
            _kafka_producer = None
        except Exception:
            # Producer в невалидном состоянии - пересоздаем
            logger.warning(
                "Kafka Producer в невалидном состоянии, пересоздаем..."
            )
            _kafka_producer = None

    # Создаем новый producer
    # request_timeout_ms остается 30000 (30 секунд) как было изначально
    _kafka_producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        # Сериализация в JSON будет в producer.py
        value_serializer=None,
        compression_type="gzip",  # Сжатие для экономии
        acks="all",  # Надежная доставка
        # retries параметр не поддерживается в AIOKafkaProducer
        # Повторные попытки обрабатываются автоматически через acks="all"
        request_timeout_ms=PRODUCER_REQUEST_TIMEOUT_MS,
    )

    try:
        # Пытаемся запустить producer с таймаутом для операции start()
        await asyncio.wait_for(_kafka_producer.start(), timeout=start_timeout)
        logger.info(
            "Kafka Producer запущен: %s", settings.kafka_bootstrap_servers
        )
    except asyncio.TimeoutError:
        logger.warning(
            "Kafka Producer не смог подключиться за %s секунд", start_timeout
        )
        _kafka_producer = None
        raise
    except Exception as e:
        logger.error("Ошибка при запуске Kafka Producer: %s", e)
        _kafka_producer = None
        raise

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
        auto_commit_interval_ms=CONSUMER_AUTO_COMMIT_INTERVAL_MS,
    )

    await consumer.start()
    logger.info("Kafka Consumer запущен: topic=%s, group=%s", topic, group_id)

    return consumer


async def _close_kafka_client(
    client, client_type: str, force_close_attr: Optional[str] = None
):
    """
    Общая функция для закрытия Kafka клиента (producer или consumer)

    Args:
        client: Экземпляр AIOKafkaProducer или AIOKafkaConsumer
        client_type: Тип клиента для логирования ("Producer" или "Consumer")
        force_close_attr: Имя атрибута для принудительного закрытия ("_sender" или "_coordinator")
    """
    if client is None:
        return

    try:
        # Останавливаем клиент с таймаутом, чтобы не зависать
        await asyncio.wait_for(client.stop(), timeout=CLIENT_STOP_TIMEOUT)
        logger.debug("Kafka %s stopped", client_type)
    except asyncio.TimeoutError:
        logger.warning("Kafka %s stop timeout, forcing close", client_type)
        # Пытаемся принудительно закрыть
        if force_close_attr:
            try:
                attr = getattr(client, force_close_attr, None)
                if attr:
                    attr.close()
            except Exception:
                pass
    except Exception as e:
        logger.debug("Error stopping Kafka %s: %s", client_type, e)


async def close_kafka_producer():
    """Закрыть Kafka Producer"""
    global _kafka_producer

    if _kafka_producer is not None:
        producer = _kafka_producer
        _kafka_producer = None  # Сбрасываем глобальную переменную сразу
        await _close_kafka_client(producer, "Producer", "_sender")


async def close_kafka_consumer(consumer: AIOKafkaConsumer):
    """
    Закрыть Kafka Consumer

    Args:
        consumer: Экземпляр consumer для закрытия
    """
    await _close_kafka_client(consumer, "Consumer", "_coordinator")


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


async def connect_kafka(max_retries: int = CONNECT_KAFKA_MAX_RETRIES, fast_mode: bool = False) -> bool:
    """
    Подключение к Kafka с повторными попытками

    Args:
        max_retries: Максимальное количество попыток подключения
        fast_mode: Если True, использует короткие задержки (для тестов)

    Пытается подключиться к Kafka с экспоненциальной задержкой.
    По умолчанию: максимум N попыток с задержками: 1s, 2s, 4s, 8s, 16s
    В fast_mode: максимум N попытки с задержками: 0.1s, 0.2s, 0.4s
    """
    if fast_mode:
        base_delay = CONNECT_KAFKA_BASE_DELAY_FAST
    else:
        base_delay = CONNECT_KAFKA_BASE_DELAY_NORMAL

    for attempt in range(max_retries):
        try:
            await get_kafka_producer()
            if not fast_mode:
                print("✅ Kafka Producer подключен")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                if not fast_mode:
                    logger.warning(
                        "Kafka недоступна (попытка %d/%d): %s. Повтор через %.1fс...",
                        attempt + 1,
                        max_retries,
                        e,
                        delay,
                    )
                await asyncio.sleep(delay)
            else:
                logger.debug(
                    "Kafka unavailable после %d попыток: %s", max_retries, e
                )
                return False

    return False
