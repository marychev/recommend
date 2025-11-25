#!/usr/bin/env python3
"""
Тесты для Cache Debug API endpoints

Тестирует все эндпоинты из app/routers/cache_debug.py:
- Проверка статуса кэша
- Получение ключей кэша
- Тестирование операций кэша
- Прогрев кэша
- Инвалидация кэша
- Управление TTL

Использование:
- Standalone: python tests/test_cache_api.py
- Pytest: pytest tests/test_cache_api.py (требует установленных зависимостей)
"""

import sys
import urllib.request
import json
import pytest
from datetime import datetime
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

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
        try:
            return e.code, e.read().decode('utf-8')
        except:
            return e.code, str(e)
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

@pytest.mark.skip(reason="Для тестирования k6 вручную")
def test_cache_status_endpoint():
    """Тест статуса кэша"""
    print("📊 Проверка статуса кэша...")
    status, response = make_request("GET", "/debug/cache/status")
    
    if status == 200:
        data = print_json(response)
        redis_connected = data.get("redis_connected", False)
        if redis_connected:
            print("   ✅ Redis подключен")
        else:
            print("   ❌ Redis не подключен")
        return redis_connected
    else:
        print(f"   ❌ Ошибка: {status}")
        if response:
            print(f"   {response[:200]}")
        return False

@pytest.mark.skip(reason="Для тестирования k6 вручную")
def test_cache_operations():
    """Тест операций кэша"""
    print("\n🔧 Тестирование операций кэша...")
    status, response = make_request("POST", "/debug/cache/test")
    
    if status == 200:
        data = print_json(response)
        success = data.get("success", False)
        if success:
            print("   ✅ Все операции кэша работают")
            results = data.get("results", {})
            if "redis_connection" in results:
                print(f"   Redis подключение: {'✅' if results['redis_connection'] else '❌'}")
            if "basic_redis_ops" in results:
                print(f"   Базовые операции: {'✅' if results['basic_redis_ops'] else '❌'}")
        else:
            print("   ❌ Ошибки при тестировании операций")
            if "error" in data:
                print(f"   Ошибка: {data['error']}")
        return success
    else:
        print(f"   ❌ Ошибка запроса: {status}")
        if response:
            print(f"   {response[:200]}")
        return False

@pytest.mark.skip(reason="Для тестирования k6 вручную")
def test_cache_keys():
    """Тест получения ключей кэша"""
    print("\n🔑 Получение ключей кэша...")
    status, response = make_request("GET", "/debug/cache/keys")
    
    if status == 200:
        data = print_json(response)
        total_keys = data.get("total_keys", 0)
        print(f"   Найдено ключей: {total_keys}")
        return True
    else:
        print(f"   ❌ Ошибка: {status}")
        if response:
            print(f"   {response[:200]}")
        return False

@pytest.mark.skip(reason="Для тестирования k6 вручную")
def test_cache_ttl():
    """Тест TTL кэша"""
    print("\n⏱️  Проверка TTL кэша...")
    status, response = make_request("GET", "/debug/cache/current-ttl")
    
    if status == 200:
        data = print_json(response)
        ttl_formatted = data.get("ttl_formatted", "неизвестен")
        print(f"   Текущий TTL: {ttl_formatted}")
        return True
    else:
        print(f"   ❌ Ошибка: {status}")
        if response:
            print(f"   {response[:200]}")
        return False

@pytest.mark.skip(reason="Для тестирования k6 вручную")
def test_cache_warmup():
    """Тест прогрева кэша"""
    print("\n🔥 Тест прогрева кэша...")
    
    # Получаем активных пользователей
    status, response = make_request("GET", "/debug/cache/warmup/active-users")
    if status == 200:
        data = print_json(response)
        active_users = data.get("active_users", [])
        count = data.get("count", 0)
        print(f"   Найдено активных пользователей: {count}")
        if count > 0:
            print(f"   Примеры: {active_users[:5]}")
        return True
    else:
        print(f"   ❌ Ошибка получения активных пользователей: {status}")
        return False

@pytest.mark.skip(reason="Для тестирования k6 вручную")
def test_cache_invalidation():
    """Тест инвалидации кэша"""
    print("\n🧹 Тест инвалидации кэша...")
    
    # Тестируем очистку кэша для несуществующего пользователя
    test_user_id = 999999
    status, response = make_request("DELETE", f"/debug/cache/clear/{test_user_id}")
    
    if status == 200:
        print("   ✅ Очистка кэша пользователя работает")
        return True
    else:
        print(f"   ⚠️  Ошибка очистки: {status}")
        return False


def main():
    """Основная функция для standalone режима"""
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ CACHE API ENDPOINTS")
    print("=" * 60)
    print(f"Время: {datetime.now()}")
    print(f"API Base: {API_BASE}\n")
    
    results = {}
    
    # Тест статуса
    results['status'] = test_cache_status_endpoint()
    
    # Тест операций
    results['operations'] = test_cache_operations()
    
    # Тест ключей
    results['keys'] = test_cache_keys()
    
    # Тест TTL
    results['ttl'] = test_cache_ttl()
    
    # Тест прогрева
    results['warmup'] = test_cache_warmup()
    
    # Тест инвалидации
    results['invalidation'] = test_cache_invalidation()
    
    # Итоги
    print("\n" + "=" * 60)
    print("📋 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"   {name}: {status}")
    
    print(f"\n   Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        return 0
    else:
        print("\n⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ")
        print("   Убедитесь, что API сервер запущен (make run)")
        return 1


if __name__ == "__main__":
    sys.exit(main())