import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendedTrack,
    PerformanceMetrics,
)
from app.routers.tracks import _get_track_by_row
from app.db.clickhouse import get_clickhouse_client
from app.config import settings
from app.services.cache import (
    get_cached_recommendations,
    set_cached_recommendations,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


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
        "exclude_listened": true,
        "include_performance_metrics": true
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
    # Инициализация метрик производительности
    start_time = time.perf_counter()
    metrics: Optional[Dict[str, Any]] = (
        {} if request.include_performance_metrics else None
    )

    # Проверяем кэш
    redis_check_start = time.perf_counter()
    cached = await get_cached_recommendations(
        user_id=request.user_id,
        top_n=request.top_n or 10,
        exclude_listened=request.exclude_listened,
    )
    if metrics is not None:
        metrics["redis_check_time_ms"] = (
            time.perf_counter() - redis_check_start
        ) * 1000

    if cached:
        logger.info(
            "Recommendations served from cache: user_id=%s", request.user_id
        )
        response = RecommendationResponse(**cached)

        # Добавляем метрики для кэшированного ответа
        if metrics is not None:
            total_time = (time.perf_counter() - start_time) * 1000
            response.performance_metrics = PerformanceMetrics(
                total_time_ms=total_time,
                redis_check_time_ms=metrics.get("redis_check_time_ms"),
                cache_hit=True,
            )

        return response

    clickhouse = get_clickhouse_client()

    try:
        # Проверка существования пользователя
        user_check_start = time.perf_counter()
        _ = await clickhouse.exists_user(request.user_id)
        if metrics is not None:
            metrics["clickhouse_user_check_time_ms"] = (
                time.perf_counter() - user_check_start
            ) * 1000

        # Проверяем минимальное количество взаимодействий
        # Оптимизация: используем PREWHERE для фильтрации до чтения всех колонок
        interactions_count_start = time.perf_counter()
        interaction_count = await clickhouse.execute(
            f"SELECT count() FROM user_track_interactions PREWHERE user_id = {request.user_id}"
        )
        if metrics is not None:
            metrics["clickhouse_interactions_count_time_ms"] = (
                time.perf_counter() - interactions_count_start
            ) * 1000

        if (
            interaction_count[0][0]
            < settings.min_interactions_for_recommendations
        ):
            # Если недостаточно данных, возвращаем популярные треки
            return await get_popular_recommendations(
                request, metrics, start_time
            )

        # Collaborative Filtering: находим похожих пользователей
        # Добавляем SETTINGS для увеличения лимита памяти и использования внешней сортировки
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
        SETTINGS 
            max_memory_usage = 5000000000,
            max_bytes_before_external_group_by = 2000000000,
            max_bytes_before_external_sort = 2000000000,
            max_bytes_in_join = 1000000000
        """

        similar_users_start = time.perf_counter()
        similar_users = await clickhouse.execute(similar_users_query)
        if metrics is not None:
            metrics["clickhouse_similar_users_time_ms"] = (
                time.perf_counter() - similar_users_start
            ) * 1000
            metrics["similar_users_count"] = len(similar_users)

        if not similar_users:
            # Если не найдено похожих пользователей, возвращаем популярные треки
            return await get_popular_recommendations(
                request, metrics, start_time
            )

        # Получаем ID похожих пользователей
        similar_user_ids = [row[0] for row in similar_users]
        similar_user_ids_str = ",".join(map(str, similar_user_ids))

        # Находим треки, которые понравились похожим пользователям
        # Оптимизация: используем LEFT JOIN вместо NOT IN (быстрее в ClickHouse)
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
        SETTINGS 
            max_memory_usage = 5000000000,
            max_bytes_before_external_group_by = 2000000000,
            max_bytes_before_external_sort = 2000000000,
            max_bytes_in_join = 1000000000
        """

        recommendations_start = time.perf_counter()
        result = await clickhouse.execute(recommendations_query)
        if metrics is not None:
            metrics["clickhouse_recommendations_time_ms"] = (
                time.perf_counter() - recommendations_start
            ) * 1000

        if not result:
            # Если нет рекомендаций, возвращаем популярные треки
            return await get_popular_recommendations(
                request, metrics, start_time
            )

        # Формируем ответ
        algorithm_start = time.perf_counter()
        recommendations = []
        max_score = result[0][8] if result else 1.0

        for row in result:
            track = _get_track_by_row(row)

            # Нормализуем score от 0 до 1
            normalized_score = row[8] / max_score if max_score > 0 else 0.0

            recommendations.append(
                RecommendedTrack(
                    track=track,
                    score=round(normalized_score, 3),
                    reason="Пользователи с похожими вкусами также слушают этот трек",
                )
            )

        if metrics is not None:
            metrics["algorithm_processing_time_ms"] = (
                time.perf_counter() - algorithm_start
            ) * 1000

        response = RecommendationResponse(
            user_id=request.user_id,
            recommendations=recommendations,
            generated_at=datetime.now(),
            algorithm="collaborative_filtering",
        )

        # Сохраняем в кэш
        redis_save_start = time.perf_counter()
        await set_cached_recommendations(
            user_id=request.user_id,
            top_n=request.top_n or 10,
            exclude_listened=request.exclude_listened,
            recommendations=response.model_dump(),
        )
        if metrics is not None:
            metrics["redis_save_time_ms"] = (
                time.perf_counter() - redis_save_start
            ) * 1000

        # Добавляем метрики производительности в ответ
        if metrics is not None:
            total_time = (time.perf_counter() - start_time) * 1000
            response.performance_metrics = PerformanceMetrics(
                total_time_ms=total_time,
                redis_check_time_ms=metrics.get("redis_check_time_ms"),
                redis_save_time_ms=metrics.get("redis_save_time_ms"),
                clickhouse_user_check_time_ms=metrics.get(
                    "clickhouse_user_check_time_ms"
                ),
                clickhouse_interactions_count_time_ms=metrics.get(
                    "clickhouse_interactions_count_time_ms"
                ),
                clickhouse_similar_users_time_ms=metrics.get(
                    "clickhouse_similar_users_time_ms"
                ),
                clickhouse_recommendations_time_ms=metrics.get(
                    "clickhouse_recommendations_time_ms"
                ),
                algorithm_processing_time_ms=metrics.get(
                    "algorithm_processing_time_ms"
                ),
                cache_hit=False,
                similar_users_count=metrics.get("similar_users_count"),
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
        # Если ошибка памяти ClickHouse, возвращаем популярные треки как fallback
        if "Code: 241" in error_str or "MEMORY_LIMIT_EXCEEDED" in error_str:
            logger.warning(
                "Memory limit exceeded for recommendations, falling back to popular tracks: %s",
                error_str
            )
            try:
                return await get_popular_recommendations(
                    request, metrics, start_time
                )
            except Exception as fallback_error:
                logger.error("Fallback to popular recommendations also failed: %s", fallback_error)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Ошибка при генерации рекомендаций (memory limit): {error_str[:200]}",
                )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации рекомендаций: {error_str[:200]}",
        )


async def get_popular_recommendations(
    request: RecommendationRequest,
    metrics: Optional[Dict[str, Any]] = None,
    start_time: Optional[float] = None,
) -> RecommendationResponse:
    """
    Получение рекомендаций на основе популярных треков
    (используется для холодного старта)
    """
    clickhouse = get_clickhouse_client()

    # Оптимизация: используем LEFT JOIN вместо NOT IN (быстрее в ClickHouse)
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
    SETTINGS 
        max_memory_usage = 5000000000,
        max_bytes_before_external_group_by = 2000000000,
        max_bytes_before_external_sort = 2000000000,
        max_bytes_in_join = 1000000000
    """

    popular_query_start = time.perf_counter()
    result = await clickhouse.execute(query)
    if metrics is not None:
        metrics["clickhouse_popular_recommendations_time_ms"] = (
            time.perf_counter() - popular_query_start
        ) * 1000

    algorithm_start = time.perf_counter()
    recommendations = []
    max_score = result[0][8] if result else 1.0

    for row in result:
        track = _get_track_by_row(row)

        normalized_score = row[8] / max_score if max_score > 0 else 0.0

        recommendations.append(
            RecommendedTrack(
                track=track,
                score=round(normalized_score, 3),
                reason="Популярный трек на платформе",
            )
        )

    if metrics is not None:
        metrics["algorithm_processing_time_ms"] = (
            time.perf_counter() - algorithm_start
        ) * 1000

    response = RecommendationResponse(
        user_id=request.user_id,
        recommendations=recommendations,
        generated_at=datetime.now(),
        algorithm="popular_based",
    )

    # Сохраняем в кэш
    redis_save_start = time.perf_counter()
    await set_cached_recommendations(
        user_id=request.user_id,
        top_n=request.top_n or 10,
        exclude_listened=request.exclude_listened,
        recommendations=response.model_dump(),
    )
    if metrics is not None:
        metrics["redis_save_time_ms"] = (
            time.perf_counter() - redis_save_start
        ) * 1000

    # Добавляем метрики производительности в ответ
    if metrics is not None and start_time is not None:
        total_time = (time.perf_counter() - start_time) * 1000
        response.performance_metrics = PerformanceMetrics(
            total_time_ms=total_time,
            redis_check_time_ms=metrics.get("redis_check_time_ms"),
            redis_save_time_ms=metrics.get("redis_save_time_ms"),
            clickhouse_user_check_time_ms=metrics.get(
                "clickhouse_user_check_time_ms"
            ),
            clickhouse_interactions_count_time_ms=metrics.get(
                "clickhouse_interactions_count_time_ms"
            ),
            clickhouse_recommendations_time_ms=metrics.get(
                "clickhouse_popular_recommendations_time_ms"
            ),
            algorithm_processing_time_ms=metrics.get(
                "algorithm_processing_time_ms"
            ),
            cache_hit=False,
        )

    logger.info(
        "Recommendations generated: user_id=%s, count=%s, algorithm=%s",
        request.user_id,
        len(recommendations),
        "popular_based",
    )

    return response


# @router.get(
#     "/{user_id}",
#     response_model=RecommendationResponse,
#     summary="Получить рекомендации (GET)",
#     description="Генерирует рекомендации для пользователя (упрощенный метод через GET)",
# )
# async def get_recommendations_simple(
#     user_id: int = Path(..., description="ID пользователя", examples=[1001])
# ):
#     """
#     Упрощенный метод получения рекомендаций через GET запрос
#     с параметрами по умолчанию
#     """
#     request = RecommendationRequest(
#         user_id=user_id,
#         top_n=settings.top_n_recommendations,
#         exclude_listened=True,
#     )
#     return await get_recommendations(request)
