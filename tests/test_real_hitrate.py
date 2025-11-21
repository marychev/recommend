#!/usr/bin/env python3
"""
Тест реального hit rate в условиях множественных запросов
"""

import urllib.request
import urllib.parse
import json
import time
import asyncio
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

def make_request(method, endpoint, data=None, timeout=30):
    """Выполнить HTTP запрос"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return response.status, response.read().decode('utf-8')
        elif method.upper() == "POST":
            if data:
                data = json.dumps(data).encode('utf-8')
            else:
                data = b''
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.status, response.read().decode('utf-8')
        else:
            return None, f"Неподдерживаемый метод: {method}"
            
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except urllib.error.URLError as e:
        return None, f"Ошибка подключения: {e.reason}"
    except Exception as e:
        return None, f"Ошибка: {e}"

def test_recommendations_hitrate():
    """Тест hit rate рекомендаций в реальных условиях"""
    print("🎯 ТЕСТ РЕАЛЬНОГО HIT RATE РЕКОМЕНДАЦИЙ")
    print("=" * 50)
    print(f"Время: {datetime.now()}")
    
    # Очищаем кэш
    print("\n🧹 Очистка кэша...")
    status, response = make_request("DELETE", "/debug/cache/clear-all")
    if status == 200:
        print("✅ Кэш очищен")
    else:
        print(f"⚠️  Не удалось очистить кэш: {status}")
    
    # Тестируем разных пользователей
    users = [1, 2, 3, 4, 5]
    total_requests = 0
    cache_hits = 0
    cache_misses = 0
    
    results = []
    
    print(f"\n📊 Тестирование {len(users)} пользователей...")
    
    for user_id in users:
        print(f"\n👤 Пользователь {user_id}:")
        
        # Делаем 3 запроса для каждого пользователя
        for request_num in range(1, 4):
            start_time = time.time()
            
            # Запрос рекомендаций
            request_data = {
                "user_id": user_id,
                "top_n": 10,
                "exclude_listened": True,
                "include_performance_metrics": True
            }
            
            status, response = make_request("POST", "/recommendations", request_data)
            request_time = (time.time() - start_time) * 1000
            
            if status == 200:
                try:
                    data = json.loads(response)
                    metrics = data.get("performance_metrics", {})
                    cache_hit = metrics.get("cache_hit", False)
                    
                    total_requests += 1
                    if cache_hit:
                        cache_hits += 1
                        hit_status = "✅ HIT"
                    else:
                        cache_misses += 1
                        hit_status = "❌ MISS"
                    
                    print(f"   Запрос {request_num}: {hit_status} ({request_time:.1f}ms)")
                    
                    results.append({
                        "user_id": user_id,
                        "request_num": request_num,
                        "cache_hit": cache_hit,
                        "time_ms": request_time,
                        "status": "success"
                    })
                    
                except json.JSONDecodeError:
                    print(f"   Запрос {request_num}: ❌ Ошибка JSON")
                    total_requests += 1
                    cache_misses += 1
            else:
                print(f"   Запрос {request_num}: ❌ Ошибка {status}")
                total_requests += 1
                cache_misses += 1
            
            # Небольшая пауза между запросами
            time.sleep(0.1)
        
        # Создаем событие для пользователя (PLAY - не должно инвалидировать)
        event_data = {
            "user_id": user_id,
            "track_id": user_id,  # Используем user_id как track_id для простоты
            "action_type": "play",
            "listen_duration_seconds": 30
        }
        
        status, response = make_request("POST", "/events", event_data)
        if status == 201:
            print(f"   📝 Событие PLAY создано")
        else:
            print(f"   ⚠️  Не удалось создать событие: {status}")
        
        time.sleep(0.2)  # Ждем обработки события
    
    # Подсчитываем статистику
    hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
    
    print("\n" + "=" * 50)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 50)
    
    print(f"Всего запросов: {total_requests}")
    print(f"Попадания в кэш: {cache_hits}")
    print(f"Промахи кэша: {cache_misses}")
    print(f"Hit Rate: {hit_rate:.1f}%")
    
    # Анализ по пользователям
    print(f"\n📋 Детали по пользователям:")
    for user_id in users:
        user_results = [r for r in results if r["user_id"] == user_id]
        user_hits = sum(1 for r in user_results if r["cache_hit"])
        user_total = len(user_results)
        user_hit_rate = (user_hits / user_total * 100) if user_total > 0 else 0
        
        print(f"   Пользователь {user_id}: {user_hits}/{user_total} ({user_hit_rate:.0f}%)")
    
    # Анализ времени ответа
    hit_times = [r["time_ms"] for r in results if r["cache_hit"]]
    miss_times = [r["time_ms"] for r in results if not r["cache_hit"]]
    
    if hit_times:
        avg_hit_time = sum(hit_times) / len(hit_times)
        print(f"\n⚡ Среднее время из кэша: {avg_hit_time:.1f}ms")
    
    if miss_times:
        avg_miss_time = sum(miss_times) / len(miss_times)
        print(f"🐌 Среднее время без кэша: {avg_miss_time:.1f}ms")
        
        if hit_times:
            speedup = avg_miss_time / avg_hit_time
            print(f"🚀 Ускорение: {speedup:.1f}x")
    
    # Оценка результата
    print(f"\n🎯 ОЦЕНКА РЕЗУЛЬТАТА:")
    if hit_rate >= 60:
        print("🎉 Отличный результат! Селективная инвалидация работает.")
    elif hit_rate >= 40:
        print("✅ Хороший результат! Есть улучшения.")
    elif hit_rate >= 20:
        print("⚠️  Средний результат. Можно улучшить.")
    elif hit_rate >= 5:
        print("❌ Низкий hit rate. Нужны дополнительные оптимизации.")
    else:
        print("💥 Критически низкий hit rate. Проверьте настройки кэша.")
    
    return hit_rate

if __name__ == "__main__":
    test_recommendations_hitrate()
