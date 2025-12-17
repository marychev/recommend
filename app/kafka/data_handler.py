"""
Универсальный обработчик данных из Kafka для записи в ClickHouse

Обрабатывает:
- users - пользователи
- tracks - треки
- events - события взаимодействий

Все данные записываются в ClickHouse батчами для оптимизации.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from collections import deque
import asyncio

from app.db.clickhouse import get_clickhouse_client
from app.models.schemas import User, Track, UserTrackInteraction
from app.services.cache_redis_client import get_redis_client
from app.models.schemas.action_type import ActionType
from app.kafka.constants import (
    DATA_HANDLER_BATCH_SIZE,
    DATA_HANDLER_FLUSH_INTERVAL,
)

logger = logging.getLogger(__name__)


class KafkaDataHandler:
    """Обработчик данных из Kafka с батчингом для ClickHouse"""
    def __init__(self, batch_size: int = DATA_HANDLER_BATCH_SIZE, flush_interval: float = DATA_HANDLER_FLUSH_INTERVAL):
        """
        Args:
            batch_size: Размер батча для записи в ClickHouse (увеличен для лучшей производительности)
            flush_interval: Интервал автоматического flush в секундах (уменьшен для более быстрой обработки)
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Буферы для батчинга
        self._buffers = {
            'users': deque(),
            'tracks': deque(),
            'events': deque(),
        }
        self._flush_lock = asyncio.Lock()
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None

    async def handle_user(self, user_data: Dict[str, Any]) -> None:
        """Обработать пользователя из Kafka"""
        try:
            async with self._flush_lock:
                self._buffers['users'].append([
                    user_data['user_id'],
                    user_data['username'],
                    user_data.get('email', ''),
                    user_data.get('age', 0),
                    user_data.get('country', ''),
                    self._parse_datetime(user_data.get('created_at')),
                ])
                
                # Если буфер заполнен, запускаем flush
                if len(self._buffers['users']) >= self.batch_size:
                    asyncio.create_task(self._flush_buffer('users'))
                    
        except Exception as e:
            logger.error("Ошибка обработки пользователя: %s", e, extra={"user": user_data})

    async def handle_track(self, track_data: Dict[str, Any]) -> None:
        """Обработать трек из Kafka"""
        try:
            async with self._flush_lock:
                self._buffers['tracks'].append([
                    track_data['track_id'],
                    track_data['title'],
                    track_data['artist'],
                    track_data.get('album', ''),
                    track_data.get('genre', ''),
                    track_data.get('duration_seconds', 0),
                    track_data.get('release_year', 0),
                    self._parse_datetime(track_data.get('created_at')),
                ])
                
                # Если буфер заполнен, запускаем flush
                if len(self._buffers['tracks']) >= self.batch_size:
                    asyncio.create_task(self._flush_buffer('tracks'))
                    
        except Exception as e:
            logger.error("Ошибка обработки трека: %s", e, extra={"track": track_data})

    async def handle_event(self, event_data: Dict[str, Any]) -> None:
        """Обработать событие из Kafka"""
        try:
            # Обновляем метрики в Redis (как было раньше)
            await self._update_analytics_metrics(event_data)
            
            # Добавляем в буфер для записи в ClickHouse
            async with self._flush_lock:
                action_type = event_data.get('action_type')
                # Преобразуем action_type в значение для ClickHouse
                if isinstance(action_type, str):
                    # Если это строка, используем как есть (уже значение Enum)
                    action_value = action_type
                elif hasattr(action_type, 'value'):
                    # Если это Enum, берем значение
                    action_value = action_type.value
                else:
                    action_value = str(action_type)
                
                self._buffers['events'].append([
                    event_data['user_id'],
                    event_data['track_id'],
                    action_value,
                    event_data.get('listen_duration_seconds'),
                    self._parse_datetime(event_data.get('timestamp')),
                ])
                
                # Если буфер заполнен, запускаем flush
                if len(self._buffers['events']) >= self.batch_size:
                    asyncio.create_task(self._flush_buffer('events'))
                    
        except Exception as e:
            logger.error("Ошибка обработки события: %s", e, extra={"event": event_data})

    async def _flush_buffer(self, table: str) -> None:
        """Сбросить буфер в ClickHouse"""
        async with self._flush_lock:
            buffer = self._buffers[table]
            if not buffer:
                return
            
            records = list(buffer)
            buffer.clear()
        
        if not records:
            return
        
        try:
            clickhouse = get_clickhouse_client()
            
            # Определяем column_names в зависимости от таблицы
            if table == 'users':
                column_names = User.column_names()
            elif table == 'tracks':
                column_names = Track.column_names()
            elif table == 'events':
                column_names = UserTrackInteraction.column_names()
            else:
                column_names = None
            
            # Выполняем батч INSERT
            await clickhouse.insert(table, records, column_names)
            
            logger.info(
                "Батч INSERT выполнен из Kafka: table=%s, records=%s",
                table,
                len(records),
            )
        except Exception as e:
            logger.error(
                "Ошибка при flush буфера %s: %s. Возвращаем записи в буфер.",
                table,
                e,
            )
            # При ошибке возвращаем записи обратно в буфер
            async with self._flush_lock:
                self._buffers[table].extendleft(reversed(records))

    async def _flush_all_buffers(self) -> None:
        """Сбросить все буферы"""
        for table in self._buffers.keys():
            await self._flush_buffer(table)

    async def start_periodic_flush(self) -> None:
        """Запустить периодический flush"""
        if self._running:
            return
        
        self._running = True
        
        async def flush_loop():
            while self._running:
                try:
                    await asyncio.sleep(self.flush_interval)
                    await self._flush_all_buffers()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("Ошибка в цикле flush: %s", e)
        
        self._flush_task = asyncio.create_task(flush_loop())
        logger.info(
            "Запущен периодический flush для Kafka Consumer: interval=%.1fs, batch_size=%s",
            self.flush_interval,
            self.batch_size,
        )

    async def stop_periodic_flush(self) -> None:
        """Остановить периодический flush и сбросить все буферы"""
        self._running = False
        
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Сбрасываем все буферы перед остановкой
        await self._flush_all_buffers()
        logger.info("Периодический flush Kafka Consumer остановлен, все буферы сброшены")

    def _parse_datetime(self, value: Any) -> datetime:
        """Парсинг datetime из различных форматов"""
        if value is None:
            return datetime.now()
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return datetime.now()
        return datetime.now()

    async def _update_analytics_metrics(self, event_data: Dict[str, Any]) -> None:
        """Обновить метрики аналитики в Redis (как в event_handler)"""
        try:
            redis_client = get_redis_client()
            if not await redis_client.is_connected():
                return

            user_id = event_data.get("user_id")
            track_id = event_data.get("track_id")
            action_type = event_data.get("action_type")

            if not all([user_id, track_id, action_type]):
                return

            if redis_client.redis is None:
                return

            redis = redis_client.redis

            # Счетчики по типам действий
            action_key = f"analytics:action:{action_type}:count"
            await redis.incr(action_key)
            await redis.expire(action_key, 86400 * 7)

            # Популярность треков
            if action_type == ActionType.PLAY.value:
                track_plays_key = f"analytics:track:{track_id}:plays"
                await redis.incr(track_plays_key)
                await redis.expire(track_plays_key, 86400 * 30)

            # Лайки треков
            if action_type == ActionType.LIKE.value:
                track_likes_key = f"analytics:track:{track_id}:likes"
                await redis.incr(track_likes_key)
                await redis.expire(track_likes_key, 86400 * 30)

            # Активность пользователя
            user_activity_key = f"analytics:user:{user_id}:activity"
            await redis.incr(user_activity_key)
            await redis.expire(user_activity_key, 86400 * 7)

            # Последняя активность
            user_last_activity_key = f"analytics:user:{user_id}:last_activity"
            await redis.set(
                user_last_activity_key,
                datetime.now().isoformat(),
                ex=86400 * 7,
            )

        except Exception as e:
            logger.error("Ошибка обновления метрик: %s", e)


# Глобальный обработчик
_data_handler: Optional[KafkaDataHandler] = None


def get_data_handler() -> KafkaDataHandler:
    """Получить глобальный обработчик данных"""
    global _data_handler
    if _data_handler is None:
        _data_handler = KafkaDataHandler(
            batch_size=DATA_HANDLER_BATCH_SIZE,
            flush_interval=DATA_HANDLER_FLUSH_INTERVAL
        )
    return _data_handler


async def process_kafka_message(topic: str, message: Dict[str, Any]) -> None:
    """
    Универсальный обработчик сообщений из Kafka
    
    Args:
        topic: Название топика (users, tracks, user_track_events)
        message: Десериализованное сообщение
    """
    handler = get_data_handler()
    
    if topic == "users":
        await handler.handle_user(message)
    elif topic == "tracks":
        await handler.handle_track(message)
    elif topic == "user_track_events":
        await handler.handle_event(message)
    else:
        logger.warning("Неизвестный топик: %s", topic)

