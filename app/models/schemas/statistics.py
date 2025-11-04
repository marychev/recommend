from typing import Optional
from pydantic import BaseModel, Field


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
        ..., description="Общее время прослушивания (часы)", examples=[125.5]
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
        ..., description="Средний процент прослушивания", examples=[78.5]
    )
