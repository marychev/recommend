import time
from datetime import datetime
from typing import Any, List
from app.models.schemas import User


NOW = datetime.now()


class TestPerformance:
    """Тесты производительности"""

    def generate_row(self, i: int, age: int = 25, country: str = "Russia") -> List[Any]:
        return [i, f"user{i}", f"user{i}@test.com", age, country, NOW]

    async def test_bulk_insert_performance(
        self, clickhouse_client, create_test_schema, clean_tables
    ):
        """Тест производительности массовой вставки"""

        # Генерируем большое количество данных
        data = [self.generate_row(i) for i in range(1000)]
        await clickhouse_client.insert(
            "users", data, column_names=User.column_names()
        )
        start_time = time.time()
        end_time = time.time()
        elapsed = end_time - start_time
        assert elapsed < 2.0

    async def test_query_performance(
        self, clickhouse_client, create_test_schema, clean_tables
    ):
        """Тест производительности запросов"""

        # Вставляем данные
        data = [self.generate_row(i) for i in range(1000)]
        await clickhouse_client.insert(
            "users", data, column_names=User.column_names()
        )

        # Тестируем скорость запроса
        start_time = time.time()
        result = await clickhouse_client.execute_raw(
            "SELECT count() FROM users WHERE age >= 25"
        )
        end_time = time.time()

        elapsed = end_time - start_time

        # Запрос должен выполниться быстро (< 0.5 секунд)
        assert elapsed < 0.5
        assert result[0][0] == 1000
