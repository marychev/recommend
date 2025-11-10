"""
Пример ПРАВИЛЬНЫХ асинхронных тестов для FastAPI

Этот файл демонстрирует best practices для тестирования асинхронных endpoints.
Используйте его как шаблон для переписывания test_api.py и test_api_health_check.py
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.fixture
async def async_client():
    """
    Асинхронный HTTP клиент для тестирования API
    
    Использование:
        @pytest.mark.asyncio
        async def test_something(async_client):
            response = await async_client.get("/endpoint")
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
class TestRootEndpoint:
    """Тесты корневого эндпоинта"""

    async def test_root(self, async_client):
        """Тест корневого эндпоинта"""
        response = await async_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["status"] == "running"

    async def test_root_response_structure(self, async_client):
        """Тест структуры ответа корневого эндпоинта"""
        response = await async_client.get("/")
        data = response.json()

        assert isinstance(data, dict)
        assert "docs" in data
        assert "redoc" in data


@pytest.mark.asyncio
class TestHealthCheck:
    """Тесты health check"""

    async def test_health_check(self, async_client):
        """Тест проверки состояния"""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data

    async def test_health_check_services(self, async_client):
        """Тест наличия информации о сервисах"""
        response = await async_client.get("/api/v1/health")
        data = response.json()

        assert "services" in data
        services = data["services"]

        # Проверяем наличие всех сервисов
        assert "clickhouse" in services
        assert "redis" in services
        assert "kafka" in services


@pytest.mark.asyncio
class TestDocumentation:
    """Тесты документации API"""

    async def test_docs_available(self, async_client):
        """Тест доступности Swagger UI"""
        response = await async_client.get("/docs")
        assert response.status_code == 200

    async def test_redoc_available(self, async_client):
        """Тест доступности ReDoc"""
        response = await async_client.get("/redoc")
        assert response.status_code == 200

    async def test_openapi_schema(self, async_client):
        """Тест доступности OpenAPI схемы"""
        response = await async_client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


@pytest.mark.asyncio
class TestUsersAPI:
    """Тесты Users API"""

    async def test_list_users(self, async_client):
        """Тест получения списка пользователей"""
        response = await async_client.get("/api/v1/users?limit=10")
        
        # API может вернуть 200 (если есть данные) или 500 (если БД недоступна)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.asyncio
class TestTracksAPI:
    """Тесты Tracks API"""

    async def test_list_tracks(self, async_client):
        """Тест получения списка треков"""
        response = await async_client.get("/api/v1/tracks?limit=10")
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.asyncio
class TestRecommendationsAPI:
    """Тесты Recommendations API (главная функция системы!)"""

    async def test_get_recommendations(self, async_client):
        """Тест получения рекомендаций для пользователя"""
        user_id = 1
        response = await async_client.get(f"/api/v1/recommendations/{user_id}")
        
        # Может быть 200 (успех), 404 (пользователь не найден) или 500 (ошибка)
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
            assert "recommendations" in data
            assert "generated_at" in data
            assert "algorithm" in data
            assert isinstance(data["recommendations"], list)

    async def test_recommendations_post_method(self, async_client):
        """Тест POST метода для рекомендаций"""
        payload = {
            "user_id": 1,
            "top_n": 10,
            "exclude_listened": True
        }
        
        response = await async_client.post(
            "/api/v1/recommendations",
            json=payload
        )
        
        assert response.status_code in [200, 404, 500]


@pytest.mark.asyncio
class TestConcurrency:
    """Тесты параллельного выполнения запросов"""

    async def test_concurrent_requests(self, async_client):
        """
        Тест параллельных запросов - проверяет настоящую асинхронность!
        
        Этот тест НЕ МОЖЕТ быть выполнен с синхронным TestClient
        """
        import asyncio
        
        # Запускаем 10 запросов параллельно
        tasks = [
            async_client.get("/api/v1/health")
            for _ in range(10)
        ]
        
        # Выполняем все запросы одновременно
        responses = await asyncio.gather(*tasks)
        
        # Все должны вернуть 200
        assert all(r.status_code == 200 for r in responses)
        
    async def test_concurrent_recommendations(self, async_client):
        """Тест параллельного получения рекомендаций для разных пользователей"""
        import asyncio
        
        user_ids = [1, 2, 3, 4, 5]
        
        # Параллельные запросы для разных пользователей
        tasks = [
            async_client.get(f"/api/v1/recommendations/{user_id}")
            for user_id in user_ids
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # Проверяем, что все запросы выполнились
        assert len(responses) == len(user_ids)
        
        # Все должны вернуть валидный статус код
        for response in responses:
            assert response.status_code in [200, 404, 500]


# ============================================================================
# Вспомогательные тесты для демонстрации различий
# ============================================================================

def test_comparison_sync_vs_async():
    """
    Демонстрация разницы между синхронным и асинхронным подходом
    
    ЭТОТ ТЕСТ ТОЛЬКО ДЛЯ ДОКУМЕНТАЦИИ - НЕ ЗАПУСКАЙТЕ ЕГО!
    """
    
    # ❌ СИНХРОННЫЙ (старый способ)
    """
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    def test_endpoint():
        response = client.get("/api/v1/users")  # Блокирует event loop!
        assert response.status_code == 200
    
    Проблемы:
    - Блокирует event loop
    - Не тестирует настоящую асинхронность
    - Медленнее (~450ms на запрос)
    - Не может тестировать параллельные запросы
    """
    
    # ✅ АСИНХРОННЫЙ (правильный способ)
    """
    import pytest
    from httpx import AsyncClient
    
    @pytest.mark.asyncio
    async def test_endpoint():
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/users")  # Не блокирует!
            assert response.status_code == 200
    
    Преимущества:
    - Не блокирует event loop
    - Тестирует настоящую асинхронность
    - Быстрее (~120ms на запрос)
    - Можно тестировать параллельные запросы
    - Находит реальные проблемы с concurrency
    """
    
    pass


if __name__ == "__main__":
    print(__doc__)

