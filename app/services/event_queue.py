"""
Очередь для батчинга событий перед отправкой в Kafka

Преимущества:
- Меньше запросов к Kafka (50 событий в одном запросе)
- Лучшая пропускная способность
- Меньше нагрузка на Kafka broker
"""

from collections import deque
import asyncio
from typing import Deque, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EventQueue:
    """Очередь для батчинга событий перед отправкой в Kafka"""

    def __init__(self, batch_size: int = 50, flush_interval: float = 2.0):
        """
        Args:
            batch_size: Размер батча для отправки (по умолчанию 50)
            flush_interval: Интервал автоматического сброса в секундах (по умолчанию 2.0)
        """
        self._queue: Deque[Dict[str, Any]] = deque()
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

    async def add_event(self, event: Dict[str, Any]):
        """
        Добавить событие в очередь

        Args:
            event: Словарь с данными события
        """
        async with self._lock:
            self._queue.append(event)
            logger.debug(f"Event added to queue. Queue size: {len(self._queue)}")

            # Если очередь заполнена, сбрасываем немедленно
            if len(self._queue) >= self._batch_size:
                # Запускаем flush в фоне, не блокируя
                asyncio.create_task(self._flush())

    async def _flush(self):
        """Отправить батч событий в Kafka"""
        if not self._queue:
            return

        events = []
        async with self._lock:
            # Берем события из очереди
            while self._queue and len(events) < self._batch_size:
                events.append(self._queue.popleft())

        if events:
            try:
                from app.kafka.producer import send_batch_events
                sent_count = await send_batch_events(events)
                logger.info(
                    f"Flushed {sent_count}/{len(events)} events to Kafka"
                )
            except Exception as e:
                logger.error(f"Error flushing events to Kafka: {e}")
                # Возвращаем события обратно в очередь при ошибке
                async with self._lock:
                    self._queue.extendleft(reversed(events))

    async def start_periodic_flush(self):
        """Запустить периодический сброс очереди"""
        if self._running:
            return

        self._running = True

        async def flush_loop():
            while self._running:
                try:
                    await asyncio.sleep(self._flush_interval)
                    await self._flush()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in flush loop: {e}")

        self._flush_task = asyncio.create_task(flush_loop())
        logger.info(
            f"Started periodic flush: interval={self._flush_interval}s, "
            f"batch_size={self._batch_size}"
        )

    async def stop(self):
        """Остановить периодический сброс и сбросить оставшиеся события"""
        self._running = False

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Сбрасываем оставшиеся события
        await self._flush()
        logger.info("Event queue stopped")

    def get_queue_size(self) -> int:
        """Получить текущий размер очереди"""
        return len(self._queue)


# Глобальная очередь событий
_event_queue: Optional[EventQueue] = None


def get_event_queue() -> EventQueue:
    """Получить глобальную очередь событий"""
    global _event_queue
    if _event_queue is None:
        _event_queue = EventQueue(
            batch_size=50,  # Можно настроить через env
            flush_interval=2.0  # Можно настроить через env
        )
    return _event_queue


async def start_event_queue():
    """Запустить глобальную очередь событий"""
    queue = get_event_queue()
    await queue.start_periodic_flush()


async def stop_event_queue():
    """Остановить глобальную очередь событий"""
    global _event_queue
    if _event_queue:
        await _event_queue.stop()
        _event_queue = None

