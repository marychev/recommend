from datetime import datetime
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Ответ на запрос состояния сервиса"""
    status: str = Field(
        ..., description="Статус сервиса", examples=["healthy"]
    )
    timestamp: datetime = Field(..., description="Время проверки")
    services: dict = Field(
        ...,
        description="Статус подключенных сервисов",
        examples=[{
            "clickhouse": "connected",
            "kafka": "connected",
            "redis": "connected"
        }]
    )
