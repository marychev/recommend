"""
Подключение к ClickHouse
"""
from typing import Optional
import clickhouse_connect
from clickhouse_connect.driver.client import Client

from app.config import settings


class ClickHouseClient:
    """Клиент для работы с ClickHouse"""

    def __init__(self):
        self.client: Optional[Client] = None

    def connect(self):
        """Подключение к ClickHouse"""
        try:
            self.client = clickhouse_connect.get_client(
                host=settings.clickhouse_host,
                port=settings.clickhouse_port,
                username=settings.clickhouse_user,
                password=settings.clickhouse_password,
                database=settings.clickhouse_database
            )
            print(
                f"✓ Подключение к ClickHouse установлено: "
                f"{settings.clickhouse_host}:{settings.clickhouse_port}"
            )
        except Exception as e:
            print(f"✗ Ошибка подключения к ClickHouse: {e}")
            raise

    def disconnect(self):
        """Отключение от ClickHouse"""
        if self.client:
            self.client.close()
            self.client = None
            print("✓ Подключение к ClickHouse закрыто")

    def is_connected(self) -> bool:
        """Проверка подключения"""
        try:
            if self.client:
                self.client.command("SELECT 1")
                return True
        except Exception:
            return False
        return False

    def execute(self, query: str, parameters=None):
        """Выполнение запроса"""
        if not self.client:
            raise RuntimeError("ClickHouse client not connected")
        return self.client.query(query, parameters=parameters)

    def insert(
        self,
        table: str,
        data: list,
        column_names: Optional[list] = None
    ):
        """Вставка данных"""
        if not self.client:
            raise RuntimeError("ClickHouse client not connected")
        return self.client.insert(table, data, column_names=column_names)


# Глобальный экземпляр клиента
clickhouse_client = ClickHouseClient()


def get_clickhouse_client() -> ClickHouseClient:
    """Получение клиента ClickHouse"""
    return clickhouse_client
