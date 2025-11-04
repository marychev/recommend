from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


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
