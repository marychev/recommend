"""
Асинхронные тесты для Health Check endpoint

Переписано с TestClient на AsyncClient для:
- Правильного тестирования async endpoints
- Улучшения производительности
- Возможности параллельного тестирования
"""

import pytest
import asyncio
import time

from httpx import AsyncClient
from app.main import app


@pytest.fixture
async def async_client():
    """Асинхронный HTTP клиент для тестирования API"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


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

    async def test_health_check_response_time(self, async_client):
        """Тест времени ответа health check (должен быть быстрым)"""

        start = time.time()
        response = await async_client.get("/api/v1/health")
        duration = time.time() - start

        assert response.status_code == 200
        # Health check должен отвечать быстро (< 1 секунды)
        assert (
            duration < 1.0
        ), f"Health check слишком медленный: {duration:.2f}s"

    async def test_health_check_services_status(self, async_client):
        """Тест проверки статуса каждого сервиса"""
        response = await async_client.get("/api/v1/health")
        data = response.json()

        services = data["services"]

        # Проверяем, что у каждого сервиса есть статус
        for service_name in ["clickhouse", "redis", "kafka"]:
            assert service_name in services
            service = services[service_name]

            # Каждый сервис должен иметь статус
            assert (
                "status" in service or "connected" in service
            ), f"Service {service_name} должен иметь поле status или connected"


@pytest.mark.asyncio
class TestHealthCheckConcurrency:
    """Тесты параллельных health check запросов"""

    async def test_multiple_concurrent_health_checks(self, async_client):
        """
        Тест множественных параллельных health check запросов

        Проверяет, что health check может обрабатывать много
        одновременных запросов без проблем.
        """

        # 20 параллельных запросов
        tasks = [async_client.get("/api/v1/health") for _ in range(20)]

        responses = await asyncio.gather(*tasks)

        # Все должны успешно выполниться
        assert len(responses) == 20
        assert all(r.status_code == 200 for r in responses)

        # Все должны вернуть одинаковую структуру
        for response in responses:
            data = response.json()
            assert "status" in data
            assert "services" in data
