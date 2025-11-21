#!/usr/bin/env python3
"""
Простая диагностика кэширования без внешних зависимостей
"""

import urllib.request
import urllib.parse
import json
import sys
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

def make_request(method, endpoint, timeout=10):
    """Выполнить HTTP запрос"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return response.status, response.read().decode('utf-8')
        elif method.upper() == "POST":
            req = urllib.request.Request(url, data=b'', method='POST')
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

def print_json(data_str):
    """Красивый вывод JSON"""
    try:
        data = json.loads(data_str)
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
        return data
    except json.JSONDecodeError:
        print(data_str)
        return None

def test_endpoint(method, endpoint, description):
    """Тест API эндпоинта"""
    print(f"\n{description}")
    print("=" * len(description))
    
    status, response = make_request(method, endpoint)
    
    if status == 200:
        print("✅ Запрос успешен")
        data = print_json(response)
        return True, data
    elif status is None:
        print(f"❌ {response}")
        return False, None
    else:
        print(f"❌ Ошибка {status}")
        print_json(response)
        return False, None

def main():
    print("🔍 ДИАГНОСТИКА КЭШИРОВАНИЯ РЕКОМЕНДАЦИЙ")
    print("=" * 50)
    print(f"Время: {datetime.now()}")
    
    # Проверяем доступность API
    print("\n🌐 Проверка доступности API...")
    status, response = make_request("GET", "/../", timeout=5)
    
    if status == 200:
        print("✅ API доступен")
    elif status is None:
        print("❌ API недоступен. Запустите: make up")
        print(f"Ошибка: {response}")
        sys.exit(1)
    else:
        print(f"⚠️  API отвечает с кодом {status}")
    
    # Тесты кэширования
    tests = [
        ("GET", "/debug/cache/status", "1️⃣  Статус кэша"),
        ("GET", "/debug/cache/keys", "2️⃣  Ключи кэша"),
        ("POST", "/debug/cache/test", "3️⃣  Тест операций кэширования"),
        ("POST", "/debug/cache/simulate-hitrate", "4️⃣  Симуляция hit rate"),
        ("POST", "/debug/cache/test-real-scenario-v2", "5️⃣  Тест реального сценария (v2)")
    ]
    
    results = []
    test_data = {}
    
    for method, endpoint, description in tests:
        success, data = test_endpoint(method, endpoint, description)
        results.append((description, success))
        if data:
            test_data[endpoint] = data
    
    # Анализ результатов
    print("\n" + "=" * 50)
    print("📋 АНАЛИЗ РЕЗУЛЬТАТОВ")
    print("=" * 50)
    
    # Анализ статуса кэша
    if "/debug/cache/status" in test_data:
        status_data = test_data["/debug/cache/status"]
        redis_connected = status_data.get("redis_connected", False)
        cache_stats = status_data.get("cache_stats", {})
        
        print(f"\n🔴 Redis подключение: {'✅ Да' if redis_connected else '❌ Нет'}")
        print(f"📊 Статус кэша: {cache_stats.get('status', 'неизвестен')}")
        print(f"🗂️  Закэшированных рекомендаций: {cache_stats.get('cached_recommendations', 0)}")
        print(f"⏰ TTL: {cache_stats.get('ttl_seconds', 0)} секунд")
    
    # Анализ ключей кэша
    if "/debug/cache/keys" in test_data:
        keys_data = test_data["/debug/cache/keys"]
        total_keys = keys_data.get("total_keys", 0)
        print(f"\n🔑 Всего ключей кэша: {total_keys}")
        
        if total_keys > 0:
            print("📋 Примеры ключей:")
            for key_info in keys_data.get("keys_sample", [])[:3]:
                print(f"   • {key_info.get('key', 'N/A')} (TTL: {key_info.get('ttl_seconds', 0)}s)")
    
    # Анализ тестов операций
    if "/debug/cache/test" in test_data:
        test_results = test_data["/debug/cache/test"].get("results", {})
        
        print(f"\n🧪 Тест операций кэширования:")
        print(f"   Redis подключение: {'✅' if test_results.get('redis_connection') else '❌'}")
        print(f"   Базовые операции Redis: {'✅' if test_results.get('basic_redis_ops') else '❌'}")
        
        cache_save = test_results.get('cache_save', {})
        cache_get = test_results.get('cache_get', {})
        
        print(f"   Сохранение в кэш: {'✅' if cache_save.get('success') else '❌'} ({cache_save.get('time_ms', 0):.1f}ms)")
        print(f"   Получение из кэша: {'✅' if cache_get.get('success') else '❌'} ({cache_get.get('time_ms', 0):.1f}ms)")
    
    # Анализ симуляции hit rate
    if "/debug/cache/simulate-hitrate" in test_data:
        sim_results = test_data["/debug/cache/simulate-hitrate"].get("results", {})
        
        hit_rate = sim_results.get("hit_rate", 0)
        hits = sim_results.get("hits", 0)
        misses = sim_results.get("misses", 0)
        avg_cache_time = sim_results.get("avg_cache_time", 0)
        avg_miss_time = sim_results.get("avg_miss_time", 0)
        
        print(f"\n🎯 Симуляция hit rate:")
        print(f"   Hit Rate: {hit_rate:.1f}%")
        print(f"   Попадания: {hits}, Промахи: {misses}")
        print(f"   Время из кэша: {avg_cache_time:.1f}ms")
        print(f"   Время при промахе: {avg_miss_time:.1f}ms")
        
        if hit_rate > 80:
            print("   🎉 Отличный hit rate!")
        elif hit_rate > 50:
            print("   ✅ Хороший hit rate")
        elif hit_rate > 10:
            print("   ⚠️  Низкий hit rate")
        else:
            print("   ❌ Критически низкий hit rate")
    
    # Анализ реального сценария
    if "/debug/cache/test-real-scenario-v2" in test_data:
        scenario_results = test_data["/debug/cache/test-real-scenario-v2"].get("results", {})
        
        hit_rate = scenario_results.get("final_hit_rate", 0)
        hits = scenario_results.get("cache_hits", 0)
        misses = scenario_results.get("cache_misses", 0)
        steps = scenario_results.get("scenario_steps", [])
        
        print(f"\n🎬 Тест реального сценария:")
        print(f"   Hit Rate: {hit_rate:.1f}%")
        print(f"   Попадания: {hits}, Промахи: {misses}")
        
        print(f"   📋 Детали по шагам:")
        for step in steps:
            hit_status = "✅ HIT" if step.get("cache_hit") else "❌ MISS"
            expected = step.get("expected", "")
            actual = "HIT" if step.get("cache_hit") else "MISS"
            correct = "✅" if expected == actual else "❌"
            print(f"      {step.get('step')}. {step.get('action')}: {hit_status} ({step.get('time_ms', 0):.1f}ms) {correct}")
        
        # Анализ корректности
        correctness = scenario_results.get("correctness_analysis", {})
        correctness_pct = scenario_results.get("correctness_percentage", 0)
        
        print(f"   📊 Корректность поведения: {correctness_pct:.0f}%")
        
        if correctness_pct == 100:
            print("   🎉 Селективная инвалидация работает идеально!")
        elif correctness_pct >= 80:
            print("   ✅ Селективная инвалидация работает хорошо")
        elif correctness_pct >= 60:
            print("   ⚠️  Селективная инвалидация работает частично")
        else:
            print("   ❌ Селективная инвалидация не работает правильно")
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("🏁 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    print(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    # Рекомендации
    print("\n🔧 РЕКОМЕНДАЦИИ:")
    
    if passed == total:
        # Все тесты прошли - анализируем hit rate
        if "/debug/cache/simulate-hitrate" in test_data:
            hit_rate = test_data["/debug/cache/simulate-hitrate"].get("results", {}).get("hit_rate", 0)
            if hit_rate > 80:
                print("✅ Кэширование работает отлично!")
                print("   Проблема может быть в агрессивной инвалидации в реальных условиях.")
            elif hit_rate < 10:
                print("❌ Кэш не работает даже в тестах!")
                print("   Проверьте логику сохранения/получения кэша.")
            else:
                print("⚠️  Кэш работает частично.")
                print("   Возможны проблемы с ключами или TTL.")
        else:
            print("✅ Базовые функции кэша работают.")
    else:
        print("❌ Обнаружены критические проблемы:")
        if not test_data.get("/debug/cache/status", {}).get("redis_connected", True):
            print("   1. Redis не подключен - запустите: docker-compose restart redis")
        print("   2. Проверьте логи: make logs-api")
        print("   3. Проверьте статус: make ps")

if __name__ == "__main__":
    main()
