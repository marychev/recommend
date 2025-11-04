from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRootEndpoint:
    """Тесты корневого эндпоинта"""

    def test_root(self):
        """Тест корневого эндпоинта"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["status"] == "running"

    def test_root_response_structure(self):
        """Тест структуры ответа корневого эндпоинта"""
        response = client.get("/")
        data = response.json()

        assert isinstance(data, dict)
        assert "docs" in data
        assert "redoc" in data


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


class TestDocumentation:
    """Тесты документации API"""

    def test_docs_available(self):
        """Тест доступности Swagger UI"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_available(self):
        """Тест доступности ReDoc"""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema(self):
        """Тест доступности OpenAPI схемы"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


# TODO: Добавить интеграционные тесты для каждого эндпоинта
# Эти тесты требуют запущенного ClickHouse
# Смотрите tests/clickhouse/ для тестов БД

# TODO List:
# - test_create_user
# - test_get_user
# - test_list_users
# - test_user_statistics
# - test_create_track
# - test_get_track
# - test_list_tracks
# - test_track_statistics
# - test_create_event
# - test_get_user_events
# - test_get_track_events
# - test_get_recommendations
# - test_popular_tracks
