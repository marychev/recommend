"""
API эндпоинты для генерации рекомендаций
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Path

from app.models.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendedTrack,
    Track,
)
from app.db.clickhouse import get_clickhouse_client
from app.config import settings
from app.services.cache import (
    get_cached_recommendations,
    set_cached_recommendations,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="Получить рекомендации",
    description="Генерирует персонализированные рекомендации треков для пользователя",
)
async def get_recommendations(request: RecommendationRequest):
    """
    Генерация персонализированных рекомендаций для пользователя

    Используется алгоритм Collaborative Filtering на основе матрицы user-item.
    Результаты кэшируются в Redis на 1 час.

    Пример запроса:
    ```json
    {
        "user_id": 1001,
        "top_n": 10,
        "exclude_listened": true
    }
    ```

    Алгоритм:
    1. Проверка кэша в Redis
    2. Находит пользователей с похожими музыкальными вкусами
    3. Находит треки, которые понравились похожим пользователям
    4. Исключает треки, которые пользователь уже слушал (опционально)
    5. Ранжирует треки по релевантности
    6. Сохраняет результат в кэш
    """
    # Проверяем кэш
    cached = await get_cached_recommendations(
        user_id=request.user_id,
        top_n=request.top_n or 10,
        exclude_listened=request.exclude_listened,
    )

    if cached:
        logger.info(
            "Recommendations served from cache: user_id=%s", request.user_id
        )
        return RecommendationResponse(**cached)

    clickhouse = get_clickhouse_client()

    try:
        # Проверяем существование пользователя
        user_check = await clickhouse.execute(
            f"SELECT count() FROM users WHERE user_id = {request.user_id}"
        )
        if user_check[0][0] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользователь с ID {request.user_id} не найден",
            )

        # Проверяем минимальное количество взаимодействий
        interaction_count = await clickhouse.execute(
            f"SELECT count() FROM user_track_interactions WHERE user_id = {request.user_id}"
        )

        if (
            interaction_count[0][0]
            < settings.min_interactions_for_recommendations
        ):
            # Если недостаточно данных, возвращаем популярные треки
            return await get_popular_recommendations(request)

        # Collaborative Filtering: находим похожих пользователей
        similar_users_query = f"""
        WITH user_tracks AS (
            SELECT track_id, implicit_rating
            FROM user_track_matrix
            WHERE user_id = {request.user_id} AND implicit_rating > 0
        )
        SELECT 
            m2.user_id,
            sum(m2.implicit_rating * ut.implicit_rating) / 
                (sqrt(sum(m2.implicit_rating * m2.implicit_rating)) * 
                 sqrt(sum(ut.implicit_rating * ut.implicit_rating))) as similarity
        FROM user_track_matrix m2
        INNER JOIN user_tracks ut ON m2.track_id = ut.track_id
        WHERE m2.user_id != {request.user_id}
          AND m2.implicit_rating > 0
        GROUP BY m2.user_id
        HAVING similarity > 0.1
        ORDER BY similarity DESC
        LIMIT 50
        """

        similar_users = await clickhouse.execute(similar_users_query)

        if not similar_users:
            # Если не найдено похожих пользователей, возвращаем популярные треки
            return await get_popular_recommendations(request)

        # Получаем ID похожих пользователей
        similar_user_ids = [row[0] for row in similar_users]
        similar_user_ids_str = ",".join(map(str, similar_user_ids))

        # Находим треки, которые понравились похожим пользователям
        exclude_clause = ""
        if request.exclude_listened:
            exclude_clause = f"""
            AND t.track_id NOT IN (
                SELECT DISTINCT track_id 
                FROM user_track_interactions 
                WHERE user_id = {request.user_id}
            )
            """

        recommendations_query = f"""
        SELECT 
            t.track_id,
            t.title,
            t.artist,
            t.album,
            t.genre,
            t.duration_seconds,
            t.release_year,
            t.created_at,
            sum(m.implicit_rating) as total_score
        FROM user_track_matrix m
        INNER JOIN tracks t ON m.track_id = t.track_id
        WHERE m.user_id IN ({similar_user_ids_str})
          AND m.implicit_rating > 0
          {exclude_clause}
        GROUP BY t.track_id, t.title, t.artist, t.album, t.genre, 
                 t.duration_seconds, t.release_year, t.created_at
        ORDER BY total_score DESC
        LIMIT {request.top_n}
        """

        result = await clickhouse.execute(recommendations_query)

        if not result:
            # Если нет рекомендаций, возвращаем популярные треки
            return await get_popular_recommendations(request)

        # Формируем ответ
        recommendations = []
        max_score = result[0][8] if result else 1.0

        for row in result:
            track = Track(
                track_id=row[0],
                title=row[1],
                artist=row[2],
                album=row[3],
                genre=row[4],
                duration_seconds=row[5],
                release_year=row[6],
                created_at=row[7],
            )

            # Нормализуем score от 0 до 1
            normalized_score = row[8] / max_score if max_score > 0 else 0.0

            recommendations.append(
                RecommendedTrack(
                    track=track,
                    score=round(normalized_score, 3),
                    reason="Пользователи с похожими вкусами также слушают этот трек",
                )
            )

        response = RecommendationResponse(
            user_id=request.user_id,
            recommendations=recommendations,
            generated_at=datetime.now(),
            algorithm="collaborative_filtering",
        )

        # Сохраняем в кэш
        await set_cached_recommendations(
            user_id=request.user_id,
            top_n=request.top_n or 10,
            exclude_listened=request.exclude_listened,
            recommendations=response.model_dump(),
        )

        logger.info(
            "Recommendations generated: user_id=%s, count=%s, algorithm=%s",
            request.user_id,
            len(recommendations),
            "collaborative_filtering",
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации рекомендаций: {str(e)}",
        )


async def get_popular_recommendations(
    request: RecommendationRequest,
) -> RecommendationResponse:
    """
    Получение рекомендаций на основе популярных треков
    (используется для холодного старта)
    """
    clickhouse = get_clickhouse_client()

    exclude_clause = ""
    if request.exclude_listened:
        exclude_clause = f"""
        AND t.track_id NOT IN (
            SELECT DISTINCT track_id 
            FROM user_track_interactions 
            WHERE user_id = {request.user_id}
        )
        """

    query = f"""
    SELECT 
        t.track_id,
        t.title,
        t.artist,
        t.album,
        t.genre,
        t.duration_seconds,
        t.release_year,
        t.created_at,
        count(*) as play_count
    FROM user_track_interactions i
    INNER JOIN tracks t ON i.track_id = t.track_id
    WHERE i.action_type = 'play'
      AND i.timestamp >= now() - INTERVAL 30 DAY
      {exclude_clause}
    GROUP BY t.track_id, t.title, t.artist, t.album, t.genre, 
             t.duration_seconds, t.release_year, t.created_at
    ORDER BY play_count DESC
    LIMIT {request.top_n}
    """

    result = await clickhouse.execute(query)

    recommendations = []
    max_score = result[0][8] if result else 1.0

    for row in result:
        track = Track(
            track_id=row[0],
            title=row[1],
            artist=row[2],
            album=row[3],
            genre=row[4],
            duration_seconds=row[5],
            release_year=row[6],
            created_at=row[7],
        )

        normalized_score = row[8] / max_score if max_score > 0 else 0.0

        recommendations.append(
            RecommendedTrack(
                track=track,
                score=round(normalized_score, 3),
                reason="Популярный трек на платформе",
            )
        )

    response = RecommendationResponse(
        user_id=request.user_id,
        recommendations=recommendations,
        generated_at=datetime.now(),
        algorithm="popular_based",
    )

    # Сохраняем в кэш
    await set_cached_recommendations(
        user_id=request.user_id,
        top_n=request.top_n or 10,
        exclude_listened=request.exclude_listened,
        recommendations=response.model_dump(),
    )

    logger.info(
        "Recommendations generated: user_id=%s, count=%s, algorithm=%s",
        request.user_id,
        len(recommendations),
        "popular_based",
    )

    return response


@router.get(
    "/recommendations/{user_id}",
    response_model=RecommendationResponse,
    summary="Получить рекомендации (GET)",
    description="Генерирует рекомендации для пользователя (упрощенный метод через GET)",
)
async def get_recommendations_simple(
    user_id: int = Path(..., description="ID пользователя", examples=[1001])
):
    """
    Упрощенный метод получения рекомендаций через GET запрос
    с параметрами по умолчанию
    """
    request = RecommendationRequest(
        user_id=user_id,
        top_n=settings.top_n_recommendations,
        exclude_listened=True,
    )
    return await get_recommendations(request)
