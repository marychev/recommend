from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.config import settings
from app.db.clickhouse import connect_clickhouse, shutdown_clickhouse
from app.db.redis_client import connect_redis, shutdown_redis
from app.kafka.client import get_kafka_producer, close_kafka_producer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    print("="*60)
    print("🚀 Запуск приложения Music Recommendation System...")
    print("="*60)

    clickhouse_connected = await connect_clickhouse()
    redis_connected = await connect_redis()
    
    # Подключаемся к Kafka
    kafka_connected = False
    try:
        await get_kafka_producer()
        kafka_connected = True
        print("✅ Kafka Producer подключен")
    except Exception as e:
        logger.warning(f"⚠️  Kafka недоступна: {e}")
        print("⚠️  Kafka недоступна (события не будут отправляться)")

    print("\n" + "="*60)
    if clickhouse_connected and redis_connected and kafka_connected:
        print("✅ Все сервисы подключены!")
    elif clickhouse_connected and redis_connected:
        print("⚠️  Приложение запущено (Kafka недоступна)")
    elif clickhouse_connected:
        print("⚠️  Приложение запущено (Redis и Kafka недоступны)")
    else:
        print("❌ ВНИМАНИЕ: ClickHouse не подключен!")
        print(
            "   API будет возвращать ошибки "
            "до подключения к ClickHouse"
        )

    print("="*60)
    print(
        f"\n🌐 API доступен на: "
        f"http://{settings.api_host}:{settings.api_port}"
    )
    print(f"📚 Документация: http://localhost:{settings.api_port}/docs")
    print(f"📨 Kafka topic: {settings.kafka_topic_events}")
    print("="*60 + "\n")

    yield

    # Shutdown
    print("\n" + "="*60)
    print("🛑 Остановка приложения...")
    print("="*60)

    await close_kafka_producer()
    await shutdown_clickhouse()
    await shutdown_redis()
    