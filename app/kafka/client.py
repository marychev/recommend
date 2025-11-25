from typing import Optional
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError
import logging
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)

# Глобальные экземпляры
_kafka_producer: Optional[AIOKafkaProducer] = None
_kafka_consumer: Optional[AIOKafkaConsumer] = None


async def get_kafka_producer(start_timeout: float = 5.0) -> AIOKafkaProducer:
    """
    Получить или создать Kafka Producer
    
    Если producer уже создан, возвращает его.
    Если producer был закрыт или не подключен, создает новый.
    
    Args:
        start_timeout: Таймаут для запуска producer в секундах (по умолчанию 5 секунд)
                       Это не request_timeout_ms, а таймаут для операции start()
    """
    global _kafka_producer

    # Проверяем, существует ли producer и подключен ли он
    if _kafka_producer is not None:
        try:
            # Проверяем, что producer все еще активен
            if _kafka_producer._sender is not None:
                return _kafka_producer
            else:
                # Producer существует, но не подключен - пересоздаем
                logger.warning("Kafka Producer не подключен, пересоздаем...")
                _kafka_producer = None
        except Exception:
            # Producer в невалидном состоянии - пересоздаем
            logger.warning("Kafka Producer в невалидном состоянии, пересоздаем...")
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
        request_timeout_ms=30000,  # Таймаут для запросов (30 секунд)
    )
    
    try:
        # Пытаемся запустить producer с таймаутом для операции start()
        await asyncio.wait_for(_kafka_producer.start(), timeout=start_timeout)
        logger.info(
            f"✅ Kafka Producer запущен: "
            f"{settings.kafka_bootstrap_servers}"
        )
    except asyncio.TimeoutError:
        logger.warning(f"Kafka Producer не смог подключиться за {start_timeout} секунд")
        _kafka_producer = None
        raise
    except Exception as e:
        logger.error(f"Ошибка при запуске Kafka Producer: {e}")
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
        auto_commit_interval_ms=5000,
    )

    await consumer.start()
    logger.info(f"✅ Kafka Consumer запущен: topic={topic}, group={group_id}")

    return consumer


async def close_kafka_producer():
    """Закрыть Kafka Producer"""
    global _kafka_producer

    if _kafka_producer is not None:
        producer = _kafka_producer
        _kafka_producer = None  # Сбрасываем глобальную переменную сразу
        
        try:
            # Останавливаем producer с таймаутом, чтобы не зависать
            await asyncio.wait_for(producer.stop(), timeout=3.0)
            logger.debug("Kafka Producer stopped")
        except asyncio.TimeoutError:
            logger.warning("Kafka Producer stop timeout, forcing close")
            # Пытаемся принудительно закрыть
            try:
                if hasattr(producer, '_sender') and producer._sender:
                    producer._sender.close()
            except Exception:
                pass
        except Exception as e:
            logger.debug("Error stopping Kafka Producer: %s", e)


async def close_kafka_consumer(consumer: AIOKafkaConsumer):
    """
    Закрыть Kafka Consumer

    Args:
        consumer: Экземпляр consumer для закрытия
    """
    if consumer is not None:
        try:
            # Останавливаем consumer с таймаутом
            await asyncio.wait_for(consumer.stop(), timeout=3.0)
            logger.debug("Kafka Consumer stopped")
        except asyncio.TimeoutError:
            logger.warning("Kafka Consumer stop timeout, forcing close")
            # Пытаемся принудительно закрыть
            try:
                if hasattr(consumer, '_coordinator') and consumer._coordinator:
                    consumer._coordinator.close()
            except Exception:
                pass
        except Exception as e:
            logger.debug("Error stopping Kafka Consumer: %s", e)


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


async def connect_kafka(max_retries: int = 5, fast_mode: bool = False) -> bool:
    """
    Подключение к Kafka с повторными попытками
    
    Args:
        max_retries: Максимальное количество попыток подключения
        fast_mode: Если True, использует короткие задержки (для тестов)
    
    Пытается подключиться к Kafka с экспоненциальной задержкой.
    По умолчанию: максимум 5 попыток с задержками: 1s, 2s, 4s, 8s, 16s
    В fast_mode: максимум 3 попытки с задержками: 0.1s, 0.2s, 0.4s
    """
    if fast_mode:
        base_delay = 0.1  # Быстрые задержки для тестов
        max_retries = min(max_retries, 3)  # Максимум 3 попытки в fast режиме
    else:
        base_delay = 1.0  # Обычные задержки
    
    for attempt in range(max_retries):
        try:
            await get_kafka_producer()
            if not fast_mode:
                print("✅ Kafka Producer подключен")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                if not fast_mode:
                    logger.warning(
                        "Kafka недоступна (попытка %d/%d): %s. Повтор через %.1fс...",
                        attempt + 1,
                        max_retries,
                        e,
                        delay
                    )
                await asyncio.sleep(delay)
            else:
                if not fast_mode:
                    logger.warning("Kafka unavailable после %d попыток: %s", max_retries, e)
                    print("⚠️  Kafka недоступна (события не будут отправляться)")
                    print(f"   Последняя ошибка: {e}")
                else:
                    logger.debug("Kafka unavailable после %d попыток: %s", max_retries, e)
                return False
    
    return False
