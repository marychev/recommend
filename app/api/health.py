"""
API эндпоинт для проверки состояния сервиса
"""

from datetime import datetime
from fastapi import APIRouter, status

from app.models.schemas import HealthCheckResponse
from app.db.clickhouse import get_clickhouse_client
from app.db.redis_client import get_redis_client
from app.kafka.client import check_kafka_health

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Проверка состояния сервиса",
    description=(
        "Проверяет доступность API и подключенных сервисов "
        "(ClickHouse, Kafka, Redis)"
    ),
)
async def health_check():
    """
    Проверка состояния сервиса и всех подключений

    Возвращает:
    - Общий статус сервиса
    - Время проверки
    - Статус каждого подключенного сервиса
    """
    clickhouse = get_clickhouse_client()
    redis = get_redis_client()

    # Проверяем ClickHouse (с попыткой переподключения)
    clickhouse_status = "disconnected"
    if await clickhouse.is_connected():
        clickhouse_status = "connected"
    else:
        # Попытка переподключения
        try:
            print("⚠️  ClickHouse disconnected, попытка переподключения...")
            await clickhouse.connect()
            if await clickhouse.is_connected():
                clickhouse_status = "connected"
                print("   ✅ ClickHouse переподключен!")
        except Exception as exc:
            print(f"   ❌ Не удалось переподключиться: {exc}")

    # Проверяем Kafka
    kafka_health = await check_kafka_health()
    kafka_status = (
        "connected"
        if kafka_health.get("status") == "healthy"
        else "disconnected"
    )

    services = {
        "clickhouse": clickhouse_status,
        "redis": (
            "connected" if await redis.is_connected() else "disconnected"
        ),
        "kafka": kafka_status,
    }

    # Определяем общий статус
    # Kafka не критична, поэтому degraded только если CH или Redis недоступны
    overall_status = (
        "healthy"
        if (
            clickhouse_status == "connected"
            and services["redis"] == "connected"
        )
        else "degraded"
    )

    return HealthCheckResponse(
        status=overall_status, timestamp=datetime.now(), services=services
    )
