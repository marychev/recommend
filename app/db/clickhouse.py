import logging
from datetime import datetime
from typing import Optional, Any, List
from aiochclient import ChClient
from aiohttp import ClientSession, ClientTimeout
from fastapi import HTTPException, status
from app.config import settings
from app.models.schemas import UserTrackInteraction, Track, User
from app.kafka.constants import DATA_HANDLER_BATCH_SIZE, DATA_HANDLER_FLUSH_INTERVAL
from app.utils.id_generator import get_next_id
from app.utils.sql_sanitize import safe_identifier
from app.utils.batch_buffer import BatchBuffer

logger = logging.getLogger(__name__)


class ClickHouseClient:
    """Асинхронный клиент ClickHouse на базе aiochclient с батчингом"""

    # Разрешенные имена таблиц и полей (защита от SQL Injection)
    ALLOWED_TABLES = {'users', 'tracks', 'user_track_interactions', 'user_recommendations', 'user_track_matrix'}
    ALLOWED_FIELDS = {'user_id', 'track_id', 'username', 'email', 'title', 'artist', 'genre'}

    @staticmethod
    def _validate_identifier(value: str, allowed: set[str], name: str = "identifier") -> str:
        """Валидация SQL идентификатора (защита от SQL Injection).
        Использует whitelist + safe_identifier из sql_sanitize как fallback."""
        if value in allowed:
            return value
        return safe_identifier(value)

    # Маппинг таблиц на column_names для INSERT
    TABLE_TO_COLUMNS = {
        'users': User.column_names,
        'tracks': Track.column_names,
        'user_track_interactions': UserTrackInteraction.column_names,
    }

    def __init__(self):
        self.client: Optional[ChClient] = None
        self.session: Optional[ClientSession] = None
        self._id_initialized: set = set()  # Кэш: для каких table:field уже инициализирован Redis-счётчик

        # Используем переиспользуемый BatchBuffer для буферизации
        self._buffer = BatchBuffer(
            tables=['users', 'tracks', 'user_track_interactions'],
            batch_size=DATA_HANDLER_BATCH_SIZE,
            flush_interval=DATA_HANDLER_FLUSH_INTERVAL,
            flush_callback=self._flush_to_clickhouse,
            name="ClickHouseClient",
        )

    async def connect(self):
        """Подключение к ClickHouse"""
        try:
            # Создаем ClientSession с таймаутами для избежания зависаний
            timeout = ClientTimeout(total=60, connect=10)  # 60 сек общий, 10 сек на подключение
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

    async def _flush_to_clickhouse(self, table: str, records: List[List[Any]]) -> None:
        """Callback для записи данных в ClickHouse (используется BatchBuffer)."""
        # Получаем column_names
        column_getter = self.TABLE_TO_COLUMNS.get(table)
        column_names = column_getter() if column_getter else None
        
        # Выполняем батч INSERT
        await self.insert(table, records, column_names)
        
        logger.info(
            "Батч INSERT (fallback): table=%s, records=%s",
            table, len(records)
        )

    async def start_periodic_flush(self) -> None:
        """Запустить периодический flush буферов"""
        await self._buffer.start()

    async def stop_periodic_flush(self) -> None:
        """Остановить периодический flush и сбросить все буферы"""
        await self._buffer.stop()

    async def exists_in_table(self, table: str, field: str, value: Any) -> bool:
        """Проверка существования записи в таблице (защита от SQL Injection)"""
        # Валидация идентификаторов
        safe_table = self._validate_identifier(table, self.ALLOWED_TABLES, "table")
        safe_field = self._validate_identifier(field, self.ALLOWED_FIELDS, "field")
        
        # value должен быть числом для ID полей
        safe_value = int(value)
        
        # Используем SELECT 1 LIMIT 1 вместо count() - намного быстрее
        check = await self.execute_raw(
            f"SELECT 1 FROM {safe_table} WHERE {safe_field} = {safe_value} LIMIT 1"
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
        """Сохраняем событие в буфер для батчинга"""
        await self._buffer.add('user_track_interactions', [
            event.user_id,
            event.track_id,
            event.action_type.value,
            event.listen_duration_seconds,
            timestamp,
        ])

    async def next_id(self, table: str, field: str) -> int:
        """
        Генерация следующего уникального ID для таблицы.

        Использует атомарный Redis INCR для гарантии уникальности ID.
        ClickHouse запрашивается только при первом вызове для инициализации счётчика.
        """
        cache_key = f"{table}:{field}"

        # Fast path: счётчик уже инициализирован — только Redis INCR
        if cache_key in self._id_initialized:
            return await get_next_id(table, field, fallback_max_id=None)

        # Slow path (первый вызов): получаем max_id из БД для инициализации
        safe_table = self._validate_identifier(table, self.ALLOWED_TABLES, "table")
        safe_field = self._validate_identifier(field, self.ALLOWED_FIELDS, "field")

        fallback_max_id = None
        try:
            if self.client:
                result = await self.execute_raw(
                    f"SELECT {safe_field} FROM {safe_table} ORDER BY {safe_field} DESC LIMIT 1"
                )
                fallback_max_id = result[0][0] if result and result[0][0] else 0
        except Exception as e:
            logger.debug("Не удалось получить max_id из БД: %s", e)

        self._id_initialized.add(cache_key)
        return await get_next_id(table, field, fallback_max_id)
    
    async def save_track(self, track: Track, track_id: Optional[int] = None) -> int:
        """Сохраняем трек в буфер для батчинга, возвращаем ID сразу"""
        # Если ID уже передан (например, из create_track), используем его
        # Иначе генерируем новый ID
        if track_id is None:
            new_id = await self.next_id("tracks", "track_id")
        else:
            new_id = track_id
        
        # Используем created_at из объекта track, если он есть, иначе текущее время
        created_at = track.created_at if hasattr(track, 'created_at') and track.created_at else datetime.now()
        
        await self._buffer.add('tracks', [
            new_id,
            track.title,
            track.artist,
            track.album or "",
            track.genre or "",
            track.duration_seconds or 0,
            track.release_year or 0,
            created_at,
        ])
        
        return new_id

    async def save_user(self, user: User, user_id: Optional[int] = None) -> int:
        """Сохраняем пользователя в буфер для батчинга, возвращаем ID сразу"""
        # Если ID уже передан (например, из create_user), используем его
        # Иначе генерируем новый ID
        if user_id is None:
            new_id = await self.next_id("users", "user_id")
        else:
            new_id = user_id
        
        # Используем created_at из объекта user, если он есть, иначе текущее время
        created_at = user.created_at if hasattr(user, 'created_at') and user.created_at else datetime.now()
        
        await self._buffer.add('users', [
            new_id,
            user.username,
            user.email or "",
            user.age or 0,
            user.country or "",
            created_at,
        ])
        
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
