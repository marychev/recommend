#!/usr/bin/env python3
"""
Тест эффективности предварительного прогрева кэша
"""

import urllib.request
import json
import time
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
                json_data = json.dumps(data).encode('utf-8')
            else:
                json_data = b''
            req = urllib.request.Request(url, data=json_data, method='POST')
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.status, response.read().decode('utf-8')
        elif method.upper() == "DELETE":
            req = urllib.request.Request(url, method='DELETE')
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

def print_json(data_str):
    """Красивый вывод JSON"""
    try:
        data = json.loads(data_str)
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
        return data
    except json.JSONDecodeError:
        print(data_str)
        return None

def test_cache_warmup_effectiveness():
    """Тест эффективности прогрева кэша"""
    print("🔥 ТЕСТ ЭФФЕКТИВНОСТИ ПРОГРЕВА КЭША")
    print("=" * 50)
    print(f"Время: {datetime.now()}")
    
    # 1. Получаем список активных пользователей
    print("\n1️⃣ Получение активных пользователей:")
    status, response = make_request("GET", "/debug/cache/warmup/active-users")
    if status == 200:
        data = print_json(response)
        active_users = data.get("active_users", [])
        print(f"Найдено активных пользователей: {len(active_users)}")
    else:
        print(f"❌ Ошибка получения активных пользователей: {status}")
        return
    
    if not active_users:
        print("⚠️  Нет активных пользователей для тестирования")
        return
    
    # Берем первых 5 пользователей для теста
    test_users = active_users[:5]
    print(f"Тестируем с пользователями: {test_users}")
    
    # 2. Очищаем кэш для чистого теста
    print("\n2️⃣ Очистка кэша:")
    status, response = make_request("DELETE", "/debug/cache/clear-all")
    if status == 200:
        print("✅ Кэш очищен")
    else:
        print(f"⚠️  Не удалось очистить кэш: {status}")
    
    # 3. Тест БЕЗ прогрева (baseline)
    print("\n3️⃣ Тест БЕЗ прогрева (baseline):")
    baseline_results = test_users_performance(test_users, "БЕЗ прогрева")
    
    # 4. Очищаем кэш снова
    make_request("DELETE", "/debug/cache/clear-all")
    
    # 5. Выполняем прогрев кэша
    print("\n4️⃣ Выполнение прогрева кэша:")
    status, response = make_request("POST", "/debug/cache/warmup/auto")
    if status == 200:
        data = print_json(response)
        if data.get("success"):
            warmup_result = data.get("result", {})
            print(f"✅ Прогрев выполнен для {warmup_result.get('successful_warmups', 0)} пользователей")
            print(f"   Время прогрева: {warmup_result.get('total_time_seconds', 0):.1f}с")
        else:
            print(f"❌ Ошибка прогрева: {data.get('result', {}).get('error', 'неизвестна')}")
            return
    else:
        print(f"❌ Ошибка запуска прогрева: {status}")
        return
    
    # Ждем завершения прогрева
    time.sleep(2)
    
    # 6. Тест С прогревом
    print("\n5️⃣ Тест С прогревом:")
    warmup_results = test_users_performance(test_users, "С прогревом")
    
    # 7. Сравнение результатов
    print("\n" + "=" * 50)
    print("📊 СРАВНЕНИЕ РЕЗУЛЬТАТОВ")
    print("=" * 50)
    
    print(f"БЕЗ прогрева:")
    print(f"   Hit Rate: {baseline_results['hit_rate']:.1f}%")
    print(f"   Среднее время: {baseline_results['avg_time']:.1f}ms")
    print(f"   Попадания: {baseline_results['hits']}/{baseline_results['total']}")
    
    print(f"\nС прогревом:")
    print(f"   Hit Rate: {warmup_results['hit_rate']:.1f}%")
    print(f"   Среднее время: {warmup_results['avg_time']:.1f}ms")
    print(f"   Попадания: {warmup_results['hits']}/{warmup_results['total']}")
    
    # Вычисляем улучшения
    hit_rate_improvement = warmup_results['hit_rate'] - baseline_results['hit_rate']
    time_improvement = baseline_results['avg_time'] / warmup_results['avg_time'] if warmup_results['avg_time'] > 0 else 1
    
    print(f"\n🎯 УЛУЧШЕНИЯ:")
    print(f"   Hit Rate: +{hit_rate_improvement:.1f}% (с {baseline_results['hit_rate']:.1f}% до {warmup_results['hit_rate']:.1f}%)")
    print(f"   Ускорение: {time_improvement:.1f}x")
    
    if hit_rate_improvement >= 10:
        print("   🎉 Отличное улучшение!")
    elif hit_rate_improvement >= 5:
        print("   ✅ Хорошее улучшение!")
    elif hit_rate_improvement > 0:
        print("   ⚠️  Небольшое улучшение")
    else:
        print("   ❌ Прогрев не дал улучшений")
    
    return {
        "baseline": baseline_results,
        "warmup": warmup_results,
        "improvement": {
            "hit_rate": hit_rate_improvement,
            "speedup": time_improvement
        }
    }

def test_users_performance(user_ids, test_name):
    """Тест производительности для списка пользователей"""
    print(f"   Тестирование производительности ({test_name}):")
    
    total_requests = 0
    cache_hits = 0
    total_time = 0
    
    for user_id in user_ids:
        # Делаем 2 запроса для каждого пользователя
        for request_num in range(1, 3):
            request_data = {
                "user_id": user_id,
                "top_n": 10,
                "exclude_listened": True,
                "include_performance_metrics": True
            }
            
            start_time = time.time()
            status, response = make_request("POST", "/recommendations", request_data)
            request_time = (time.time() - start_time) * 1000
            
            total_requests += 1
            total_time += request_time
            
            if status == 200:
                try:
                    data = json.loads(response)
                    metrics = data.get("performance_metrics", {})
                    cache_hit = metrics.get("cache_hit", False)
                    
                    if cache_hit:
                        cache_hits += 1
                        hit_status = "HIT"
                    else:
                        hit_status = "MISS"
                    
                    print(f"      Пользователь {user_id}, запрос {request_num}: {hit_status} ({request_time:.1f}ms)")
                    
                except json.JSONDecodeError:
                    print(f"      Пользователь {user_id}, запрос {request_num}: Ошибка JSON")
            else:
                print(f"      Пользователь {user_id}, запрос {request_num}: Ошибка {status}")
            
            # Небольшая пауза между запросами
            time.sleep(0.1)
    
    hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
    avg_time = total_time / total_requests if total_requests > 0 else 0
    
    return {
        "hit_rate": hit_rate,
        "avg_time": avg_time,
        "hits": cache_hits,
        "total": total_requests
    }

def test_warmup_stats():
    """Тест статистики прогрева"""
    print("\n📈 СТАТИСТИКА ПРОГРЕВА:")
    status, response = make_request("GET", "/debug/cache/warmup/stats")
    if status == 200:
        data = print_json(response)
    else:
        print(f"❌ Ошибка получения статистики: {status}")

if __name__ == "__main__":
    print("🚀 Запуск тестирования прогрева кэша...")
    
    # Основной тест эффективности
    results = test_cache_warmup_effectiveness()
    
    # Статистика прогрева
    test_warmup_stats()
    
    print("\n" + "=" * 50)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 50)
