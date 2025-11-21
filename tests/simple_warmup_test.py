#!/usr/bin/env python3
"""
Упрощенный тест прогрева кэша
"""

import urllib.request
import json
import time

API_BASE = "http://localhost:8000/api/v1"

def make_request(method, endpoint, data=None):
    """Простой HTTP запрос"""
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            with urllib.request.urlopen(url, timeout=10) as response:
                return response.status, json.loads(response.read().decode())
        elif method == "POST":
            json_data = json.dumps(data).encode() if data else b'{}'
            req = urllib.request.Request(url, data=json_data, method='POST')
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status, json.loads(response.read().decode())
        elif method == "DELETE":
            req = urllib.request.Request(url, method='DELETE')
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status, json.loads(response.read().decode())
    except Exception as e:
        return None, {"error": str(e)}

def test_warmup_simple():
    print("🔥 ПРОСТОЙ ТЕСТ ПРОГРЕВА КЭША")
    print("=" * 35)
    
    # 1. Проверяем статус кэша
    print("\n1️⃣ Проверка статуса кэша:")
    status, data = make_request("GET", "/debug/cache/status")
    if status == 200:
        print(f"✅ Кэш работает: {data.get('cache_stats', {}).get('status', 'неизвестен')}")
    else:
        print(f"❌ Проблема с кэшем: {data.get('error', 'неизвестна')}")
        return
    
    # 2. Получаем активных пользователей
    print("\n2️⃣ Получение активных пользователей:")
    status, data = make_request("GET", "/debug/cache/warmup/active-users")
    if status == 200:
        users = data.get("active_users", [])
        print(f"✅ Найдено {len(users)} активных пользователей")
        if users:
            print(f"   Примеры: {users[:3]}")
    else:
        print(f"❌ Ошибка: {data.get('error', 'неизвестна')}")
        # Используем тестовых пользователей
        users = [1, 2, 3, 4, 5]
        print(f"⚠️  Используем тестовых пользователей: {users}")
    
    if not users:
        print("❌ Нет пользователей для тестирования")
        return
    
    # 3. Тест одного пользователя
    test_user = users[0]
    print(f"\n3️⃣ Тест пользователя {test_user}:")
    
    # Очищаем кэш для пользователя
    status, data = make_request("DELETE", f"/debug/cache/clear/{test_user}")
    if status == 200:
        print("✅ Кэш пользователя очищен")
    
    # Первый запрос (должен быть MISS)
    print("   Первый запрос (ожидается MISS):")
    start_time = time.time()
    status, data = make_request("POST", "/recommendations", {
        "user_id": test_user,
        "top_n": 10,
        "exclude_listened": True,
        "include_performance_metrics": True
    })
    first_time = (time.time() - start_time) * 1000
    
    if status == 200:
        metrics = data.get("performance_metrics", {})
        cache_hit = metrics.get("cache_hit", False)
        print(f"   {'HIT' if cache_hit else 'MISS'} ({first_time:.1f}ms)")
    else:
        print(f"   ❌ Ошибка: {status}")
        return
    
    # Второй запрос (должен быть HIT)
    print("   Второй запрос (ожидается HIT):")
    start_time = time.time()
    status, data = make_request("POST", "/recommendations", {
        "user_id": test_user,
        "top_n": 10,
        "exclude_listened": True,
        "include_performance_metrics": True
    })
    second_time = (time.time() - start_time) * 1000
    
    if status == 200:
        metrics = data.get("performance_metrics", {})
        cache_hit = metrics.get("cache_hit", False)
        print(f"   {'HIT' if cache_hit else 'MISS'} ({second_time:.1f}ms)")
        
        if cache_hit:
            speedup = first_time / second_time if second_time > 0 else 1
            print(f"   🚀 Ускорение: {speedup:.1f}x")
        else:
            print("   ⚠️  Кэш не сработал")
    else:
        print(f"   ❌ Ошибка: {status}")
    
    # 4. Тест прогрева для пользователя
    print(f"\n4️⃣ Тест прогрева для пользователя {test_user}:")
    
    # Очищаем кэш
    make_request("DELETE", f"/debug/cache/clear/{test_user}")
    
    # Выполняем прогрев
    status, data = make_request("POST", f"/debug/cache/warmup/user/{test_user}")
    if status == 200 and data.get("success"):
        print("✅ Прогрев выполнен")
        
        # Проверяем, что кэш прогрелся
        start_time = time.time()
        status, data = make_request("POST", "/recommendations", {
            "user_id": test_user,
            "top_n": 10,
            "exclude_listened": True,
            "include_performance_metrics": True
        })
        warmup_time = (time.time() - start_time) * 1000
        
        if status == 200:
            metrics = data.get("performance_metrics", {})
            cache_hit = metrics.get("cache_hit", False)
            print(f"   После прогрева: {'HIT' if cache_hit else 'MISS'} ({warmup_time:.1f}ms)")
            
            if cache_hit:
                print("   🎉 Прогрев работает!")
            else:
                print("   ❌ Прогрев не сработал")
        else:
            print(f"   ❌ Ошибка проверки: {status}")
    else:
        print(f"❌ Ошибка прогрева: {data.get('error', 'неизвестна')}")
    
    # 5. Статистика прогрева
    print("\n5️⃣ Статистика прогрева:")
    status, data = make_request("GET", "/debug/cache/warmup/stats")
    if status == 200:
        stats = data.get("stats", {})
        print(f"   Последний запуск: {stats.get('last_run', 'никогда')}")
        print(f"   Прогрето пользователей: {stats.get('users_warmed', 0)}")
        print(f"   Ошибок: {stats.get('errors', 0)}")
    else:
        print(f"❌ Ошибка получения статистики: {data.get('error', 'неизвестна')}")
    
    print("\n✅ ТЕСТ ЗАВЕРШЕН")

if __name__ == "__main__":
    test_warmup_simple()
