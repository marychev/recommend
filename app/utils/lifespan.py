from contextlib import asynccontextmanager
import logging
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

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    print("🚀 Запуск приложения Music Recommendation System...")

    clickhouse_connected = await connect_clickhouse()
    redis_connected = await connect_redis()
    kafka_connected = await connect_kafka()
    
    consumer_task: Optional[asyncio.Task] = None
    
    # Запускаем очередь для батчинга событий в Kafka
    if kafka_connected:
        await start_event_queue()
        print("✅ Очередь событий запущена (батчинг Kafka)")
        
        # Запускаем Kafka Consumer для обработки событий
        try:
            consumer_task = await start_background_consumer(process_event_handler)
            print("✅ Kafka Consumer запущен (обработка событий)")
        except Exception as e:
            logger.warning(f"Не удалось запустить Kafka Consumer: {e}")
            print(f"⚠️  Kafka Consumer не запущен: {e}")

    print("\n" + "=" * 60)
    if clickhouse_connected and redis_connected and kafka_connected:
        print("✅ Все сервисы подключены!")
    elif clickhouse_connected and redis_connected:
        print("⚠️  Приложение запущено (Kafka недоступна)")
    elif clickhouse_connected:
        print("⚠️  Приложение запущено (Redis и Kafka недоступны)")
    else:
        print("❌ ВНИМАНИЕ: ClickHouse не подключен!")
        print("   API будет возвращать ошибки " "до подключения к ClickHouse")

    print("=" * 60)
    print(
        f"\n🌐 API доступен на: "
        f"http://{settings.api_host}:{settings.api_port}"
    )
    print(f"📚 Документация: http://localhost:{settings.api_port}/docs")
    print(f"📨 Kafka topic: {settings.kafka_topic_events}")
    print("=" * 60 + "\n")

    yield

    # Shutdown
    print("\n" + "=" * 60)
    print("🛑 Остановка приложения...")
    print("=" * 60)

    # Останавливаем Kafka Consumer
    if consumer_task is not None:
        try:
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
            print("✅ Kafka Consumer остановлен")
        except Exception as e:
            logger.warning(f"Ошибка при остановке Consumer: {e}")

    # Останавливаем очередь событий (сбросит оставшиеся события)
    await stop_event_queue()
    
    await close_kafka_producer()
    await shutdown_clickhouse()
    await shutdown_redis()
