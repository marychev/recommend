from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.schemas import Track


class RecommendationRequest(BaseModel):
    """Запрос на получение рекомендаций"""

    user_id: int = Field(..., description="ID пользователя", examples=[1001])
    top_n: Optional[int] = Field(
        10, description="Количество рекомендаций", examples=[10], ge=1, le=100
    )
    exclude_listened: bool = Field(
        True, description="Исключить уже прослушанные треки"
    )


class RecommendedTrack(BaseModel):
    """Рекомендованный трек с оценкой"""

    track: Track = Field(..., description="Информация о треке")
    score: float = Field(
        ..., description="Оценка релевантности", examples=[0.85]
    )
    reason: Optional[str] = Field(
        None,
        description="Причина рекомендации",
        examples=["Пользователи с похожими вкусами слушают этот трек"],
    )


class RecommendationResponse(BaseModel):
    """Ответ с рекомендациями"""

    user_id: int = Field(..., description="ID пользователя", examples=[1001])
    recommendations: List[RecommendedTrack] = Field(
        ..., description="Список рекомендованных треков"
    )
    generated_at: datetime = Field(
        ..., description="Время генерации рекомендаций"
    )
    algorithm: str = Field(
        ...,
        description="Используемый алгоритм",
        examples=["collaborative_filtering"],
    )
