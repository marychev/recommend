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
    try:
        users_handler = create_topic_handler("users")
        users_task = asyncio.create_task(
            consume_events(users_handler, settings.kafka_topic_users, f"{settings.kafka_consumer_group}_users")
        )
        tasks.append(users_task)
        logger.info("Consumer для топика 'users' запущен")
    except Exception as e:
        logger.warning("Не удалось запустить consumer для users: %s", e)
    
    # Запускаем consumer для tracks
    try:
        tracks_handler = create_topic_handler("tracks")
        tracks_task = asyncio.create_task(
            consume_events(tracks_handler, settings.kafka_topic_tracks, f"{settings.kafka_consumer_group}_tracks")
        )
        tasks.append(tracks_task)
        logger.info("Consumer для топика 'tracks' запущен")
    except Exception as e:
        logger.warning("Не удалось запустить consumer для tracks: %s", e)
    
    # Запускаем consumer для events
    try:
        events_handler = create_topic_handler("user_track_events")
        events_task = asyncio.create_task(
            consume_events(events_handler, settings.kafka_topic_events, f"{settings.kafka_consumer_group}_events")
        )
        tasks.append(events_task)
        logger.info("Consumer для топика 'user_track_events' запущен")
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

