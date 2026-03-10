import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendedTrack,
)
from app.routers.tracks import _get_track_by_row
from app.db.clickhouse import get_clickhouse_client
from app.config import settings
from app.services.cache import (
    get_cached_recommendations,
    set_cached_recommendations,
    exists_user_cached,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)

SETTINGS: str = """SETTINGS
    max_memory_usage = 20_000_000_000,
    max_bytes_before_external_group_by = 10_000_000_000,
    max_bytes_before_external_sort = 10_000_000_000,
    max_bytes_in_join = 8_000_000_000"""


@router.post(
    "",
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
    cached = await get_cached_recommendations(
        user_id=request.user_id,
        top_n=request.top_n or 10,
        exclude_listened=request.exclude_listened,
    )

    if cached:
        logger.info(
            "Recommendations served from CACHE: user_id=%s, top_n=%s, exclude_listened=%s",
            request.user_id,
            request.top_n or 10,
            request.exclude_listened,
        )
        return RecommendationResponse(**cached)

    clickhouse = get_clickhouse_client()

    try:
        _ = await exists_user_cached(request.user_id, clickhouse)

        interaction_count = await clickhouse.execute(
            f"SELECT count() FROM user_track_interactions PREWHERE user_id = {request.user_id}"
        )

        if (
            interaction_count[0][0]
            < settings.min_interactions_for_recommendations
        ):
            return await get_popular_recommendations(request)

        # Collaborative Filtering: находим похожих пользователей
        similar_users_query = f"""
        WITH user_tracks AS (
            SELECT track_id, implicit_rating
            FROM user_track_matrix
            PREWHERE user_id = {request.user_id} AND implicit_rating > 0
            LIMIT 1000
        )
        SELECT
            m2.user_id,
            sum(m2.implicit_rating * ut.implicit_rating) /
                (sqrt(sum(m2.implicit_rating * m2.implicit_rating)) *
                 sqrt(sum(ut.implicit_rating * ut.implicit_rating))) as similarity
        FROM user_track_matrix m2
        INNER JOIN user_tracks ut ON m2.track_id = ut.track_id
        PREWHERE m2.user_id != {request.user_id}
          AND m2.implicit_rating > 0
        GROUP BY m2.user_id
        HAVING similarity > 0.1
        ORDER BY similarity DESC
        LIMIT 50
        {SETTINGS}
        """

        similar_users = await clickhouse.execute(similar_users_query)

        if not similar_users:
            return await get_popular_recommendations(request)

        similar_user_ids = [row[0] for row in similar_users]
        similar_user_ids_str = ",".join(map(str, similar_user_ids))

        # Находим треки, которые понравились похожим пользователям
        exclude_join = ""
        exclude_where = ""
        if request.exclude_listened:
            exclude_join = f"""
            LEFT JOIN (
                SELECT DISTINCT track_id
                FROM user_track_interactions
                PREWHERE user_id = {request.user_id}
            ) excluded ON t.track_id = excluded.track_id
            """
            exclude_where = "AND excluded.track_id IS NULL"

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
        {exclude_join}
        PREWHERE m.user_id IN ({similar_user_ids_str})
          AND m.implicit_rating > 0
        WHERE 1=1
        {exclude_where}
        GROUP BY t.track_id, t.title, t.artist, t.album, t.genre,
                 t.duration_seconds, t.release_year, t.created_at
        ORDER BY total_score DESC
        LIMIT {request.top_n}
        {SETTINGS}
        """

        result = await clickhouse.execute(recommendations_query)

        if not result:
            return await get_popular_recommendations(request)

        recommendations = _build_recommendations(
            result, reason="Пользователи с похожими вкусами также слушают этот трек"
        )

        response = RecommendationResponse(
            user_id=request.user_id,
            recommendations=recommendations,
            generated_at=datetime.now(),
            algorithm="collaborative_filtering",
        )

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
        error_str = str(e)
        if "Code: 241" in error_str or "MEMORY_LIMIT_EXCEEDED" in error_str:
            logger.warning(
                "Memory limit exceeded for recommendations, falling back to popular tracks: %s",
                error_str,
            )
            try:
                return await get_popular_recommendations(request)
            except Exception as fallback_error:
                logger.error(
                    "Fallback to popular recommendations also failed: %s",
                    fallback_error,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Ошибка при генерации рекомендаций (memory limit): {error_str[:200]}",
                )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации рекомендаций: {error_str[:200]}",
        )


def _build_recommendations(
    result: list, reason: str
) -> list[RecommendedTrack]:
    """Построить список RecommendedTrack из результата запроса."""
    recommendations = []
    max_score = result[0][8] if result else 1.0

    for row in result:
        track = _get_track_by_row(row)
        normalized_score = row[8] / max_score if max_score > 0 else 0.0
        recommendations.append(
            RecommendedTrack(
                track=track,
                score=round(normalized_score, 3),
                reason=reason,
            )
        )
    return recommendations


async def get_popular_recommendations(
    request: RecommendationRequest,
) -> RecommendationResponse:
    """
    Получение рекомендаций на основе популярных треков
    (используется для холодного старта)
    """
    clickhouse = get_clickhouse_client()

    exclude_join = ""
    exclude_where = ""
    if request.exclude_listened:
        exclude_join = f"""
        LEFT JOIN (
            SELECT DISTINCT track_id
            FROM user_track_interactions
            PREWHERE user_id = {request.user_id}
        ) excluded ON t.track_id = excluded.track_id
        """
        exclude_where = "AND excluded.track_id IS NULL"

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
    {exclude_join}
    PREWHERE i.action_type = 'play'
      AND i.timestamp >= now() - INTERVAL 30 DAY
    WHERE 1=1
    {exclude_where}
    GROUP BY t.track_id, t.title, t.artist, t.album, t.genre,
             t.duration_seconds, t.release_year, t.created_at
    ORDER BY play_count DESC
    LIMIT {request.top_n}
    {SETTINGS}
    """

    result = await clickhouse.execute(query)

    recommendations = _build_recommendations(
        result, reason="Популярный трек на платформе"
    )

    response = RecommendationResponse(
        user_id=request.user_id,
        recommendations=recommendations,
        generated_at=datetime.now(),
        algorithm="popular_based",
    )

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
