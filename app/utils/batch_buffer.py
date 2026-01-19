"""
Переиспользуемый буфер для батчинга INSERT операций в ClickHouse.

Устраняет дублирование кода между ClickHouseClient и KafkaDataHandler.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Awaitable
from collections import deque

logger = logging.getLogger(__name__)


class BatchBuffer:
    """
    Универсальный буфер для батчинга данных перед записью.
    
    Поддерживает:
    - Автоматический flush при заполнении буфера
    - Периодический flush по таймеру
    - Возврат записей в буфер при ошибках
    - Thread-safe операции через asyncio.Lock
    
    Example:
        ```python
        async def flush_to_db(table: str, records: List):
            await clickhouse.insert(table, records)
        
        buffer = BatchBuffer(
            tables=['users', 'tracks'],
            batch_size=100,
            flush_interval=5.0,
            flush_callback=flush_to_db
        )
        
        await buffer.start()
        await buffer.add('users', [1, 'john', 'john@example.com'])
        await buffer.stop()  # Сбросит все оставшиеся записи
        ```
    """
    
    def __init__(
        self,
        tables: List[str],
        batch_size: int = 100,
        flush_interval: float = 5.0,
        flush_callback: Optional[Callable[[str, List[List[Any]]], Awaitable[None]]] = None,
        name: str = "BatchBuffer",
    ):
        """
        Args:
            tables: Список имен таблиц/буферов
            batch_size: Размер батча для автоматического flush
            flush_interval: Интервал периодического flush в секундах
            flush_callback: Async функция для записи данных (table, records) -> None
            name: Имя буфера для логирования
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.flush_callback = flush_callback
        self.name = name
        
        # Создаем буферы для каждой таблицы
        self._buffers: Dict[str, deque] = {table: deque() for table in tables}
        self._flush_lock = asyncio.Lock()
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None
    
    async def add(self, table: str, record: List[Any]) -> None:
        """
        Добавить запись в буфер.
        
        Args:
            table: Имя таблицы/буфера
            record: Список значений для INSERT
        """
        if table not in self._buffers:
            raise ValueError(f"Unknown table: {table}")
        
        async with self._flush_lock:
            self._buffers[table].append(record)
            
            # Если буфер заполнен, запускаем flush
            if len(self._buffers[table]) >= self.batch_size:
                asyncio.create_task(self._flush_buffer(table))
    
    async def add_batch(self, table: str, records: List[List[Any]]) -> None:
        """
        Добавить несколько записей в буфер.
        
        Args:
            table: Имя таблицы/буфера
            records: Список записей
        """
        for record in records:
            await self.add(table, record)
    
    def get_buffer_size(self, table: str) -> int:
        """Получить текущий размер буфера для таблицы."""
        return len(self._buffers.get(table, []))
    
    def get_total_size(self) -> int:
        """Получить общий размер всех буферов."""
        return sum(len(buf) for buf in self._buffers.values())
    
    async def _flush_buffer(self, table: str) -> None:
        """Сбросить буфер в хранилище."""
        async with self._flush_lock:
            buffer = self._buffers[table]
            if not buffer:
                return
            
            records = list(buffer)
            buffer.clear()
        
        if not records:
            return
        
        try:
            if self.flush_callback:
                await self.flush_callback(table, records)
            
            logger.debug(
                "[%s] Flush выполнен: table=%s, records=%s",
                self.name, table, len(records)
            )
        except Exception as e:
            logger.error(
                "[%s] Ошибка flush буфера %s: %s. Возвращаем записи.",
                self.name, table, e
            )
            # При ошибке возвращаем записи обратно в буфер
            async with self._flush_lock:
                self._buffers[table].extendleft(reversed(records))
    
    async def _flush_all(self) -> None:
        """Сбросить все буферы."""
        for table in self._buffers.keys():
            await self._flush_buffer(table)
    
    async def start(self) -> None:
        """Запустить периодический flush."""
        if self._running:
            return
        
        self._running = True
        
        async def flush_loop():
            while self._running:
                try:
                    await asyncio.sleep(self.flush_interval)
                    await self._flush_all()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("[%s] Ошибка в цикле flush: %s", self.name, e)
        
        self._flush_task = asyncio.create_task(flush_loop())
        logger.info(
            "[%s] Периодический flush запущен: interval=%.1fs, batch_size=%s",
            self.name, self.flush_interval, self.batch_size
        )
    
    async def stop(self) -> None:
        """Остановить периодический flush и сбросить все буферы."""
        self._running = False
        
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Сбрасываем все буферы перед остановкой
        await self._flush_all()
        logger.info("[%s] Остановлен, все буферы сброшены", self.name)
    
    async def flush_now(self, table: Optional[str] = None) -> None:
        """
        Принудительный flush.
        
        Args:
            table: Если указано, сбрасывает только этот буфер. Иначе — все.
        """
        if table:
            await self._flush_buffer(table)
        else:
            await self._flush_all()
