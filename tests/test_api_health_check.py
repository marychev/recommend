from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthCheck:
    """Тесты health check"""

    def test_health_check(self):
        """Тест проверки состояния"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data

    def test_health_check_services(self):
        """Тест наличия информации о сервисах"""
        response = client.get("/api/v1/health")
        data = response.json()

        assert "services" in data
        services = data["services"]

        # Проверяем наличие всех сервисов
        assert "clickhouse" in services
        assert "redis" in services
        assert "kafka" in services
