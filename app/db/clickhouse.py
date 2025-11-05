from re import T
from typing import Optional, Any, List
from aiochclient import ChClient
from aiohttp import ClientSession
from fastapi import HTTPException, status
from app.models.schemas import UserTrackInteraction, Track, User
from datetime import datetime

from app.config import settings


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

            # Проверяем подключение
            await self.client.execute("SELECT 1")

            print(
                f"✓ Подключение к ClickHouse установлено: "
                f"{settings.clickhouse_host}:{settings.clickhouse_port}"
            )
        except Exception as e:
            if self.session:
                await self.session.close()
                self.session = None
            self.client = None
            print(f"✗ Ошибка подключения к ClickHouse: {e}")
            raise

    async def disconnect(self):
        """Отключение от ClickHouse"""
        if self.session:
            await self.session.close()
            self.session = None
            self.client = None
            print("✓ Подключение к ClickHouse закрыто")

    async def is_connected(self) -> bool:
        """Проверка подключения"""
        try:
            if self.client:
                await self.client.execute("SELECT 1")
                return True
        except Exception:
            return False
        return False

    async def execute(
        self, query: str, parameters: Optional[dict] = None
    ) -> List[dict]:
        """Выполнение запроса с возвратом результатов в виде словарей"""
        if not self.client:
            raise RuntimeError("ClickHouse client not connected")

        try:
            # aiochclient не поддерживает параметры напрямую, выполняем простой запрос
            result = await self.client.fetch(query)
            return result
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}")

    async def execute_raw(
        self, query: str, parameters: Optional[dict] = None
    ) -> List[tuple]:
        """Выполнение запроса с возвратом сырых результатов (список кортежей)"""
        if not self.client:
            raise RuntimeError("ClickHouse client not connected")

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
        if not self.client:
            raise RuntimeError("ClickHouse client not connected")

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

    async def exists_user(self, user_id: int) -> List[tuple]:
        """Проверяем существование пользователя"""
        user_check = await self.execute_raw(
            f"SELECT count() FROM users WHERE user_id = {user_id}"
        )
        if user_check[0][0] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользователь с ID {user_id} не найден",
            )

        return user_check

    async def exists_track(self, track_id: int) -> List[tuple]:
        """Проверяем существование трека"""
        track_check = await self.execute_raw(
            f"SELECT count() FROM tracks WHERE track_id = {track_id}"
        )
        if track_check[0][0] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Трек с ID {track_id} не найден",
            )
        return track_check

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
            column_names=[
                "user_id",
                "track_id",
                "action_type",
                "listen_duration_seconds",
                "timestamp",
            ],
        )

    async def save_track(self, track: Track) -> int:
        """Сохраняем трек"""
        # Генерируем ID
        result = await self.execute_raw(
            "SELECT max(track_id) as max_id FROM tracks"
        )
        max_id = result[0][0] if result and result[0][0] else 0
        new_id = (max_id or 0) + 1

        # Вставляем трек
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
            column_names=[
                "track_id",
                "title",
                "artist",
                "album",
                "genre",
                "duration_seconds",
                "release_year",
                "created_at",
            ],
        )
        return new_id

    async def save_user(self, user: User) -> int:
        """Сохраняем пользователя"""
        # Генерируем ID (в реальности нужно использовать автоинкремент или UUID)
        result = await self.execute_raw(
            "SELECT max(user_id) as max_id FROM users"
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
            column_names=[
                "user_id",
                "username",
                "email",
                "age",
                "country",
                "created_at",
            ],
        )

        return new_id


clickhouse_client = ClickHouseClient()


def get_clickhouse_client() -> ClickHouseClient:
    return clickhouse_client


async def connect_clickhouse() -> bool:
    """Подключение к ClickHouse"""
    clickhouse_connected = False
    try:
        print(
            f"\n📊 Подключение к ClickHouse "
            f"({settings.clickhouse_host}:{settings.clickhouse_port})..."
        )
        clickhouse = get_clickhouse_client()
        await clickhouse.connect()
        clickhouse_connected = True
        print("   ✅ ClickHouse подключен успешно!")
    except Exception as exc:
        print("   ❌ ОШИБКА: Не удалось подключиться к ClickHouse!")
        print(f"   Детали: {exc}")
        print("\n   💡 Решение:")
        print("      docker-compose up -d clickhouse")
        print("      или")
        print("      bash scripts/docker-reset-clickhouse.sh")

    return clickhouse_connected


async def shutdown_clickhouse() -> None:
    """Отключение от ClickHouse"""
    try:
        clickhouse = get_clickhouse_client()
        if await clickhouse.is_connected():
            await clickhouse.disconnect()
    except Exception as exc:
        print(f"⚠️ Ошибка при отключении от ClickHouse: {exc}")
