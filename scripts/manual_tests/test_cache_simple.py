#!/usr/bin/env python3
"""
Простой тест кэширования

Базовые проверки работы кэша:
- Статус Redis
- Базовые операции
- Проверка ключей
"""

import urllib.request
import json
import pytest
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"


def make_request(method, endpoint, data=None, timeout=30):
    """Выполнить HTTP запрос"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return response.status, json.loads(response.read().decode('utf-8'))
        elif method.upper() == "POST":
            if data:
                json_data = json.dumps(data).encode('utf-8')
            else:
                json_data = b''
            req = urllib.request.Request(url, data=json_data, method='POST')
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.status, json.loads(response.read().decode('utf-8'))
        elif method.upper() == "DELETE":
            req = urllib.request.Request(url, method='DELETE')
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.status, json.loads(response.read().decode('utf-8'))
        else:
            return None, {"error": f"Неподдерживаемый метод: {method}"}
            
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode('utf-8'))
        except:
            return e.code, {"error": str(e)}
    except urllib.error.URLError as e:
        return None, {"error": f"Ошибка подключения: {e.reason}"}
    except Exception as e:
        return None, {"error": f"Ошибка: {e}"}

@pytest.mark.skip(reason="Для тестирования k6 вручную")
def test_cache_simple():
    """Простой тест кэша"""
    print("🧪 ПРОСТОЙ ТЕСТ КЭША")
    print("=" * 50)
    print(f"Время: {datetime.now()}")
    print(f"API: {API_BASE}\n")
    
    results = {}
    
    # 1. Проверка статуса
    print("1️⃣ Проверка статуса кэша...")
    status, data = make_request("GET", "/debug/cache/status")
    
    if status == 200:
        redis_connected = data.get("redis_connected", False)
        if redis_connected:
            print("   ✅ Redis подключен")
            cache_stats = data.get("cache_stats", {})
            cached_count = cache_stats.get("cached_recommendations", 0)
            print(f"   📊 Закэшированных рекомендаций: {cached_count}")
            results['status'] = True
        else:
            print("   ❌ Redis не подключен")
            results['status'] = False
    else:
        print(f"   ❌ Ошибка запроса: {status}")
        if "error" in data:
            print(f"   {data['error']}")
        results['status'] = False
    
    # 2. Базовые операции
    print("\n2️⃣ Тест базовых операций...")
    status, data = make_request("POST", "/debug/cache/test")
    
    if status == 200 and data.get("success"):
        print("   ✅ Базовые операции работают")
        results_data = data.get("results", {})
        
        if results_data.get("redis_connection"):
            print("      ✅ Подключение Redis")
        else:
            print("      ❌ Подключение Redis не работает")
        
        if results_data.get("basic_redis_ops"):
            print("      ✅ Базовые операции Redis")
        else:
            print("      ❌ Базовые операции Redis не работают")
        
        cache_save = results_data.get("cache_save", {})
        if cache_save.get("success"):
            print(f"      ✅ Сохранение в кэш ({cache_save.get('time_ms', 0):.1f}ms)")
        
        cache_get = results_data.get("cache_get", {})
        if cache_get.get("success"):
            print(f"      ✅ Получение из кэша ({cache_get.get('time_ms', 0):.1f}ms)")
        
        results['operations'] = True
    else:
        print("   ❌ Ошибки при тестировании операций")
        if "error" in data:
            print(f"   {data['error']}")
        results['operations'] = False
    
    # 3. Ключи кэша
    print("\n3️⃣ Проверка ключей кэша...")
    status, data = make_request("GET", "/debug/cache/keys")
    
    if status == 200:
        total_keys = data.get("total_keys", 0)
        print(f"   📋 Найдено ключей: {total_keys}")
        
        if total_keys > 0:
            keys_sample = data.get("keys_sample", [])
            print(f"   🔑 Примеры ключей:")
            for i, key_info in enumerate(keys_sample[:3], 1):
                key = key_info.get("key", "")
                ttl = key_info.get("ttl_seconds", -1)
                print(f"      {i}. {key}")
                if ttl > 0:
                    print(f"         TTL: {ttl}s")
        
        results['keys'] = True
    else:
        print(f"   ❌ Ошибка получения ключей: {status}")
        results['keys'] = False
    
    # 4. Текущий TTL
    print("\n4️⃣ Текущий TTL кэша...")
    status, data = make_request("GET", "/debug/cache/current-ttl")
    
    if status == 200:
        ttl_formatted = data.get("ttl_formatted", "неизвестен")
        ttl_hours = data.get("ttl_hours", 0)
        print(f"   ⏱️  TTL: {ttl_formatted}")
        results['ttl'] = True
    else:
        print(f"   ❌ Ошибка получения TTL: {status}")
        results['ttl'] = False
    
    # Итоги
    print("\n" + "=" * 50)
    print("📋 ИТОГИ")
    print("=" * 50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status_icon = "✅" if result else "❌"
        print(f"   {status_icon} {name}")
    
    print(f"\n   Результат: {passed}/{total} проверок пройдено")
    
    if passed == total:
        print("\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("   Кэш работает корректно.")
    elif results.get('status') and results.get('operations'):
        print("\n⚠️  ОБНАРУЖЕНЫ НЕЗНАЧИТЕЛЬНЫЕ ПРОБЛЕМЫ")
        print("   Основная функциональность кэша работает.")
    else:
        print("\n❌ ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
        print("   Проверьте подключение к Redis и настройки кэша.")
        print("   Запустите: docker-compose up -d redis")
    
    print("=" * 50)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(test_cache_simple())

