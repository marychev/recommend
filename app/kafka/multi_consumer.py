"""
Мульти-consumer для обработки нескольких Kafka топиков

Обрабатывает:
- users - пользователи
- tracks - треки  
- user_track_events - события взаимодействий
"""

import asyncio
import logging
from typing import Optional

from app.kafka.consumer import consume_events
from app.kafka.data_handler import process_kafka_message, get_data_handler
from app.kafka.constants import (
    CONSUMER_MAX_RETRIES,
    CONSUMER_RETRY_DELAY_INITIAL,
)
from app.config import settings

logger = logging.getLogger(__name__)


async def start_multi_consumer() -> list[asyncio.Task]:
    """
    Запустить consumers для всех топиков
    
    Returns:
        list[asyncio.Task]: Список задач consumers
    """
    tasks = []
    
    # Запускаем периодический flush для батчинга
    handler = get_data_handler()
    await handler.start_periodic_flush()
    
    # Создаем обработчик для каждого топика
    def create_topic_handler(topic: str):
        async def handler(message: dict):
            await process_kafka_message(topic, message)
        return handler
    
    # Запускаем consumer для users
    # Используем обертку для автоматического переподключения при ошибках
    async def start_consumer_with_retry(topic_name: str, topic_config: str, consumer_group_suffix: str):
        """Запустить consumer с автоматическим переподключением"""
        max_retries = CONSUMER_MAX_RETRIES
        retry_delay = CONSUMER_RETRY_DELAY_INITIAL
        
        for attempt in range(max_retries):
            try:
                handler = create_topic_handler(topic_name)
                await consume_events(handler, topic_config, f"{settings.kafka_consumer_group}_{consumer_group_suffix}")
                return  # Успешно запущен
            except Exception as e:
                error_str = str(e)
                if "CoordinatorNotAvailable" in error_str or "15" in error_str:
                    if attempt < max_retries - 1:
                        logger.warning(
                            "Kafka Coordinator не готов для %s (попытка %d/%d), повтор через %d сек...",
                            topic_name, attempt + 1, max_retries, retry_delay
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Экспоненциальная задержка
                    else:
                        logger.error("Не удалось запустить consumer для %s после %d попыток: %s", topic_name, max_retries, e)
                        raise
                else:
                    logger.error("Ошибка при запуске consumer для %s: %s", topic_name, e)
                    raise
    
    # Запускаем consumers в фоне с обработкой ошибок
    try:
        users_task = asyncio.create_task(
            start_consumer_with_retry("users", settings.kafka_topic_users, "users")
        )
        tasks.append(users_task)
        logger.info("Consumer для топика 'users' запускается...")
    except Exception as e:
        logger.warning("Не удалось запустить consumer для users: %s", e)
    
    try:
        tracks_task = asyncio.create_task(
            start_consumer_with_retry("tracks", settings.kafka_topic_tracks, "tracks")
        )
        tasks.append(tracks_task)
        logger.info("Consumer для топика 'tracks' запускается...")
    except Exception as e:
        logger.warning("Не удалось запустить consumer для tracks: %s", e)
    
    try:
        events_task = asyncio.create_task(
            start_consumer_with_retry("user_track_events", settings.kafka_topic_events, "events")
        )
        tasks.append(events_task)
        logger.info("Consumer для топика 'user_track_events' запускается...")
    except Exception as e:
        logger.warning("Не удалось запустить consumer для events: %s", e)
    
    return tasks


async def stop_multi_consumer(tasks: list[asyncio.Task]) -> None:
    """Остановить все consumers"""
    # Останавливаем периодический flush
    handler = get_data_handler()
    await handler.stop_periodic_flush()
    
    # Отменяем все задачи
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    logger.info("Все Kafka consumers остановлены")

