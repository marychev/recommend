"""
Pydantic модели для API (схемы запросов и ответов)
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class ActionType(str, Enum):
    """Типы действий пользователя с треком"""
    PLAY = "play"
    LIKE = "like"
    DISLIKE = "dislike"
    SKIP = "skip"
    ADD_TO_PLAYLIST = "add_to_playlist"
    SHARE = "share"


# ==================== Track Models ====================

class TrackBase(BaseModel):
    """Базовая модель трека"""
    title: str = Field(
        ..., description="Название трека", examples=["Bohemian Rhapsody"]
    )
    artist: str = Field(..., description="Исполнитель", examples=["Queen"])
    album: Optional[str] = Field(
        None, description="Альбом", examples=["A Night at the Opera"]
    )
    genre: Optional[str] = Field(None, description="Жанр", examples=["Rock"])
    duration_seconds: Optional[int] = Field(
        None, description="Длительность в секундах", examples=[354]
    )
    release_year: Optional[int] = Field(
        None, description="Год выпуска", examples=[1975]
    )


class TrackCreate(TrackBase):
    """Модель для создания трека"""


class Track(TrackBase):
    """Модель трека с ID"""
    track_id: int = Field(
        ..., description="Уникальный идентификатор трека", examples=[12345]
    )
    created_at: datetime = Field(..., description="Дата создания записи")

    model_config = ConfigDict(from_attributes=True)


# ==================== User Models ====================

class UserBase(BaseModel):
    """Базовая модель пользователя"""
    username: str = Field(
        ..., description="Имя пользователя", examples=["john_doe"]
    )
    email: Optional[str] = Field(
        None, description="Email пользователя", examples=["john@example.com"]
    )
    age: Optional[int] = Field(
        None, description="Возраст", examples=[25], ge=1, le=120
    )
    country: Optional[str] = Field(
        None, description="Страна", examples=["Russia"]
    )


class UserCreate(UserBase):
    """Модель для создания пользователя"""


class User(UserBase):
    """Модель пользователя с ID"""
    user_id: int = Field(
        ...,
        description="Уникальный идентификатор пользователя",
        examples=[1001]
    )
    created_at: datetime = Field(..., description="Дата регистрации")

    model_config = ConfigDict(from_attributes=True)


# ==================== Interaction Models ====================

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
        examples=[180]
    )


class UserTrackInteractionCreate(UserTrackInteractionBase):
    """Модель для создания события взаимодействия"""
    timestamp: Optional[datetime] = Field(
        None,
        description=(
            "Время события (если не указано, используется текущее время)"
        )
    )


class UserTrackInteraction(UserTrackInteractionBase):
    """Модель взаимодействия с timestamp"""
    timestamp: datetime = Field(..., description="Время события")

    model_config = ConfigDict(from_attributes=True)


# ==================== Recommendation Models ====================

class RecommendationRequest(BaseModel):
    """Запрос на получение рекомендаций"""
    user_id: int = Field(..., description="ID пользователя", examples=[1001])
    top_n: Optional[int] = Field(
        10,
        description="Количество рекомендаций",
        examples=[10],
        ge=1,
        le=100
    )
    exclude_listened: bool = Field(
        True,
        description="Исключить уже прослушанные треки"
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
        examples=["Пользователи с похожими вкусами слушают этот трек"]
    )


class RecommendationResponse(BaseModel):
    """Ответ с рекомендациями"""
    user_id: int = Field(..., description="ID пользователя", examples=[1001])
    recommendations: List[RecommendedTrack] = Field(
        ...,
        description="Список рекомендованных треков"
    )
    generated_at: datetime = Field(
        ..., description="Время генерации рекомендаций"
    )
    algorithm: str = Field(
        ...,
        description="Используемый алгоритм",
        examples=["collaborative_filtering"]
    )


# ==================== Statistics Models ====================

class UserStatistics(BaseModel):
    """Статистика пользователя"""
    user_id: int = Field(..., description="ID пользователя", examples=[1001])
    total_interactions: int = Field(
        ..., description="Всего взаимодействий", examples=[450]
    )
    unique_tracks: int = Field(
        ..., description="Уникальных треков", examples=[320]
    )
    favorite_genre: Optional[str] = Field(
        None, description="Любимый жанр", examples=["Rock"]
    )
    total_listen_time_hours: float = Field(
        ...,
        description="Общее время прослушивания (часы)",
        examples=[125.5]
    )


class TrackStatistics(BaseModel):
    """Статистика трека"""
    track_id: int = Field(..., description="ID трека", examples=[12345])
    total_plays: int = Field(
        ..., description="Всего прослушиваний", examples=[15420]
    )
    unique_listeners: int = Field(
        ..., description="Уникальных слушателей", examples=[8934]
    )
    total_likes: int = Field(..., description="Всего лайков", examples=[5432])
    average_listen_percentage: float = Field(
        ...,
        description="Средний процент прослушивания",
        examples=[78.5]
    )


# ==================== Health Check ====================

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
