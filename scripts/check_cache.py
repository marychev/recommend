#!/usr/bin/env python3
"""
Скрипт для проверки кэширования рекомендаций

Использование:
    python scripts/check_cache.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.services.cache import (
    get_cached_recommendations,
    set_cached_recommendations,
    get_cache_stats,
    invalidate_cached_user_recommendations,
    get_cache_key_recommendations,
)
from app.services.cache_redis_client import get_redis_client


async def check_redis_connection():
    """Проверка подключения к Redis"""
    print("🔍 Проверка подключения к Redis...")
    redis = get_redis_client()
    is_connected = await redis.is_connected()
    
    if is_connected:
        print("✅ Redis подключен")
        return True
    else:
        print("❌ Redis НЕ подключен")
        return False


async def check_cache_stats():
    """Проверка статистики кэша"""
    print("\n📊 Статистика кэша:")
    stats = await get_cache_stats()
    print(f"   Статус: {stats.get('status', 'unknown')}")
    if 'cached_recommendations' in stats:
        print(f"   Закэшированных рекомендаций: {stats['cached_recommendations']}")
    if 'ttl_seconds' in stats:
        print(f"   TTL: {stats['ttl_seconds']} секунд ({stats['ttl_seconds'] / 3600:.1f} часов)")


async def test_cache_operations():
    """Тест операций кэширования"""
    print("\n🧪 Тест операций кэширования:")
    
    test_user_id = 999999
    test_recommendations = {
        "user_id": test_user_id,
        "recommendations": [
            {
                "track": {
                    "track_id": 1,
                    "title": "Test Track",
                    "artist": "Test Artist",
                },
                "score": 0.95,
                "reason": "Test reason"
            }
        ],
        "generated_at": "2024-01-01T00:00:00",
        "algorithm": "test"
    }
    
    # 1. Проверяем, что кэша нет
    print(f"\n1️⃣ Проверка кэша для user_id={test_user_id} (должен быть MISS)...")
    cached = await get_cached_recommendations(
        user_id=test_user_id,
        top_n=10,
        exclude_listened=True
    )
    if cached is None:
        print("   ✅ Cache MISS (ожидаемо)")
    else:
        print("   ⚠️ Cache HIT (неожиданно)")
    
    # 2. Сохраняем в кэш
    print(f"\n2️⃣ Сохранение рекомендаций в кэш для user_id={test_user_id}...")
    success = await set_cached_recommendations(
        user_id=test_user_id,
        top_n=10,
        exclude_listened=True,
        recommendations=test_recommendations
    )
    if success:
        print("   ✅ Рекомендации сохранены в кэш")
    else:
        print("   ❌ Ошибка сохранения в кэш")
        return
    
    # 3. Проверяем, что кэш есть
    print(f"\n3️⃣ Проверка кэша для user_id={test_user_id} (должен быть HIT)...")
    cached = await get_cached_recommendations(
        user_id=test_user_id,
        top_n=10,
        exclude_listened=True
    )
    if cached:
        print("   ✅ Cache HIT (ожидаемо)")
        print(f"   Найдено рекомендаций: {len(cached.get('recommendations', []))}")
    else:
        print("   ❌ Cache MISS (неожиданно)")
    
    # 4. Проверяем другой top_n (должен быть MISS)
    print(f"\n4️⃣ Проверка кэша для user_id={test_user_id}, top_n=20 (должен быть MISS)...")
    cached = await get_cached_recommendations(
        user_id=test_user_id,
        top_n=20,
        exclude_listened=True
    )
    if cached is None:
        print("   ✅ Cache MISS (ожидаемо - другой top_n)")
    else:
        print("   ⚠️ Cache HIT (неожиданно)")
    
    # 5. Инвалидируем кэш
    print(f"\n5️⃣ Инвалидация кэша для user_id={test_user_id}...")
    success = await invalidate_cached_user_recommendations(test_user_id)
    if success:
        print("   ✅ Кэш инвалидирован")
    else:
        print("   ⚠️ Ошибка инвалидации (возможно, кэша не было)")
    
    # 6. Проверяем, что кэша нет после инвалидации
    print(f"\n6️⃣ Проверка кэша после инвалидации (должен быть MISS)...")
    cached = await get_cached_recommendations(
        user_id=test_user_id,
        top_n=10,
        exclude_listened=True
    )
    if cached is None:
        print("   ✅ Cache MISS (ожидаемо после инвалидации)")
    else:
        print("   ❌ Cache HIT (неожиданно - кэш должен быть удален)")


async def check_cache_keys():
    """Проверка ключей кэша"""
    print("\n🔑 Проверка ключей кэша:")
    redis = get_redis_client()
    
    if not await redis.is_connected():
        print("   ❌ Redis не подключен")
        return
    
    pattern = "recommendations:user:*"
    keys = await redis.keys(pattern)
    
    print(f"   Найдено ключей: {len(keys)}")
    
    if keys:
        print("\n   Примеры ключей (первые 5):")
        for key in keys[:5]:
            try:
                ttl = await redis.redis.ttl(key) if redis.redis else -1
                print(f"   - {key} (TTL: {ttl}s)")
            except Exception as e:
                print(f"   - {key} (ошибка получения TTL: {e})")


async def main():
    """Основная функция"""
    print("=" * 60)
    print("Проверка кэширования рекомендаций")
    print("=" * 60)
    
    # Проверка подключения
    is_connected = await check_redis_connection()
    if not is_connected:
        print("\n❌ Redis не подключен. Проверьте настройки подключения.")
        return
    
    # Статистика
    await check_cache_stats()
    
    # Проверка ключей
    await check_cache_keys()
    
    # Тест операций
    await test_cache_operations()
    
    # Финальная статистика
    print("\n" + "=" * 60)
    print("Финальная статистика:")
    await check_cache_stats()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

