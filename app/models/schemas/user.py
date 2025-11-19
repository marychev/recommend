from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


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
        examples=[1001],
    )
    created_at: datetime = Field(..., description="Дата регистрации")

    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def column_names() -> list[str]:
        return [
            "user_id",
            "username",
            "email",
            "age",
            "country",
            "created_at",
            # "model_config"
    ]
