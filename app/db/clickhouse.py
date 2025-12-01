import time
import random
import logging
from datetime import datetime
from typing import Optional, Any, List
from aiochclient import ChClient
from aiohttp import ClientSession
from fastapi import HTTPException, status
from app.config import settings
from app.models.schemas import UserTrackInteraction, Track, User


logger = logging.getLogger(__name__)


class ClickHouseClient:
    """Асинхронный клиент ClickHouse на базе aiochclient"""

    def __init__(self):
        self.client: Optional[ChClient] = None
        self.session: Optional[ClientSession] = None

    async def connect(self):
        """Подключение к ClickHouse"""
        try:
            self.session = ClientSession()

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
        """Вставка данных в таблицу"""
        # await self._ensure_connected()

        if not data:
            return

        try:
            # Формируем запрос INSERT
            columns = f"({', '.join(column_names)})" if column_names else ""
            query = f"INSERT INTO {table} {columns} VALUES"

            # aiochclient поддерживает прямую вставку данных
            await self.client.execute(query, *data)
        except Exception as e:
            raise RuntimeError(f"Insert failed: {e}")

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
        """Сохраняем событие в ClickHouse"""
        await self.insert(
            "user_track_interactions",
            [
                [
                    event.user_id,
                    event.track_id,
                    event.action_type.value,
                    event.listen_duration_seconds,
                    timestamp,
                ]
            ],
            column_names=UserTrackInteraction.column_names(),
        )

    async def next_id(self, table: str, field: str) -> int:
        # Оптимизированная генерация ID: используем ORDER BY DESC LIMIT 1 вместо max()
        # Это быстрее и использует меньше памяти на больших таблицах
        try:
            result = await self.execute_raw(
                f"SELECT {field} FROM {table} ORDER BY {field} DESC LIMIT 1"
            )
            max_id = result[0][0] if result and result[0][0] else 0
        except Exception:
            # Если ошибка (например, таблица пуста или проблема с памятью), начинаем с 1
            max_id = 0
        
        return (max_id or 0) + 1
    
    async def save_track(self, track: Track) -> int:
        new_id = await self.next_id("tracks", "track_id")
        await self.insert(
            "tracks",
            [
                [
                    new_id,
                    track.title,
                    track.artist,
                    track.album or "",
                    track.genre or "",
                    track.duration_seconds or 0,
                    track.release_year or 0,
                    datetime.now(),
                ]
            ],
            column_names=Track.column_names(),
        )
        return new_id

    async def save_user(self, user: User) -> int:
        """Сохраняем пользователя"""
        new_id = await self.next_id("users", "user_id")
        await self.insert(
            "users",
            [
                [
                    new_id,
                    user.username,
                    user.email or "",
                    user.age or 0,
                    user.country or "",
                    datetime.now(),
                ]
            ],
            column_names=User.column_names(),
        )
        return new_id

        # Fallback: используем запрос к БД
        try:
            result = await self.execute_raw(
                "SELECT user_id FROM users ORDER BY user_id DESC LIMIT 1"
            )
            max_id = result[0][0] if result and result[0][0] else 0
            new_id = (max_id or 0) + 1
            await self.insert(
                "users",
                [
                    [
                        new_id,
                        user.username,
                        user.email or "",
                        user.age or 0,
                        user.country or "",
                        datetime.now(),
                    ]
                ],
                column_names=User.column_names(),
            )
            return new_id
        except Exception as e:
            raise RuntimeError(
                f"Failed to save user after {max_retries} attempts: {e}"
            )


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
