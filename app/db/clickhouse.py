import logging
import asyncio
from datetime import datetime
from typing import Optional, Any, List, Dict
from collections import deque
from aiochclient import ChClient
from aiohttp import ClientSession, ClientTimeout
from fastapi import HTTPException, status
from app.config import settings
from app.models.schemas import UserTrackInteraction, Track, User
from app.kafka.constants import DATA_HANDLER_BATCH_SIZE, DATA_HANDLER_FLUSH_INTERVAL 

logger = logging.getLogger(__name__)


class ClickHouseClient:
    """Асинхронный клиент ClickHouse на базе aiochclient с батчингом"""

    def __init__(self):
        self.client: Optional[ChClient] = None
        self.session: Optional[ClientSession] = None
        
        # Буферы для батчинга INSERT запросов
        self._insert_buffer: Dict[str, deque] = {
            'users': deque(),
            'tracks': deque(),
            'user_track_interactions': deque(),
        }
        self._buffer_size = DATA_HANDLER_BATCH_SIZE  # Размер батча (увеличен для лучшей производительности)
        self._flush_interval = DATA_HANDLER_FLUSH_INTERVAL  # Интервал автоматического flush в секундах (уменьшен для более быстрой обработки)
        self._flush_task: Optional[asyncio.Task] = None
        self._flush_lock = asyncio.Lock()
        self._running = False

    async def connect(self):
        """Подключение к ClickHouse"""
        try:
            # Создаем ClientSession с таймаутами для избежания зависаний
            timeout = ClientTimeout(total=30, connect=10)  # 30 сек общий, 10 сек на подключение
            self.session = ClientSession(timeout=timeout)

            # Формируем URL подключения
            url = (
                f"http://{settings.clickhouse_host}:{settings.clickhouse_port}"
            )

            self.client = ChClient(
                self.session,
                url=url,
                user=settings.clickhouse_user,
                password=settings.clickhouse_password,
                database=settings.clickhouse_database,
            )

            # await self.client.execute("SELECT 1")  # Проверяем подключение - Optimized

            logger.info(
                "Подключение к ClickHouse установлено: %s:%s",
                settings.clickhouse_host,
                settings.clickhouse_port,
            )
        except Exception as e:
            if self.session:
                await self.session.close()
                self.session = None
            self.client = None
            logger.error("Ошибка подключения к ClickHouse: %s", e)
            raise

    async def disconnect(self):
        """Отключение от ClickHouse"""
        if self.session:
            try:
                await self.session.close()
            except Exception:
                pass  # Игнорируем ошибки при закрытии
            finally:
                self.session = None
                self.client = None
                logger.info("Подключение к ClickHouse закрыто")

    async def is_connected(self) -> bool:
        """Проверка подключения"""
        try:
            if self.client:
                await self.client.execute("SELECT 1")
                return True
        except Exception:
            return False
        return False

    async def _ensure_connected(self) -> None:
        """Проверяет подключение и пытается переподключиться, если нужно"""
        if not self.client:
            try:
                await self.connect()
            except Exception as e:
                raise RuntimeError(f"ClickHouse client not connected: {e}")
        else:
            # Проверяем, что подключение действительно работает
            try:
                await self.client.execute("SELECT 1")
            except Exception:
                # Подключение потеряно, переподключаемся
                try:
                    if self.session:
                        await self.session.close()
                    self.session = None
                    self.client = None
                    await self.connect()
                except Exception as e:
                    raise RuntimeError(f"ClickHouse client not connected: {e}")

    async def execute(
        self, query: str, parameters: Optional[dict] = None
    ) -> List[dict]:
        """Выполнение запроса с возвратом результатов в виде словарей"""
        # await self._ensure_connected() - Optimized
        try:
            # aiochclient не поддерживает параметры напрямую, выполняем простой запрос
            return await self.client.fetch(query)
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}")

    async def execute_raw(
        self, query: str, parameters: Optional[dict] = None
    ) -> List[tuple]:
        """Выполнение запроса с возвратом сырых результатов (список кортежей)"""
        # await self._ensure_connected()
        try:
            # Получаем данные и преобразуем в список кортежей
            result = await self.client.fetch(query)
            # aiochclient возвращает строки, конвертируем в кортежи
            return [tuple(row.values()) for row in result]
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}")

    async def insert(
        self,
        table: str,
        data: List[List[Any]],
        column_names: Optional[List[str]] = None,
    ):
        """Вставка данных в таблицу (поддерживает батчи)"""
        # await self._ensure_connected()

        if not data:
            return

        try:
            # Формируем запрос INSERT
            columns = f"({', '.join(column_names)})" if column_names else ""
            query = f"INSERT INTO {table} {columns} VALUES"

            # aiochclient.execute принимает данные как позиционные аргументы после query
            # Распаковываем список списков для передачи каждой строки как отдельного аргумента
            await self.client.execute(query, *data)
        except Exception as e:
            raise RuntimeError(f"Insert failed: {e}")

    async def _flush_buffer(self, table: str) -> None:
        """Сбросить буфер в ClickHouse для указанной таблицы"""
        async with self._flush_lock:
            buffer = self._insert_buffer[table]
            if not buffer:
                return
            
            # Берем все записи из буфера
            records = list(buffer)
            buffer.clear()
        
        if not records:
            return
        
        try:
            # Определяем column_names в зависимости от таблицы
            if table == 'users':
                column_names = User.column_names()
            elif table == 'tracks':
                column_names = Track.column_names()
            elif table == 'user_track_interactions':
                column_names = UserTrackInteraction.column_names()
            else:
                column_names = None
            
            # Выполняем батч INSERT
            await self.insert(table, records, column_names)
            
            logger.info(
                "Батч INSERT выполнен: table=%s, records=%s",
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
                self._insert_buffer[table].extendleft(reversed(records))

    async def _flush_all_buffers(self) -> None:
        """Сбросить все буферы в ClickHouse"""
        for table in self._insert_buffer.keys():
            await self._flush_buffer(table)

    async def start_periodic_flush(self) -> None:
        """Запустить периодический flush буферов"""
        if self._running:
            return
        
        self._running = True
        
        async def flush_loop():
            while self._running:
                try:
                    await asyncio.sleep(self._flush_interval)
                    await self._flush_all_buffers()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("Ошибка в цикле flush: %s", e)
        
        self._flush_task = asyncio.create_task(flush_loop())
        logger.info(
            "Запущен периодический flush буферов: interval=%.1fs, buffer_size=%s",
            self._flush_interval,
            self._buffer_size,
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
        logger.info("Периодический flush остановлен, все буферы сброшены")

    async def exists_in_table(self, table: str, field: str, value: Any) -> bool:
        # Используем SELECT 1 LIMIT 1 вместо count() - намного быстрее
        check = await self.execute_raw(
            f"SELECT 1 FROM {table} WHERE {field} = {value} LIMIT 1"
        )
        if not check or len(check) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{table.title} с ID {value} не найден",
            )
        return True
    
    async def exists_user(self, user_id: int) -> bool:
        return await self.exists_in_table("users", "user_id", user_id)

    async def exists_track(self, track_id: int) -> bool:
        return await self.exists_in_table("tracks", "track_id", track_id)

    async def save_event(
        self, event: UserTrackInteraction, timestamp: datetime
    ) -> None:
        """Сохраняем событие в ClickHouse (с батчингом)"""
        await self.save_event_buffered(event, timestamp)

    async def save_event_buffered(
        self, event: UserTrackInteraction, timestamp: datetime
    ) -> None:
        """Сохраняем событие в буфер для батчинга"""
        async with self._flush_lock:
            self._insert_buffer['user_track_interactions'].append([
                event.user_id,
                event.track_id,
                event.action_type.value,
                event.listen_duration_seconds,
                timestamp,
            ])
            
            # Если буфер заполнен, запускаем flush
            if len(self._insert_buffer['user_track_interactions']) >= self._buffer_size:
                asyncio.create_task(self._flush_buffer('user_track_interactions'))

    async def next_id(self, table: str, field: str) -> int:
        # Оптимизированная генерация ID: используем ORDER BY DESC LIMIT 1 вместо max()
        # Это быстрее и использует меньше памяти на больших таблицах
        try:
            # Проверяем подключение перед запросом
            if not self.client:
                try:
                    await self._ensure_connected()
                except Exception as conn_error:
                    # Если не можем подключиться, используем временный ID на основе timestamp
                    logger.warning("Не удалось подключиться к ClickHouse для генерации ID: %s. Используем временный ID", conn_error)
                    import time
                    return int(time.time() * 1000) % 1000000  # Временный ID на основе timestamp
            
            result = await self.execute_raw(
                f"SELECT {field} FROM {table} ORDER BY {field} DESC LIMIT 1"
            )
            max_id = result[0][0] if result and result[0][0] else 0
        except Exception as e:
            # Если ошибка (например, таблица пуста, нет подключения или проблема с памятью), используем временный ID
            logger.warning("Ошибка при генерации ID для %s.%s: %s. Используем временный ID", table, field, e)
            import time
            return int(time.time() * 1000) % 1000000  # Временный ID на основе timestamp
        
        return (max_id or 0) + 1
    
    async def save_track(self, track: Track) -> int:
        """Сохраняем трек в ClickHouse (с батчингом)"""
        return await self.save_track_buffered(track)

    async def save_track_buffered(self, track: Track, track_id: Optional[int] = None) -> int:
        """Сохраняем трек в буфер для батчинга, возвращаем ID сразу"""
        # Если ID уже передан (например, из create_track), используем его
        # Иначе генерируем новый ID
        if track_id is None:
            new_id = await self.next_id("tracks", "track_id")
        else:
            new_id = track_id
        
        # Используем created_at из объекта track, если он есть, иначе текущее время
        created_at = track.created_at if hasattr(track, 'created_at') and track.created_at else datetime.now()
        
        async with self._flush_lock:
            self._insert_buffer['tracks'].append([
                new_id,
                track.title,
                track.artist,
                track.album or "",
                track.genre or "",
                track.duration_seconds or 0,
                track.release_year or 0,
                created_at,
            ])
            
            # Если буфер заполнен, запускаем flush
            if len(self._insert_buffer['tracks']) >= self._buffer_size:
                asyncio.create_task(self._flush_buffer('tracks'))
        
        return new_id

    async def save_user(self, user: User) -> int:
        """Сохраняем пользователя в ClickHouse (с батчингом)"""
        return await self.save_user_buffered(user)

    async def save_user_buffered(self, user: User, user_id: Optional[int] = None) -> int:
        """Сохраняем пользователя в буфер для батчинга, возвращаем ID сразу"""
        # Если ID уже передан (например, из create_user), используем его
        # Иначе генерируем новый ID
        if user_id is None:
            new_id = await self.next_id("users", "user_id")
        else:
            new_id = user_id
        
        # Используем created_at из объекта user, если он есть, иначе текущее время
        created_at = user.created_at if hasattr(user, 'created_at') and user.created_at else datetime.now()
        
        async with self._flush_lock:
            self._insert_buffer['users'].append([
                new_id,
                user.username,
                user.email or "",
                user.age or 0,
                user.country or "",
                created_at,
            ])
            
            # Если буфер заполнен, запускаем flush
            if len(self._insert_buffer['users']) >= self._buffer_size:
                asyncio.create_task(self._flush_buffer('users'))
        
        return new_id


clickhouse_client = ClickHouseClient()


def get_clickhouse_client() -> ClickHouseClient:
    return clickhouse_client


async def connect_clickhouse() -> bool:
    """Подключение к ClickHouse"""
    clickhouse_connected = False
    try:
        logger.info(
            "\nПодключение к ClickHouse (%s:%s)...",
            settings.clickhouse_host,
            settings.clickhouse_port,
        )
        clickhouse = get_clickhouse_client()
        await clickhouse.connect()
        clickhouse_connected = True
        logger.info("ClickHouse подключен успешно!")
    except Exception as exc:
        logger.error("ОШИБКА: Не удалось подключиться к ClickHouse!")
        logger.error("Детали: %s", exc)
        logger.info("Решение: docker-compose up -d clickhouse или bash scripts/docker-reset-clickhouse.sh")

    return clickhouse_connected


async def shutdown_clickhouse() -> None:
    """Отключение от ClickHouse"""
    try:
        clickhouse = get_clickhouse_client()
        if await clickhouse.is_connected():
            await clickhouse.disconnect()
    except Exception as exc:
        logger.error("Ошибка при отключении от ClickHouse: %s", exc)
