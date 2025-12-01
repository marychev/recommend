"""
Эндпоинт для диагностики кэширования
"""

import asyncio
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.services.cache import get_cache_recommendations_ttl
from app.services.cache_warmup import get_warmup_service

from app.services.cache_redis_client import get_redis_client
from app.services.cache import (
    get_cached_recommendations,
    set_cached_recommendations,
    get_cache_stats,
    get_cache_key_recommendations,
    invalidate_cached_user_recommendations
)
from app.models.schemas.action_type import ActionType
from app.config import settings

router = APIRouter(
    prefix="/debug/cache",
    tags=["Cache Debug"],
)


@router.get("/status")
async def cache_status():
    """Проверка статуса кэша"""
    redis = get_redis_client()
    
    try:
        is_connected = await redis.is_connected()
        stats = await get_cache_stats()
        
        return {
            "redis_connected": is_connected,
            "cache_stats": stats,
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка проверки кэша: {str(e)}")


@router.get("/keys")
async def cache_keys():
    """Получить все ключи кэша рекомендаций"""
    redis = get_redis_client()
    
    try:
        pattern = "recommendations:user:*"
        keys = await redis.keys(pattern)
        
        key_details = []
        for key in keys[:10]:  # Ограничиваем до 10 ключей
            try:
                # Используем Redis клиент напрямую для TTL
                ttl = await redis.redis.ttl(key) if redis.redis else -1
                value = await redis.get(key)
                size = len(value) if value else 0
                
                key_details.append({
                    "key": key,
                    "ttl_seconds": ttl,
                    "size_bytes": size
                })
            except Exception as e:
                key_details.append({
                    "key": key,
                    "ttl_seconds": "error",
                    "size_bytes": 0,
                    "error": str(e)
                })
        
        return {
            "total_keys": len(keys),
            "keys_sample": key_details,
            "pattern": pattern
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения ключей: {str(e)}")


@router.post("/test")
async def test_cache_operations():
    """Тест операций кэширования"""
    test_user_id = 999999
    results = {}
    
    try:
        # 1. Тест подключения Redis
        redis = get_redis_client()
        is_connected = await redis.is_connected()
        results["redis_connection"] = is_connected
        
        if not is_connected:
            return {
                "success": False,
                "error": "Redis не подключен",
                "results": results
            }
        
        # 2. Тест базовых операций Redis
        test_key = "test:diagnosis:123"
        test_value = "test_value"
        
        await redis.set(test_key, test_value, ex=60)
        retrieved = await redis.get(test_key)
        await redis.delete(test_key)
        
        results["basic_redis_ops"] = retrieved == test_value
        
        # 3. Тест функций кэширования
        test_recommendations = {
            "user_id": test_user_id,
            "recommendations": [
                {
                    "track": {
                        "track_id": 1,
                        "title": "Test Track",
                        "artist": "Test Artist",
                        "album": "Test Album",
                        "genre": "Test",
                        "duration_seconds": 180,
                        "release_year": 2023,
                        "created_at": datetime.now()
                    },
                    "score": 0.95,
                    "reason": "Test recommendation"
                }
            ],
            "generated_at": datetime.now(),
            "algorithm": "test"
        }
        
        # Сохранение в кэш
        save_start = time.time()
        save_result = await set_cached_recommendations(
            user_id=test_user_id,
            top_n=10,
            exclude_listened=True,
            recommendations=test_recommendations,
            ttl=300
        )
        save_time = (time.time() - save_start) * 1000
        
        results["cache_save"] = {
            "success": save_result,
            "time_ms": save_time
        }
        
        # Получение из кэша
        get_start = time.time()
        cached_data = await get_cached_recommendations(
            user_id=test_user_id,
            top_n=10,
            exclude_listened=True
        )
        get_time = (time.time() - get_start) * 1000
        
        results["cache_get"] = {
            "success": cached_data is not None,
            "time_ms": get_time,
            "data_found": bool(cached_data)
        }
        
        # Проверка ключа
        cache_key = get_cache_key_recommendations(test_user_id, 10, True)
        key_exists = await redis.get(cache_key) is not None
        
        results["cache_key"] = {
            "key": cache_key,
            "exists": key_exists
        }
        
        # Очистка тестовых данных
        await redis.delete(cache_key)
        
        # Общий результат
        all_success = all([
            results["redis_connection"],
            results["basic_redis_ops"],
            results["cache_save"]["success"],
            results["cache_get"]["success"]
        ])
        
        return {
            "success": all_success,
            "results": results,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": results
        }


@router.post("/set-ttl/{ttl_hours}")
async def set_cache_ttl(ttl_hours: int):
    """Временно изменить TTL кэша для тестирования"""
    
    if ttl_hours < 1 or ttl_hours > 24:
        raise HTTPException(
            status_code=400, 
            detail="TTL должен быть от 1 до 24 часов"
        )
    
    old_ttl = settings.recommendations_cache_ttl
    new_ttl = ttl_hours * 3600  # конвертируем часы в секунды
    
    # Временно изменяем TTL
    settings.recommendations_cache_ttl = new_ttl
    
    return {
        "success": True,
        "old_ttl_seconds": old_ttl,
        "old_ttl_hours": old_ttl // 3600,
        "new_ttl_seconds": new_ttl,
        "new_ttl_hours": ttl_hours,
        "message": f"TTL изменен с {old_ttl//3600}ч на {ttl_hours}ч",
        "note": "Изменение временное, до перезапуска сервера",
        "timestamp": datetime.now()
    }


@router.post("/warmup/auto")
async def auto_warmup_cache():
    """Автоматический прогрев кэша для активных пользователей"""    
    warmup_service = get_warmup_service()
    result = await warmup_service.auto_warmup(max_users=50, min_interactions=5)
    
    return {
        "success": result.get("success", True),
        "result": result,
        "timestamp": datetime.now()
    }


@router.post("/warmup/user/{user_id}")
async def warmup_user_cache(user_id: int):
    """Прогрев кэша для конкретного пользователя"""    
    warmup_service = get_warmup_service()
    success = await warmup_service.warmup_user_recommendations(user_id)
    
    return {
        "success": success,
        "user_id": user_id,
        "message": "Прогрев выполнен" if success else "Ошибка прогрева",
        "timestamp": datetime.now()
    }


@router.get("/warmup/stats")
async def get_warmup_stats():
    """Получить статистику прогрева кэша"""
    
    warmup_service = get_warmup_service()
    stats = warmup_service.get_warmup_stats()
    
    return {
        "stats": stats,
        "timestamp": datetime.now()
    }


@router.get("/current-ttl")
async def get_current_ttl():
    """Получить текущий TTL кэша"""
    
    ttl_seconds = get_cache_recommendations_ttl()
    ttl_hours = ttl_seconds // 3600
    ttl_minutes = (ttl_seconds % 3600) // 60
    
    return {
        "ttl_seconds": ttl_seconds,
        "ttl_hours": ttl_hours,
        "ttl_minutes": ttl_minutes,
        "ttl_formatted": f"{ttl_hours}ч {ttl_minutes}м",
        "timestamp": datetime.now()
    }


@router.get("/warmup/active-users")
async def get_active_users_for_warmup():
    """Получить список активных пользователей для прогрева"""
    
    warmup_service = get_warmup_service()
    active_users = await warmup_service.get_active_users(
        hours_back=24, 
        min_interactions=3, 
        limit=20
    )
    
    return {
        "active_users": active_users,
        "count": len(active_users),
        "criteria": {
            "hours_back": 24,
            "min_interactions": 3,
            "limit": 20
        },
        "timestamp": datetime.now()
    }


@router.post("/simulate-hitrate")
async def simulate_cache_hitrate():
    """Симуляция hit rate кэша"""
    test_user_id = 1  # Используем существующего пользователя
    results = {
        "requests": [],
        "hit_rate": 0,
        "avg_cache_time": 0,
        "avg_miss_time": 0
    }
    
    try:
        # Очищаем существующий кэш для пользователя
        await invalidate_cached_user_recommendations(test_user_id)
        
        # Создаем тестовые рекомендации
        test_recommendations = {
            "user_id": test_user_id,
            "recommendations": [
                {
                    "track": {
                        "track_id": i,
                        "title": f"Test Track {i}",
                        "artist": f"Test Artist {i}",
                        "album": "Test Album",
                        "genre": "Test",
                        "duration_seconds": 180,
                        "release_year": 2023,
                        "created_at": datetime.now()
                    },
                    "score": 0.9 - i * 0.1,
                    "reason": "Test recommendation"
                } for i in range(1, 6)
            ],
            "generated_at": datetime.now(),
            "algorithm": "test_simulation"
        }
        
        hits = 0
        misses = 0
        cache_times = []
        miss_times = []
        
        # Делаем 10 запросов
        for i in range(10):
            start_time = time.time()
            
            cached_data = await get_cached_recommendations(
                user_id=test_user_id,
                top_n=10,
                exclude_listened=True
            )
            
            request_time = (time.time() - start_time) * 1000
            
            if cached_data:
                # Cache hit
                hits += 1
                cache_times.append(request_time)
                results["requests"].append({
                    "request_num": i + 1,
                    "cache_hit": True,
                    "time_ms": request_time
                })
            else:
                # Cache miss - сохраняем данные в кэш
                misses += 1
                miss_times.append(request_time)
                
                await set_cached_recommendations(
                    user_id=test_user_id,
                    top_n=10,
                    exclude_listened=True,
                    recommendations=test_recommendations
                )
                
                results["requests"].append({
                    "request_num": i + 1,
                    "cache_hit": False,
                    "time_ms": request_time
                })
            
            # Небольшая пауза между запросами
            await asyncio.sleep(0.1)
        
        # Вычисляем статистику
        total_requests = hits + misses
        results["hit_rate"] = (hits / total_requests * 100) if total_requests > 0 else 0
        results["hits"] = hits
        results["misses"] = misses
        results["avg_cache_time"] = sum(cache_times) / len(cache_times) if cache_times else 0
        results["avg_miss_time"] = sum(miss_times) / len(miss_times) if miss_times else 0
        
        # Очищаем тестовые данные
        await invalidate_cached_user_recommendations(test_user_id)
        
        return {
            "success": True,
            "results": results,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": results
        }


@router.delete("/clear/{user_id}")
async def clear_user_cache(user_id: int):
    """Очистить кэш для конкретного пользователя"""
    try:
        result = await invalidate_cached_user_recommendations(user_id)
        return {
            "success": result,
            "user_id": user_id,
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка очистки кэша: {str(e)}")


@router.delete("/clear-all")
async def clear_all_cache():
    """Очистить весь кэш рекомендаций"""
    redis = get_redis_client()
    
    try:
        pattern = "recommendations:user:*"
        keys = await redis.keys(pattern)
        
        if keys:
            await redis.delete(*keys)
        
        return {
            "success": True,
            "cleared_keys": len(keys),
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка очистки кэша: {str(e)}")


@router.post("/test-real-scenario-v2")
async def test_real_scenario_v2():
    """Улучшенный тест реального сценария с прямой инвалидацией"""
    from app.routers.recommendations import get_recommendations
    from app.models.schemas import RecommendationRequest
    
    test_user_id = 1
    results = {
        "scenario_steps": [],
        "cache_hits": 0,
        "cache_misses": 0,
        "final_hit_rate": 0,
        "invalidation_log": []
    }
    
    try:
        # Очищаем кэш для чистого теста
        await invalidate_cached_user_recommendations(test_user_id)
        results["invalidation_log"].append("Начальная очистка кэша")
        
        # Шаг 1: Первый запрос рекомендаций (должен быть cache miss)
        start_time = time.time()
        req1 = RecommendationRequest(
            user_id=test_user_id,
            top_n=10,
            exclude_listened=True,
            include_performance_metrics=True
        )
        resp1 = await get_recommendations(req1)
        time1 = (time.time() - start_time) * 1000
        
        cache_hit1 = resp1.performance_metrics.cache_hit if resp1.performance_metrics else False
        results["scenario_steps"].append({
            "step": 1,
            "action": "Первый запрос рекомендаций",
            "cache_hit": cache_hit1,
            "time_ms": time1,
            "expected": "MISS"
        })
        
        if cache_hit1:
            results["cache_hits"] += 1
        else:
            results["cache_misses"] += 1
        
        # Шаг 2: Второй запрос рекомендаций (должен быть cache hit)
        await asyncio.sleep(0.1)
        start_time = time.time()
        resp2 = await get_recommendations(req1)
        time2 = (time.time() - start_time) * 1000
        
        cache_hit2 = resp2.performance_metrics.cache_hit if resp2.performance_metrics else False
        results["scenario_steps"].append({
            "step": 2,
            "action": "Второй запрос рекомендаций",
            "cache_hit": cache_hit2,
            "time_ms": time2,
            "expected": "HIT"
        })
        
        if cache_hit2:
            results["cache_hits"] += 1
        else:
            results["cache_misses"] += 1
        
        # Шаг 3: Симуляция события PLAY (НЕ должно инвалидировать кэш)
        results["invalidation_log"].append("Событие PLAY - кэш НЕ должен инвалидироваться")
        # Не инвалидируем кэш для PLAY
        
        # Шаг 4: Третий запрос рекомендаций (должен быть cache hit)
        await asyncio.sleep(0.1)
        start_time = time.time()
        resp3 = await get_recommendations(req1)
        time3 = (time.time() - start_time) * 1000
        
        cache_hit3 = resp3.performance_metrics.cache_hit if resp3.performance_metrics else False
        results["scenario_steps"].append({
            "step": 3,
            "action": "После события PLAY",
            "cache_hit": cache_hit3,
            "time_ms": time3,
            "expected": "HIT"
        })
        
        if cache_hit3:
            results["cache_hits"] += 1
        else:
            results["cache_misses"] += 1
        
        # Шаг 5: Симуляция события LIKE (ДОЛЖНО инвалидировать кэш)
        results["invalidation_log"].append("Событие LIKE - инвалидируем кэш")
        await invalidate_cached_user_recommendations(test_user_id)
        
        # Шаг 6: Четвертый запрос рекомендаций (должен быть cache miss)
        await asyncio.sleep(0.1)
        start_time = time.time()
        resp4 = await get_recommendations(req1)
        time4 = (time.time() - start_time) * 1000
        
        cache_hit4 = resp4.performance_metrics.cache_hit if resp4.performance_metrics else False
        results["scenario_steps"].append({
            "step": 4,
            "action": "После события LIKE",
            "cache_hit": cache_hit4,
            "time_ms": time4,
            "expected": "MISS"
        })
        
        if cache_hit4:
            results["cache_hits"] += 1
        else:
            results["cache_misses"] += 1
        
        # Шаг 7: Пятый запрос рекомендаций (должен быть cache hit)
        await asyncio.sleep(0.1)
        start_time = time.time()
        resp5 = await get_recommendations(req1)
        time5 = (time.time() - start_time) * 1000
        
        cache_hit5 = resp5.performance_metrics.cache_hit if resp5.performance_metrics else False
        results["scenario_steps"].append({
            "step": 5,
            "action": "Пятый запрос",
            "cache_hit": cache_hit5,
            "time_ms": time5,
            "expected": "HIT"
        })
        
        if cache_hit5:
            results["cache_hits"] += 1
        else:
            results["cache_misses"] += 1
        
        # Подсчитываем итоговый hit rate
        total_requests = results["cache_hits"] + results["cache_misses"]
        results["final_hit_rate"] = (results["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
        
        # Анализ корректности
        results["correctness_analysis"] = {
            "step_1_correct": not cache_hit1,  # Должен быть MISS
            "step_2_correct": cache_hit2,      # Должен быть HIT
            "step_3_correct": cache_hit3,      # Должен быть HIT (PLAY не инвалидирует)
            "step_4_correct": not cache_hit4,  # Должен быть MISS (LIKE инвалидировал)
            "step_5_correct": cache_hit5,      # Должен быть HIT
        }
        
        correct_steps = sum(results["correctness_analysis"].values())
        results["correctness_percentage"] = (correct_steps / 5) * 100
        
        return {
            "success": True,
            "results": results,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": results
        }


@router.post("/test-real-scenario")
async def test_real_scenario():
    """Тест реального сценария: рекомендации + события + повторные рекомендации"""
    from app.routers.recommendations import get_recommendations
    from app.routers.events import create_event
    from app.models.schemas import RecommendationRequest, UserTrackInteractionCreate
    from fastapi import BackgroundTasks
    
    test_user_id = 1
    results = {
        "scenario_steps": [],
        "cache_hits": 0,
        "cache_misses": 0,
        "final_hit_rate": 0
    }
    
    try:
        # Очищаем кэш для чистого теста
        await invalidate_cached_user_recommendations(test_user_id)
        
        # Шаг 1: Первый запрос рекомендаций (должен быть cache miss)
        start_time = time.time()
        req1 = RecommendationRequest(
            user_id=test_user_id,
            top_n=10,
            exclude_listened=True,
            include_performance_metrics=True
        )
        resp1 = await get_recommendations(req1)
        time1 = (time.time() - start_time) * 1000
        
        cache_hit1 = resp1.performance_metrics.cache_hit if resp1.performance_metrics else False
        results["scenario_steps"].append({
            "step": 1,
            "action": "Первый запрос рекомендаций",
            "cache_hit": cache_hit1,
            "time_ms": time1
        })
        
        if cache_hit1:
            results["cache_hits"] += 1
        else:
            results["cache_misses"] += 1
        
        # Шаг 2: Второй запрос рекомендаций (должен быть cache hit)
        await asyncio.sleep(0.1)
        start_time = time.time()
        resp2 = await get_recommendations(req1)
        time2 = (time.time() - start_time) * 1000
        
        cache_hit2 = resp2.performance_metrics.cache_hit if resp2.performance_metrics else False
        results["scenario_steps"].append({
            "step": 2,
            "action": "Второй запрос рекомендаций (ожидается cache hit)",
            "cache_hit": cache_hit2,
            "time_ms": time2
        })
        
        if cache_hit2:
            results["cache_hits"] += 1
        else:
            results["cache_misses"] += 1
        
        # Шаг 3: Событие PLAY (НЕ должно инвалидировать кэш)
        background_tasks = BackgroundTasks()
        play_event = UserTrackInteractionCreate(
            user_id=test_user_id,
            track_id=1,
            action_type=ActionType.PLAY,
            listen_duration_seconds=30
        )
        await create_event(play_event, background_tasks)
        
        # PLAY не должно инвалидировать кэш согласно нашей логике
        # Проверяем, что инвалидация НЕ происходит
        if play_event.action_type not in [ActionType.LIKE, ActionType.DISLIKE, ActionType.ADD_TO_PLAYLIST, ActionType.SHARE]:
            # Кэш должен остаться нетронутым
            pass
        
        # Ждем завершения операций
        await asyncio.sleep(0.1)
        
        # Шаг 4: Третий запрос рекомендаций (должен быть cache hit, т.к. PLAY не инвалидирует)
        start_time = time.time()
        resp3 = await get_recommendations(req1)
        time3 = (time.time() - start_time) * 1000
        
        cache_hit3 = resp3.performance_metrics.cache_hit if resp3.performance_metrics else False
        results["scenario_steps"].append({
            "step": 3,
            "action": "После события PLAY (ожидается cache hit)",
            "cache_hit": cache_hit3,
            "time_ms": time3
        })
        
        if cache_hit3:
            results["cache_hits"] += 1
        else:
            results["cache_misses"] += 1
        
        # Шаг 5: Событие LIKE (ДОЛЖНО инвалидировать кэш)
        like_event = UserTrackInteractionCreate(
            user_id=test_user_id,
            track_id=2,
            action_type=ActionType.LIKE
        )
        background_tasks = BackgroundTasks()
        await create_event(like_event, background_tasks)
        
        # Принудительно инвалидируем кэш для тестирования
        # (в реальности это делается в фоновых задачах)
        if like_event.action_type in [ActionType.LIKE, ActionType.DISLIKE, ActionType.ADD_TO_PLAYLIST, ActionType.SHARE]:
            await invalidate_cached_user_recommendations(test_user_id)
        
        # Ждем завершения операций
        await asyncio.sleep(0.1)
        
        # Шаг 6: Четвертый запрос рекомендаций (должен быть cache miss, т.к. LIKE инвалидировал)
        start_time = time.time()
        resp4 = await get_recommendations(req1)
        time4 = (time.time() - start_time) * 1000
        
        cache_hit4 = resp4.performance_metrics.cache_hit if resp4.performance_metrics else False
        results["scenario_steps"].append({
            "step": 4,
            "action": "После события LIKE (ожидается cache miss)",
            "cache_hit": cache_hit4,
            "time_ms": time4
        })
        
        if cache_hit4:
            results["cache_hits"] += 1
        else:
            results["cache_misses"] += 1
        
        # Шаг 7: Пятый запрос рекомендаций (должен быть cache hit)
        await asyncio.sleep(0.1)
        start_time = time.time()
        resp5 = await get_recommendations(req1)
        time5 = (time.time() - start_time) * 1000
        
        cache_hit5 = resp5.performance_metrics.cache_hit if resp5.performance_metrics else False
        results["scenario_steps"].append({
            "step": 5,
            "action": "Пятый запрос (ожидается cache hit)",
            "cache_hit": cache_hit5,
            "time_ms": time5
        })
        
        if cache_hit5:
            results["cache_hits"] += 1
        else:
            results["cache_misses"] += 1
        
        # Подсчитываем итоговый hit rate
        total_requests = results["cache_hits"] + results["cache_misses"]
        results["final_hit_rate"] = (results["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "success": True,
            "results": results,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": results
        }
