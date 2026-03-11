#!/usr/bin/env python3
"""
Простая проверка здоровья API перед тестированием прогрева
"""

import urllib.request
import json
import time

API_BASE = "http://localhost:8000"

def check_endpoint(method, endpoint, description):
    """Проверить доступность эндпоинта"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method == "GET":
            with urllib.request.urlopen(url, timeout=5) as response:
                status = response.status
                data = response.read().decode('utf-8')
        elif method == "POST":
            req = urllib.request.Request(url, data=b'{}', method='POST')
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=5) as response:
                status = response.status
                data = response.read().decode('utf-8')
        
        print(f"✅ {description}: {status}")
        return True
        
    except urllib.error.HTTPError as e:
        print(f"❌ {description}: HTTP {e.code}")
        return False
    except urllib.error.URLError as e:
        print(f"❌ {description}: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ {description}: {e}")
        return False


def main():
    print("🏥 ПРОВЕРКА ЗДОРОВЬЯ API")
    print("=" * 30)
    
    # Основные эндпоинты
    endpoints = [
        ("GET", "/", "Корневой эндпоинт"),
        ("GET", "/api/v1/health", "Health check"),
        ("GET", "/api/v1/debug/cache/status", "Статус кэша"),
        ("GET", "/api/v1/debug/cache/current-ttl", "Текущий TTL"),
        ("POST", "/api/v1/debug/cache/warmup/auto", "Автопрогрев (может быть ошибка - это нормально)"),
    ]
    
    working = 0
    total = len(endpoints)
    
    for method, endpoint, description in endpoints:
        if check_endpoint(method, endpoint, description):
            working += 1
        time.sleep(0.2)
    
    print(f"\n📊 Результат: {working}/{total} эндпоинтов работают")
    
    if working >= 3:
        print("✅ API в основном работает, можно тестировать")
        return True
    else:
        print("❌ Слишком много проблем с API")
        return False

if __name__ == "__main__":
    main()
