#!/usr/bin/env python3
"""
Простой тест TTL оптимизации
"""

import urllib.request
import json
import time

API_BASE = "http://localhost:8000/api/v1"

def make_request(method, endpoint):
    """Простой HTTP запрос"""
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            with urllib.request.urlopen(url) as response:
                return json.loads(response.read().decode())
        elif method == "POST":
            req = urllib.request.Request(url, data=b'', method='POST')
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}

def test_ttl():
    print("🕐 ПРОСТОЙ ТЕСТ TTL ОПТИМИЗАЦИИ")
    print("=" * 40)
    
    # 1. Текущий TTL
    print("\n1️⃣ Текущий TTL:")
    result = make_request("GET", "/debug/cache/current-ttl")
    if "error" not in result:
        print(f"   TTL: {result.get('ttl_formatted', 'неизвестен')}")
    else:
        print(f"   Ошибка: {result['error']}")
    
    # 2. Тест с TTL 1 час (baseline)
    print("\n2️⃣ Тест с TTL 1 час:")
    make_request("POST", "/debug/cache/set-ttl/1")
    time.sleep(0.5)
    result = make_request("POST", "/debug/cache/test-real-scenario-v2")
    if "error" not in result and result.get("success"):
        hit_rate = result["results"]["final_hit_rate"]
        print(f"   Hit Rate: {hit_rate}%")
    else:
        print(f"   Ошибка: {result.get('error', 'неизвестна')}")
    
    # 3. Тест с TTL 2 часа
    print("\n3️⃣ Тест с TTL 2 часа:")
    make_request("POST", "/debug/cache/set-ttl/2")
    time.sleep(0.5)
    result = make_request("POST", "/debug/cache/test-real-scenario-v2")
    if "error" not in result and result.get("success"):
        hit_rate = result["results"]["final_hit_rate"]
        print(f"   Hit Rate: {hit_rate}%")
    else:
        print(f"   Ошибка: {result.get('error', 'неизвестна')}")
    
    # 4. Тест с TTL 4 часа
    print("\n4️⃣ Тест с TTL 4 часа:")
    make_request("POST", "/debug/cache/set-ttl/4")
    time.sleep(0.5)
    result = make_request("POST", "/debug/cache/test-real-scenario-v2")
    if "error" not in result and result.get("success"):
        hit_rate = result["results"]["final_hit_rate"]
        correctness = result["results"]["correctness_percentage"]
        print(f"   Hit Rate: {hit_rate}%")
        print(f"   Корректность: {correctness}%")
        
        if hit_rate >= 70:
            print("   🎉 Отличный результат!")
        elif hit_rate >= 60:
            print("   ✅ Хороший результат!")
        else:
            print("   ⚠️ Требуются дополнительные оптимизации")
    else:
        print(f"   Ошибка: {result.get('error', 'неизвестна')}")
    
    print("\n✅ ТЕСТ ЗАВЕРШЕН")
    print("=" * 40)

if __name__ == "__main__":
    test_ttl()
