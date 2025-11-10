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
    include_performance_metrics: bool = Field(
        False, description="Включить детальные метрики производительности в ответ"
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


class PerformanceMetrics(BaseModel):
    """Детальные метрики производительности запроса"""

    total_time_ms: float = Field(
        ..., description="Общее время выполнения запроса (мс)", examples=[245.67]
    )
    redis_check_time_ms: Optional[float] = Field(
        None, description="Время проверки кэша Redis (мс)", examples=[2.34]
    )
    redis_save_time_ms: Optional[float] = Field(
        None, description="Время сохранения в Redis (мс)", examples=[3.12]
    )
    clickhouse_user_check_time_ms: Optional[float] = Field(
        None, description="Время проверки существования пользователя (мс)", examples=[15.23]
    )
    clickhouse_interactions_count_time_ms: Optional[float] = Field(
        None, description="Время подсчета взаимодействий пользователя (мс)", examples=[12.45]
    )
    clickhouse_similar_users_time_ms: Optional[float] = Field(
        None, description="Время поиска похожих пользователей (мс)", examples=[89.56]
    )
    clickhouse_recommendations_time_ms: Optional[float] = Field(
        None, description="Время получения рекомендаций (мс)", examples=[123.78]
    )
    algorithm_processing_time_ms: Optional[float] = Field(
        None, description="Время обработки результатов алгоритмом (мс)", examples=[4.21]
    )
    cache_hit: bool = Field(
        ..., description="Был ли использован кэш", examples=[False]
    )
    similar_users_count: Optional[int] = Field(
        None, description="Количество найденных похожих пользователей", examples=[50]
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
    performance_metrics: Optional[PerformanceMetrics] = Field(
        None,
        description="Детальные метрики производительности (включается опционально)"
    )
