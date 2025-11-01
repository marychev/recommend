"""
API эндпоинты для работы с пользователями
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Path, Query

from app.models.schemas import User, UserCreate, UserStatistics
from app.db.clickhouse import get_clickhouse_client

router = APIRouter()


@router.post(
    "/users",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Создать пользователя",
    description="Создает новый профиль пользователя в системе"
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
        # Генерируем ID (в реальности нужно использовать автоинкремент или UUID)
        result = await clickhouse.execute_raw("SELECT max(user_id) as max_id FROM users")
        max_id = result[0][0] if result and result[0][0] else 0
        new_id = (max_id or 0) + 1
        
        # Вставляем пользователя
        await clickhouse.insert(
            "users",
            [[
                new_id,
                user.username,
                user.email or "",
                user.age or 0,
                user.country or "",
                datetime.now()
            ]],
            column_names=["user_id", "username", "email", "age", "country", "created_at"]
        )
        
        return User(
            user_id=new_id,
            username=user.username,
            email=user.email,
            age=user.age,
            country=user.country,
            created_at=datetime.now()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании пользователя: {str(e)}"
        )


@router.get(
    "/users/{user_id}",
    response_model=User,
    summary="Получить пользователя",
    description="Возвращает информацию о пользователе по его ID"
)
async def get_user(
    user_id: int = Path(..., description="ID пользователя", examples=[1001])
):
    clickhouse = get_clickhouse_client()
    
    try:
        result = await clickhouse.execute_raw(
            "SELECT user_id, username, email, age, country, created_at FROM users WHERE user_id = {user_id:UInt32}",
            parameters={"user_id": user_id}
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользователь с ID {user_id} не найден"
            )
        
        row = result[0]
        return User(
            user_id=row[0],
            username=row[1],
            email=row[2],
            age=row[3],
            country=row[4],
            created_at=row[5]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении пользователя: {str(e)}"
        )


@router.get(
    "/users",
    response_model=List[User],
    summary="Список пользователей",
    description="Возвращает список всех пользователей с пагинацией"
)
async def list_users(
    limit: int = Query(100, description="Количество записей", ge=1, le=1000),
    offset: int = Query(0, description="Смещение", ge=0)
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
        
        users = []
        for row in result:
            users.append(User(
                user_id=row[0],
                username=row[1],
                email=row[2],
                age=row[3],
                country=row[4],
                created_at=row[5]
            ))
        
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка пользователей: {str(e)}"
        )


@router.get(
    "/users/{user_id}/statistics",
    response_model=UserStatistics,
    summary="Статистика пользователя",
    description="Возвращает статистику активности пользователя"
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
        # Проверяем существование пользователя
        user_check = await clickhouse.execute_raw(
            "SELECT count() FROM users WHERE user_id = {user_id:UInt32}",
            parameters={"user_id": user_id}
        )
        
        if user_check[0][0] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользователь с ID {user_id} не найден"
            )
        
        # Получаем статистику
        stats_query = """
        SELECT 
            count() as total_interactions,
            uniq(track_id) as unique_tracks,
            sum(listen_duration_seconds) / 3600.0 as total_listen_hours
        FROM user_track_interactions
        WHERE user_id = {user_id:UInt32}
        """
        
        stats_result = await clickhouse.execute_raw(stats_query, parameters={"user_id": user_id})
        stats_row = stats_result[0] if stats_result else (0, 0, 0.0)
        
        # Получаем любимый жанр
        genre_query = """
        SELECT t.genre, count() as cnt
        FROM user_track_interactions i
        JOIN tracks t ON i.track_id = t.track_id
        WHERE i.user_id = {user_id:UInt32} AND t.genre != ''
        GROUP BY t.genre
        ORDER BY cnt DESC
        LIMIT 1
        """
        
        genre_result = await clickhouse.execute_raw(genre_query, parameters={"user_id": user_id})
        favorite_genre = genre_result[0][0] if genre_result else None
        
        return UserStatistics(
            user_id=user_id,
            total_interactions=stats_row[0],
            unique_tracks=stats_row[1],
            favorite_genre=favorite_genre,
            total_listen_time_hours=round(stats_row[2], 2)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении статистики: {str(e)}"
        )
