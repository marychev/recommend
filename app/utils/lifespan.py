from contextlib import asynccontextmanager
import asyncio
from typing import Optional

from fastapi import FastAPI

from app.config import settings
from app.db.clickhouse import connect_clickhouse, shutdown_clickhouse
from app.services.cache_redis_client import connect_redis, shutdown_redis
from app.services.event_queue import start_event_queue, stop_event_queue
from app.kafka.client import close_kafka_producer, connect_kafka
from app.kafka.consumer import start_background_consumer
from app.kafka.event_handler import process_event_handler
from app.utils.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("Запуск приложения Music Recommendation System...")

    clickhouse_connected = await connect_clickhouse()
    redis_connected = await connect_redis()
    kafka_connected = await connect_kafka()
    
    consumer_task: Optional[asyncio.Task] = None
    
    # Запускаем очередь для батчинга событий в Kafka
    if kafka_connected:
        await start_event_queue()
        logger.info("Очередь событий запущена (батчинг Kafka)")
        
        # Запускаем Kafka Consumer для обработки событий
        try:
            consumer_task = await start_background_consumer(process_event_handler)
            logger.info("Kafka Consumer запущен (обработка событий)")
        except Exception as e:
            logger.warning("Не удалось запустить Kafka Consumer: %s", e)
            logger.warning("Kafka Consumer не запущен: %s", e)

    logger.info("=" * 60)
    if clickhouse_connected and redis_connected and kafka_connected:
        logger.info("Все сервисы подключены!")
    elif clickhouse_connected and redis_connected:
        logger.warning("Приложение запущено (Kafka недоступна)")
    elif clickhouse_connected:
        logger.warning("Приложение запущено (Redis и Kafka недоступны)")
    else:
        logger.error("ВНИМАНИЕ: ClickHouse не подключен!")
        logger.error("API будет возвращать ошибки до подключения к ClickHouse")

    logger.info(
        "API доступен на: http://%s:%s",
        settings.api_host, settings.api_port
    )
    logger.info("Документация: http://localhost:%s/docs", settings.api_port)
    logger.info("Kafka topic: %s", settings.kafka_topic_events)
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("=" * 60)
    logger.info("Остановка приложения...")
    logger.info("=" * 60)

    # Останавливаем Kafka Consumer
    if consumer_task is not None:
        try:
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
            logger.info("Kafka Consumer остановлен")
        except Exception as e:
            logger.warning("Ошибка при остановке Consumer: %s", e)

    # Останавливаем очередь событий (сбросит оставшиеся события)
    await stop_event_queue()
    
    await close_kafka_producer()
    await shutdown_clickhouse()
    await shutdown_redis()
