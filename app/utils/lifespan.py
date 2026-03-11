from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI

from app.config import settings
from app.db.clickhouse import (
    connect_clickhouse,
    shutdown_clickhouse,
    get_clickhouse_client,
)
from app.services.cache_redis_client import connect_redis, shutdown_redis
from app.services.cache import get_cached_popular_tracks, set_cached_popular_tracks
from app.services.event_queue import start_event_queue, stop_event_queue
from app.kafka.client import close_kafka_producer, connect_kafka
from app.kafka.multi_consumer import start_multi_consumer, stop_multi_consumer
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("Запуск приложения Music Recommendation System...")

    clickhouse_connected = await connect_clickhouse()
    redis_connected = await connect_redis()
    kafka_connected = await connect_kafka()
    
    # Запускаем периодический flush буферов ClickHouse (для fallback механизма)
    if clickhouse_connected:
        try:
            clickhouse = get_clickhouse_client()
            await clickhouse.start_periodic_flush()
            logger.info("Периодический flush буферов ClickHouse запущен (интервал: 5 сек)")
        except Exception as e:
            logger.warning("Не удалось запустить периодический flush ClickHouse: %s", e)
    
    consumer_tasks: list[asyncio.Task] = []
    
    # Запускаем очередь для батчинга событий в Kafka (для отправки)
    if kafka_connected:
        await start_event_queue()
        logger.info("Очередь событий запущена (батчинг Kafka)")
        
        # Запускаем мульти-consumer для обработки всех топиков (users, tracks, events)
        # Consumer будет писать в ClickHouse батчами
        if clickhouse_connected:
            # Ждем, пока Kafka полностью запустится (особенно Group Coordinator)
            # Это предотвращает ошибки CoordinatorNotAvailableError
            # logger.info("Ожидание готовности Kafka (Group Coordinator)...")
            # await asyncio.sleep(5)  # Даем Kafka время на инициализацию
            
            try:
                consumer_tasks = await start_multi_consumer()
                logger.info("Kafka Multi-Consumer запущен (обработка users, tracks, events → ClickHouse)")
            except Exception as e:
                logger.warning("Не удалось запустить Kafka Multi-Consumer: %s", e)
                logger.warning("Consumer будет переподключаться автоматически при появлении сообщений")

    # Прогрев кэша популярных треков при старте
    if clickhouse_connected and redis_connected:
        try:
            cached = await get_cached_popular_tracks(10)
            if cached is None:
                clickhouse = get_clickhouse_client()
                # Двухэтапный запрос: сначала top IDs, потом детали
                top_ids = await clickhouse.execute("""
                    SELECT track_id, count(*) as play_count
                    FROM user_track_interactions
                    WHERE action_type = 'play'
                    GROUP BY track_id ORDER BY play_count DESC LIMIT 10
                    SETTINGS max_memory_usage=2000000000
                """)
                result_serializable = []
                if top_ids:
                    play_counts = {row[0]: row[1] for row in top_ids}
                    ids_str = ",".join(str(row[0]) for row in top_ids)
                    details = await clickhouse.execute(f"""
                        SELECT track_id, title, artist, album, genre,
                               duration_seconds, release_year, created_at
                        FROM tracks WHERE track_id IN ({ids_str})
                    """)
                    for row in details:
                        result_serializable.append(
                            [row[i] for i in range(8)] + [play_counts.get(row[0], 0)]
                        )
                    result_serializable.sort(key=lambda r: r[8], reverse=True)
                await set_cached_popular_tracks(10, result_serializable)
                logger.info("Кэш популярных треков прогрет (%d треков)", len(result_serializable))
            else:
                logger.info("Кэш популярных треков уже заполнен")
        except Exception as e:
            logger.warning("Не удалось прогреть кэш популярных треков: %s", e)

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

    # Останавливаем Kafka Multi-Consumer
    if consumer_tasks:
        try:
            await stop_multi_consumer(consumer_tasks)
            logger.info("Kafka Multi-Consumer остановлен")
        except Exception as e:
            logger.warning("Ошибка при остановке Multi-Consumer: %s", e)

    # Останавливаем очередь событий (сбросит оставшиеся события)
    await stop_event_queue()
    
    # Останавливаем периодический flush ClickHouse (сбросит все буферы)
    try:
        clickhouse = get_clickhouse_client()
        await clickhouse.stop_periodic_flush()
        logger.info("Периодический flush ClickHouse остановлен")
    except Exception as e:
        logger.warning("Ошибка при остановке периодического flush ClickHouse: %s", e)
    
    await close_kafka_producer()
    await shutdown_clickhouse()
    await shutdown_redis()
