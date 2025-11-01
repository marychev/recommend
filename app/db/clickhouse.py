from typing import Optional, Any, List
from aiochclient import ChClient
from aiohttp import ClientSession

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
            url = f"http://{settings.clickhouse_host}:{settings.clickhouse_port}"
            
            self.client = ChClient(
                self.session,
                url=url,
                user=settings.clickhouse_user,
                password=settings.clickhouse_password,
                database=settings.clickhouse_database
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

    async def execute(self, query: str, parameters: Optional[dict] = None) -> List[dict]:
        """Выполнение запроса с возвратом результатов в виде словарей"""
        if not self.client:
            raise RuntimeError("ClickHouse client not connected")
        
        try:
            # aiochclient не поддерживает параметры напрямую, выполняем простой запрос
            result = await self.client.fetch(query)
            return result
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}")

    async def execute_raw(self, query: str, parameters: Optional[dict] = None) -> List[tuple]:
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
        column_names: Optional[List[str]] = None
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
