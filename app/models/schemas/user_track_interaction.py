from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.schemas import ActionType


class UserTrackInteractionBase(BaseModel):
    """Базовая модель взаимодействия пользователя с треком"""

    user_id: int = Field(..., description="ID пользователя", examples=[1001])
    track_id: int = Field(..., description="ID трека", examples=[12345])
    action_type: ActionType = Field(
        ..., description="Тип действия", examples=["play"]
    )
    listen_duration_seconds: Optional[int] = Field(
        None,
        description="Длительность прослушивания в секундах",
        examples=[180],
    )


class UserTrackInteractionCreate(UserTrackInteractionBase):
    """Модель для создания события взаимодействия"""

    timestamp: Optional[datetime] = Field(
        None,
        description=(
            "Время события (если не указано, используется текущее время)"
        ),
    )


class UserTrackInteraction(UserTrackInteractionBase):
    """Модель взаимодействия с timestamp"""

    timestamp: datetime = Field(..., description="Время события")

    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def column_names() -> list[str]:
        return [
            "user_id",
            "track_id",
            "action_type",
            "listen_duration_seconds",
            "timestamp",
            # "model_config"
        ]