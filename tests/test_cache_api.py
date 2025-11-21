#!/usr/bin/env python3
"""
Тестирование кэширования через API
"""

import requests
import json
import sys
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

def print_json(data):
    """Красивый вывод JSON"""
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))

def test_api_endpoint(method, endpoint, description):
    """Тест API эндпоинта"""
    print(f"\n{description}")
    print("=" * len(description))
    
    try:
        url = f"{API_BASE}{endpoint}"
        
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, timeout=30)
        else:
            print(f"❌ Неподдерживаемый метод: {method}")
            return False
        
        if response.status_code == 200:
            print("✅ Запрос успешен")
            data = response.json()
            print_json(data)
            return True
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к API. Убедитесь, что сервер запущен на localhost:8000")
        return False
    except requests.exceptions.Timeout:
        print("❌ Таймаут запроса")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    print("🔍 ДИАГНОСТИКА КЭШИРОВАНИЯ РЕКОМЕНДАЦИЙ")
    print("=" * 50)
    print(f"Время: {datetime.now()}")
    
    # Проверяем доступность API
    print("\n🌐 Проверка доступности API...")
    try:
        response = requests.get(f"{API_BASE.replace('/api/v1', '')}/", timeout=5)
        if response.status_code == 200:
            print("✅ API доступен")
        else:
            print(f"⚠️  API отвечает с кодом {response.status_code}")
    except:
        print("❌ API недоступен. Запустите: make up")
        sys.exit(1)
    
    # Тесты кэширования
    tests = [
        ("GET", "/debug/cache/status", "1️⃣  Статус кэша"),
        ("GET", "/debug/cache/keys", "2️⃣  Ключи кэша"),
        ("POST", "/debug/cache/test", "3️⃣  Тест операций кэширования"),
        ("POST", "/debug/cache/simulate-hitrate", "4️⃣  Симуляция hit rate")
    ]
    
    results = []
    for method, endpoint, description in tests:
        success = test_api_endpoint(method, endpoint, description)
        results.append((description, success))
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📋 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
    else:
        print("⚠️  Обнаружены проблемы с кэшированием")

if __name__ == "__main__":
    main()
