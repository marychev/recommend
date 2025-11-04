"""
API эндпоинты для работы с треками
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Path, Query

from app.models.schemas import Track, TrackCreate, TrackStatistics
from app.db.clickhouse import get_clickhouse_client

router = APIRouter()


@router.post(
    "/tracks",
    response_model=Track,
    status_code=status.HTTP_201_CREATED,
    summary="Создать трек",
    description="Добавляет новый трек в каталог",
)
async def create_track(track: TrackCreate):
    """
    Создание нового трека

    Пример запроса:
    ```json
    {
        "title": "Bohemian Rhapsody",
        "artist": "Queen",
        "album": "A Night at the Opera",
        "genre": "Rock",
        "duration_seconds": 354,
        "release_year": 1975
    }
    ```
    """
    clickhouse = get_clickhouse_client()

    try:
        # Генерируем ID
        result = await clickhouse.execute_raw(
            "SELECT max(track_id) as max_id FROM tracks"
        )
        max_id = result[0][0] if result and result[0][0] else 0
        new_id = (max_id or 0) + 1

        # Вставляем трек
        await clickhouse.insert(
            "tracks",
            [
                [
                    new_id,
                    track.title,
                    track.artist,
                    track.album or "",
                    track.genre or "",
                    track.duration_seconds or 0,
                    track.release_year or 0,
                    datetime.now(),
                ]
            ],
            column_names=[
                "track_id",
                "title",
                "artist",
                "album",
                "genre",
                "duration_seconds",
                "release_year",
                "created_at",
            ],
        )

        return Track(
            track_id=new_id,
            title=track.title,
            artist=track.artist,
            album=track.album,
            genre=track.genre,
            duration_seconds=track.duration_seconds,
            release_year=track.release_year,
            created_at=datetime.now(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании трека: {str(e)}",
        )


@router.get(
    "/tracks/{track_id}",
    response_model=Track,
    summary="Получить трек",
    description="Возвращает информацию о треке по его ID",
)
async def get_track(
    track_id: int = Path(..., description="ID трека", examples=[12345])
):
    """
    Получение информации о треке по ID
    """
    clickhouse = get_clickhouse_client()

    try:
        result = await clickhouse.execute_raw(
            f"""SELECT track_id, title, artist, album, genre, 
                      duration_seconds, release_year, created_at 
               FROM tracks WHERE track_id = {track_id}"""
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Трек с ID {track_id} не найден",
            )

        row = result[0]
        return Track(
            track_id=row[0],
            title=row[1],
            artist=row[2],
            album=row[3],
            genre=row[4],
            duration_seconds=row[5],
            release_year=row[6],
            created_at=row[7],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении трека: {str(e)}",
        )


@router.get(
    "/tracks",
    response_model=List[Track],
    summary="Список треков",
    description="Возвращает список треков с возможностью фильтрации по жанру и исполнителю",
)
async def list_tracks(
    genre: Optional[str] = Query(
        None, description="Фильтр по жанру", examples=["Rock"]
    ),
    artist: Optional[str] = Query(
        None, description="Фильтр по исполнителю", examples=["Queen"]
    ),
    limit: int = Query(100, description="Количество записей", ge=1, le=1000),
    offset: int = Query(0, description="Смещение", ge=0),
):
    """
    Получение списка треков с фильтрацией и пагинацией
    """
    clickhouse = get_clickhouse_client()

    try:
        # Строим запрос с фильтрами
        where_clauses = []
        if genre:
            where_clauses.append(f"genre = '{genre}'")
        if artist:
            where_clauses.append(f"artist = '{artist}'")

        where_sql = (
            f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        )

        query = f"""
            SELECT track_id, title, artist, album, genre, 
                   duration_seconds, release_year, created_at 
            FROM tracks 
            {where_sql}
            ORDER BY track_id 
            LIMIT {limit} OFFSET {offset}
        """

        result = await clickhouse.execute_raw(query)

        tracks = []
        for row in result:
            tracks.append(
                Track(
                    track_id=row[0],
                    title=row[1],
                    artist=row[2],
                    album=row[3],
                    genre=row[4],
                    duration_seconds=row[5],
                    release_year=row[6],
                    created_at=row[7],
                )
            )

        return tracks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка треков: {str(e)}",
        )


@router.get(
    "/tracks/{track_id}/statistics",
    response_model=TrackStatistics,
    summary="Статистика трека",
    description="Возвращает статистику прослушиваний трека",
)
async def get_track_statistics(
    track_id: int = Path(..., description="ID трека", examples=[12345])
):
    """
    Получение статистики трека:
    - Общее количество прослушиваний
    - Количество уникальных слушателей
    - Количество лайков
    - Средний процент прослушивания
    """
    clickhouse = get_clickhouse_client()

    try:
        # Проверяем существование трека
        track_check = await clickhouse.execute_raw(
            f"SELECT count(), duration_seconds FROM tracks WHERE track_id = {track_id} GROUP BY duration_seconds"
        )

        if not track_check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Трек с ID {track_id} не найден",
            )

        track_duration = track_check[0][1]

        # Получаем статистику
        stats_query = f"""
        SELECT 
            countIf(action_type = 'play') as total_plays,
            uniq(user_id) as unique_listeners,
            countIf(action_type = 'like') as total_likes,
            avg(listen_duration_seconds) as avg_listen_duration
        FROM user_track_interactions
        WHERE track_id = {track_id}
        """

        stats_result = await clickhouse.execute_raw(stats_query)
        stats_row = stats_result[0] if stats_result else (0, 0, 0, 0.0)

        # Рассчитываем средний процент прослушивания
        avg_listen_percentage = 0.0
        if track_duration and track_duration > 0 and stats_row[3]:
            avg_listen_percentage = (stats_row[3] / track_duration) * 100

        return TrackStatistics(
            track_id=track_id,
            total_plays=stats_row[0],
            unique_listeners=stats_row[1],
            total_likes=stats_row[2],
            average_listen_percentage=round(avg_listen_percentage, 2),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении статистики: {str(e)}",
        )


@router.get(
    "/tracks/popular/top",
    response_model=List[Track],
    summary="Популярные треки",
    description="Возвращает список самых популярных треков за последние 30 дней",
)
async def get_popular_tracks(
    limit: int = Query(20, description="Количество треков", ge=1, le=100)
):
    """
    Получение топа популярных треков
    """
    clickhouse = get_clickhouse_client()

    try:
        query = f"""
        SELECT 
            t.track_id, t.title, t.artist, t.album, t.genre, 
            t.duration_seconds, t.release_year, t.created_at
        FROM tracks t
        INNER JOIN (
            SELECT track_id, count() as play_count
            FROM user_track_interactions
            WHERE action_type = 'play' 
              AND timestamp >= now() - INTERVAL 30 DAY
            GROUP BY track_id
            ORDER BY play_count DESC
            LIMIT {limit}
        ) AS popular ON t.track_id = popular.track_id
        ORDER BY popular.play_count DESC
        """

        result = await clickhouse.execute_raw(query)

        tracks = []
        for row in result:
            tracks.append(
                Track(
                    track_id=row[0],
                    title=row[1],
                    artist=row[2],
                    album=row[3],
                    genre=row[4],
                    duration_seconds=row[5],
                    release_year=row[6],
                    created_at=row[7],
                )
            )

        return tracks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении популярных треков: {str(e)}",
        )
