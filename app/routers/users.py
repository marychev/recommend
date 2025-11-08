from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Path, Query

from app.models.schemas import User, UserCreate, UserStatistics
from app.db.clickhouse import get_clickhouse_client

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Создать пользователя",
    description="Создает новый профиль пользователя в системе",
)
async def create_user(user: UserCreate):
    """
    Создание нового пользователя

    Пример запроса:
    ```json
    {
        "username": "john_doe",
        "email": "john@example.com",
        "age": 25,
        "country": "Russia"
    }
    ```
    """
    clickhouse = get_clickhouse_client()

    try:
        new_id = await clickhouse.save_user(user)
        return User(
            user_id=new_id,
            username=user.username,
            email=user.email or "",
            age=user.age or 0,
            country=user.country or "",
            created_at=datetime.now(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании пользователя: {str(e)}",
        )


@router.get(
    "/{user_id}",
    response_model=User,
    summary="Получить пользователя",
    description="Возвращает информацию о пользователе по его ID",
)
async def get_user(
    user_id: int = Path(..., description="ID пользователя", examples=[1001])
):
    clickhouse = get_clickhouse_client()

    try:
        result = await clickhouse.execute_raw(
            f"SELECT user_id, username, email, age, country, created_at FROM users WHERE user_id = {user_id}"
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользователь с ID {user_id} не найден",
            )

        row = result[0]
        return User(
            user_id=row[0],
            username=row[1],
            email=row[2],
            age=row[3],
            country=row[4],
            created_at=row[5],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении пользователя: {str(e)}",
        )


@router.get(
    "",
    response_model=List[User],
    summary="Список пользователей",
    description="Возвращает список всех пользователей с пагинацией",
)
async def list_users(
    limit: int = Query(100, description="Количество записей", ge=1, le=1000),
    offset: int = Query(0, description="Смещение", ge=0),
):
    """
    Получение списка пользователей с пагинацией
    """
    clickhouse = get_clickhouse_client()

    try:
        result = await clickhouse.execute_raw(
            f"""
            SELECT user_id, username, email, age, country, created_at 
            FROM users 
            ORDER BY user_id 
            LIMIT {limit} OFFSET {offset}
            """
        )

        users = [
            User(
                user_id=row[0],
                username=row[1],
                email=row[2],
                age=row[3],
                country=row[4],
                created_at=row[5],
            )
            for row in result
        ]

        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка пользователей: {str(e)}",
        )


@router.get(
    "/{user_id}/statistics",
    response_model=UserStatistics,
    summary="Статистика пользователя",
    description="Возвращает статистику активности пользователя",
)
async def get_user_statistics(
    user_id: int = Path(..., description="ID пользователя", examples=[1001])
):
    """
    Получение статистики пользователя:
    - Общее количество взаимодействий
    - Количество уникальных прослушанных треков
    - Любимый жанр
    - Общее время прослушивания
    """
    clickhouse = get_clickhouse_client()

    try:
        _ = await clickhouse.exists_user(user_id)

        # Получаем статистику
        stats_query = f"""
        SELECT 
            count() as total_interactions,
            uniq(track_id) as unique_tracks,
            sum(listen_duration_seconds) / 3600.0 as total_listen_hours
        FROM user_track_interactions
        WHERE user_id = {user_id}
        """

        stats_result = await clickhouse.execute_raw(stats_query)
        stats_row = stats_result[0] if stats_result else (0, 0, 0.0)

        # Получаем любимый жанр
        genre_query = f"""
        SELECT t.genre, count() as cnt
        FROM user_track_interactions i
        JOIN tracks t ON i.track_id = t.track_id
        WHERE i.user_id = {user_id} AND t.genre != ''
        GROUP BY t.genre
        ORDER BY cnt DESC
        LIMIT 1
        """

        genre_result = await clickhouse.execute_raw(genre_query)
        favorite_genre = genre_result[0][0] if genre_result else None

        return UserStatistics(
            user_id=user_id,
            total_interactions=stats_row[0],
            unique_tracks=stats_row[1],
            favorite_genre=favorite_genre,
            total_listen_time_hours=round(stats_row[2], 2),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении статистики: {str(e)}",
        )
