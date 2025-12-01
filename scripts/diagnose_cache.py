#!/usr/bin/env python3
"""
Диагностический скрипт для анализа проблем с кэшированием рекомендаций
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from app.services.cache_redis_client import get_redis_client, connect_redis
from app.services.cache import (
    get_cached_recommendations,
    set_cached_recommendations,
    get_cache_stats,
    get_cache_key_recommendations
)
from app.config import settings


async def test_redis_connection():
    """Тест подключения к Redis"""
    print("🔴 Тестирование подключения к Redis...")
    
    try:
        redis_connected = await connect_redis()
        if redis_connected:
            print("   ✅ Redis подключен успешно")
            return True
        else:
            print("   ❌ Не удалось подключиться к Redis")
            return False
    except Exception as e:
        print(f"   ❌ Ошибка подключения к Redis: {e}")
        return False


async def test_basic_redis_operations():
    """Тест базовых операций Redis"""
    print("\n🔧 Тестирование базовых операций Redis...")
    
    redis = get_redis_client()
    
    try:
        # Тест записи
        test_key = "test:cache:diagnosis"
        test_value = "test_value_123"
        
        await redis.set(test_key, test_value, ex=60)
        print("   ✅ Запись в Redis работает")
        
        # Тест чтения
        retrieved = await redis.get(test_key)
        if retrieved == test_value:
            print("   ✅ Чтение из Redis работает")
        else:
            print(f"   ❌ Проблема с чтением: ожидали '{test_value}', получили '{retrieved}'")
            return False
        
        # Тест удаления
        await redis.delete(test_key)
        deleted_check = await redis.get(test_key)
        if deleted_check is None:
            print("   ✅ Удаление из Redis работает")
        else:
            print("   ❌ Проблема с удалением из Redis")
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании Redis операций: {e}")
        return False


async def analyze_existing_cache():
    """Анализ существующих ключей кэша"""
    print("\n📊 Анализ существующего кэша...")
    
    redis = get_redis_client()
    
    try:
        # Получаем все ключи рекомендаций
        pattern = "recommendations:user:*"
        keys = await redis.keys(pattern)
        
        print(f"   📋 Найдено ключей кэша: {len(keys)}")
        
        if keys:
            print("   🔑 Примеры ключей:")
            for i, key in enumerate(keys[:5]):  # Показываем первые 5
                ttl = await redis.ttl(key)
                size = len(await redis.get(key) or "")
                print(f"      {i+1}. {key}")
                print(f"         TTL: {ttl}s, Размер: {size} байт")
        else:
            print("   ⚠️  Ключи кэша не найдены - возможно кэш пуст")
            
        return len(keys)
        
    except Exception as e:
        print(f"   ❌ Ошибка при анализе кэша: {e}")
        return 0


async def test_cache_functions():
    """Тест функций кэширования рекомендаций"""
    print("\n🧪 Тестирование функций кэширования...")
    
    # Тестовые данные
    test_user_id = 999999
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
    
    try:
        # Тест сохранения в кэш
        print("   💾 Тестирование сохранения в кэш...")
        save_result = await set_cached_recommendations(
            user_id=test_user_id,
            top_n=10,
            exclude_listened=True,
            recommendations=test_recommendations,
            ttl=300  # 5 минут для теста
        )
        
        if save_result:
            print("   ✅ Сохранение в кэш работает")
        else:
            print("   ❌ Проблема с сохранением в кэш")
            return False
        
        # Небольшая пауза
        await asyncio.sleep(0.1)
        
        # Тест получения из кэша
        print("   📥 Тестирование получения из кэша...")
        cached_data = await get_cached_recommendations(
            user_id=test_user_id,
            top_n=10,
            exclude_listened=True
        )
        
        if cached_data:
            print("   ✅ Получение из кэша работает")
            print(f"   📋 Получено рекомендаций: {len(cached_data.get('recommendations', []))}")
        else:
            print("   ❌ Проблема с получением из кэша")
            return False
        
        # Проверяем ключ кэша
        cache_key = get_cache_key_recommendations(test_user_id, 10, True)
        print(f"   🔑 Ключ кэша: {cache_key}")
        
        # Очищаем тестовые данные
        redis = get_redis_client()
        await redis.delete(cache_key)
        print("   🧹 Тестовые данные очищены")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании функций кэша: {e}")
        return False


async def simulate_recommendation_request():
    """Симуляция запроса рекомендаций для проверки кэширования"""
    print("\n🎯 Симуляция запроса рекомендаций...")
    
    test_user_id = 1  # Используем существующего пользователя
    
    try:
        # Первый запрос - должен быть cache miss
        print("   📤 Первый запрос (ожидается cache miss)...")
        start_time = time.time()
        
        cached_first = await get_cached_recommendations(
            user_id=test_user_id,
            top_n=10,
            exclude_listened=True
        )
        
        first_time = (time.time() - start_time) * 1000
        
        if cached_first:
            print(f"   ⚠️  Неожиданно найден кэш (время: {first_time:.2f}ms)")
        else:
            print(f"   ✅ Cache miss как ожидалось (время: {first_time:.2f}ms)")
        
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
        
        # Сохраняем в кэш
        print("   💾 Сохранение рекомендаций в кэш...")
        save_result = await set_cached_recommendations(
            user_id=test_user_id,
            top_n=10,
            exclude_listened=True,
            recommendations=test_recommendations
        )
        
        if not save_result:
            print("   ❌ Не удалось сохранить в кэш")
            return False
        
        # Второй запрос - должен быть cache hit
        print("   📥 Второй запрос (ожидается cache hit)...")
        start_time = time.time()
        
        cached_second = await get_cached_recommendations(
            user_id=test_user_id,
            top_n=10,
            exclude_listened=True
        )
        
        second_time = (time.time() - start_time) * 1000
        
        if cached_second:
            print(f"   ✅ Cache hit успешен! (время: {second_time:.2f}ms)")
            print(f"   📊 Ускорение: {first_time/second_time:.1f}x")
            return True
        else:
            print(f"   ❌ Cache hit не сработал (время: {second_time:.2f}ms)")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка при симуляции запроса: {e}")
        return False


async def get_cache_statistics():
    """Получение статистики кэша"""
    print("\n📈 Статистика кэша...")
    
    try:
        stats = await get_cache_stats()
        print("   📊 Текущая статистика:")
        for key, value in stats.items():
            print(f"      {key}: {value}")
        
        return stats
        
    except Exception as e:
        print(f"   ❌ Ошибка при получении статистики: {e}")
        return {}


async def main():
    """Основная функция диагностики"""
    print("=" * 60)
    print("🔍 ДИАГНОСТИКА КЭШИРОВАНИЯ РЕКОМЕНДАЦИЙ")
    print("=" * 60)
    
    # Проверяем конфигурацию
    print(f"\n⚙️  Конфигурация Redis:")
    print(f"   Host: {settings.redis_host}")
    print(f"   Port: {settings.redis_port}")
    print(f"   DB: {settings.redis_db}")
    
    results = {}
    
    # 1. Тест подключения
    results['redis_connection'] = await test_redis_connection()
    
    if not results['redis_connection']:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Redis недоступен!")
        print("   Запустите: docker-compose up -d redis")
        return
    
    # 2. Тест базовых операций
    results['basic_operations'] = await test_basic_redis_operations()
    
    # 3. Анализ существующего кэша
    results['existing_cache_keys'] = await analyze_existing_cache()
    
    # 4. Тест функций кэширования
    results['cache_functions'] = await test_cache_functions()
    
    # 5. Симуляция запроса
    results['simulation'] = await simulate_recommendation_request()
    
    # 6. Статистика
    results['stats'] = await get_cache_statistics()
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ ОТЧЕТ ДИАГНОСТИКИ")
    print("=" * 60)
    
    all_passed = True
    
    checks = [
        ("Redis подключение", results['redis_connection']),
        ("Базовые операции Redis", results['basic_operations']),
        ("Функции кэширования", results['cache_functions']),
        ("Симуляция запросов", results['simulation'])
    ]
    
    for check_name, passed in checks:
        status = "✅ ПРОЙДЕН" if passed else "❌ ПРОВАЛЕН"
        print(f"   {check_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\n   Существующих ключей кэша: {results['existing_cache_keys']}")
    
    if all_passed:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("   Кэширование должно работать корректно.")
        print("   Если hit rate все еще 0%, проблема может быть в:")
        print("   - Слишком частой инвалидации кэша")
        print("   - Различных параметрах запросов")
        print("   - Логике тестирования производительности")
    else:
        print("\n⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        print("   Необходимо исправить найденные ошибки.")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
