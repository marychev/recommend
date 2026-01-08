#!/usr/bin/env python3
"""
Скрипт для измерения лага между созданием записи в k6 и вставкой в ClickHouse

Измеряет время от момента отправки POST запроса до фактической вставки записи в БД.
"""
import asyncio
import aiohttp
import time
import sys
from datetime import datetime
from typing import List, Dict, Optional
import json

# Конфигурация
API_URL = "http://localhost:8000"
CLICKHOUSE_URL = "http://localhost:8123"
DATABASE = "music_recommend"

# Количество запросов для теста
NUM_REQUESTS = 50
CHECK_INTERVAL = 0.5  # Интервал проверки в секундах
MAX_WAIT_TIME = 60  # Максимальное время ожидания записи (учитывает батчинг: 5 сек интервал + время обработки)


class LagMeasurement:
    """Класс для измерения лага вставки"""
    
    def __init__(self):
        self.results: List[Dict] = []
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def create_user(self, test_id: int) -> Optional[Dict]:
        """Создает пользователя через API и возвращает данные для проверки"""
        username = f"lag_test_user_{test_id}_{int(time.time() * 1000)}"
        payload = {
            "username": username,
            "email": f"{username}@test.com",
            "age": 25,
            "country": "US"
        }
        
        request_time = time.time()
        request_timestamp = datetime.fromtimestamp(request_time)
        
        try:
            async with self.session.post(
                f"{API_URL}/api/v1/users",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    user_id = data.get('user_id')
                    response_time = time.time()
                    
                    return {
                        'test_id': test_id,
                        'user_id': user_id,
                        'username': username,
                        'request_time': request_time,
                        'request_timestamp': request_timestamp.isoformat(),
                        'response_time': response_time,
                        'api_response_time_ms': (response_time - request_time) * 1000,
                        'status': 'created'
                    }
                else:
                    text = await response.text()
                    print(f"❌ Ошибка создания пользователя {test_id}: {response.status} - {text[:100]}")
                    return None
        except Exception as e:
            print(f"❌ Исключение при создании пользователя {test_id}: {e}")
            return None
    
    async def check_user_in_clickhouse(self, user_id: int, username: str = None) -> Optional[datetime]:
        """Проверяет, когда пользователь был вставлен в ClickHouse"""
        # Используем username для более надежной проверки (так как user_id может быть одинаковым)
        # Экранируем username для безопасности
        username_escaped = username.replace("'", "''") if username else None
        
        if username_escaped:
            # Проверяем по username (более надежно, так как user_id может быть одинаковым)
            query = f"""
            SELECT created_at
            FROM {DATABASE}.users
            WHERE username = '{username_escaped}'
            LIMIT 1
            """
        else:
            query = f"""
            SELECT created_at
            FROM {DATABASE}.users
            WHERE user_id = {user_id}
            LIMIT 1
            """
        
        try:
            # Используем формат JSON для более надежного парсинга
            query_with_format = query.replace('LIMIT 1', 'FORMAT JSONEachRow LIMIT 1')
            
            async with self.session.get(
                f"{CLICKHOUSE_URL}/",
                params={'query': query_with_format},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    text = await response.text()
                    if text.strip():
                        try:
                            # Пробуем парсить JSON
                            lines = text.strip().split('\n')
                            for line in lines:
                                if line.strip():
                                    data = json.loads(line)
                                    created_at_str = data.get('created_at')
                                    if created_at_str:
                                        # Парсим формат ClickHouse DateTime
                                        try:
                                            created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
                                            return created_at
                                        except ValueError:
                                            try:
                                                created_at = datetime.fromisoformat(created_at_str.replace(' ', 'T'))
                                                return created_at
                                            except:
                                                pass
                        except json.JSONDecodeError:
                            # Если не JSON, пробуем обычный формат
                            created_at_str = text.strip()
                            try:
                                created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
                                return created_at
                            except ValueError:
                                try:
                                    created_at = datetime.fromisoformat(created_at_str.replace(' ', 'T'))
                                    return created_at
                                except:
                                    pass
                    return None
                else:
                    error_text = await response.text()
                    return None
        except Exception as e:
            return None
    
    async def measure_lag_for_user(self, test_id: int) -> Optional[Dict]:
        """Измеряет лаг для одного пользователя"""
        # Создаем пользователя
        user_data = await self.create_user(test_id)
        if not user_data:
            return None
        
        user_id = user_data['user_id']
        username = user_data['username']
        request_time = user_data['request_time']
        
        # Ждем появления записи в ClickHouse
        start_check_time = time.time()
        created_at = None
        check_count = 0
        last_progress_time = start_check_time
        
        while (time.time() - start_check_time) < MAX_WAIT_TIME:
            check_count += 1
            created_at = await self.check_user_in_clickhouse(user_id, username)
            if created_at:
                # Вычисляем лаг сразу при обнаружении
                insert_time = created_at.timestamp()
                lag_seconds = insert_time - request_time
                lag_ms = lag_seconds * 1000
                
                # Выводим информацию о найденной записи
                elapsed_check = time.time() - start_check_time
                print(f"✅ Запись #{test_id} найдена: user_id={user_id}, username={username[:30]}..., "
                      f"лаг={lag_ms:.2f}ms, проверок={check_count}, время проверки={elapsed_check:.1f}с")
                
                user_data['insert_time'] = insert_time
                user_data['insert_timestamp'] = created_at.isoformat()
                user_data['insert_lag_ms'] = lag_ms
                user_data['insert_lag_seconds'] = lag_seconds
                user_data['status'] = 'inserted'
                user_data['check_count'] = check_count
                user_data['check_elapsed_seconds'] = elapsed_check
                
                return user_data
            
            # Показываем прогресс каждые 5 секунд
            current_time = time.time()
            if current_time - last_progress_time >= 5.0:
                elapsed = current_time - start_check_time
                print(f"⏳ Запись #{test_id}: проверка {check_count}, прошло {elapsed:.1f}с из {MAX_WAIT_TIME}с...")
                last_progress_time = current_time
            
            await asyncio.sleep(CHECK_INTERVAL)
        
        # Запись не найдена
        elapsed = time.time() - start_check_time
        print(f"⚠️  Запись #{test_id} не найдена после {elapsed:.1f}с ({check_count} проверок): user_id={user_id}, username={username[:30]}...")
        user_data['status'] = 'not_found'
        user_data['insert_lag_ms'] = None
        user_data['check_count'] = check_count
        user_data['check_elapsed_seconds'] = elapsed
        return user_data
    
    async def run_measurements(self, num_requests: int = NUM_REQUESTS):
        """Запускает измерения лага для нескольких запросов"""
        print("=" * 80)
        print("📊 ИЗМЕРЕНИЕ ЛАГА ВСТАВКИ В CLICKHOUSE")
        print("=" * 80)
        print()
        print(f"Количество запросов: {num_requests}")
        print(f"API URL: {API_URL}")
        print(f"ClickHouse URL: {CLICKHOUSE_URL}")
        print(f"Интервал проверки: {CHECK_INTERVAL} сек")
        print(f"Максимальное время ожидания: {MAX_WAIT_TIME} сек")
        print()
        print("ℹ️  ИНФОРМАЦИЯ:")
        print("   • Система использует батчинг INSERT (интервал flush: 5 сек)")
        print("   • Если Kafka недоступен, используется fallback (прямая вставка в ClickHouse)")
        print("   • Ожидаемый лаг: 5-10 секунд (из-за батчинга)")
        print()
        
        # Создаем задачи последовательно с небольшой задержкой для лучшей отслеживаемости
        print(f"⏳ Отправка {num_requests} запросов...")
        tasks = []
        for i in range(num_requests):
            task = asyncio.create_task(self.measure_lag_for_user(i + 1))
            tasks.append(task)
            # Небольшая задержка между запросами для избежания перегрузки
            await asyncio.sleep(0.2)
        
        print(f"✅ Все запросы отправлены, ожидание вставки в ClickHouse...")
        print(f"   (проверка каждые {CHECK_INTERVAL} сек, максимум {MAX_WAIT_TIME} сек)")
        print()
        
        # Выполняем все задачи
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем исключения
        results = [r for r in results if not isinstance(r, Exception)]
        
        # Фильтруем успешные результаты
        self.results = [r for r in results if r is not None]
        
        return self.results
    
    def print_statistics(self):
        """Выводит статистику измерений"""
        if not self.results:
            print("❌ Нет результатов для анализа")
            return
        
        inserted_results = [r for r in self.results if r.get('status') == 'inserted']
        not_found_results = [r for r in self.results if r.get('status') == 'not_found']
        
        print()
        print("=" * 80)
        print("📈 СТАТИСТИКА ИЗМЕРЕНИЙ")
        print("=" * 80)
        print()
        
        print(f"Всего запросов:        {len(self.results)}")
        print(f"Успешно вставлено:      {len(inserted_results)} ({len(inserted_results)/len(self.results)*100:.1f}%)")
        print(f"Не найдено в БД:        {len(not_found_results)} ({len(not_found_results)/len(self.results)*100:.1f}%)")
        print()
        
        if not inserted_results:
            print("⚠️  Нет успешных измерений для анализа")
            return
        
        # Статистика по лагу вставки
        lags = [r['insert_lag_ms'] for r in inserted_results]
        api_times = [r['api_response_time_ms'] for r in inserted_results]
        
        print("⏱️  ЛАГ ВСТАВКИ (время от запроса до вставки в БД):")
        print(f"   Минимум:             {min(lags):.2f} ms")
        print(f"   Максимум:            {max(lags):.2f} ms")
        print(f"   Среднее:             {sum(lags) / len(lags):.2f} ms")
        print(f"   Медиана:             {sorted(lags)[len(lags) // 2]:.2f} ms")
        if len(lags) > 1:
            p95_index = int(len(lags) * 0.95)
            p99_index = int(len(lags) * 0.99)
            print(f"   95 перцентиль:       {sorted(lags)[p95_index]:.2f} ms")
            print(f"   99 перцентиль:       {sorted(lags)[min(p99_index, len(lags)-1)]:.2f} ms")
        print()
        
        print("⚡ ВРЕМЯ ОТВЕТА API (время от запроса до ответа API):")
        print(f"   Минимум:             {min(api_times):.2f} ms")
        print(f"   Максимум:            {max(api_times):.2f} ms")
        print(f"   Среднее:             {sum(api_times) / len(api_times):.2f} ms")
        print(f"   Медиана:             {sorted(api_times)[len(api_times) // 2]:.2f} ms")
        print()
        
        # Разница между лагом и временем ответа API
        differences = [lag - api_time for lag, api_time in zip(lags, api_times)]
        print("📊 РАЗНИЦА (лаг вставки - время ответа API):")
        print(f"   Это время, которое запись провела в очереди/буфере")
        print(f"   Минимум:             {min(differences):.2f} ms")
        print(f"   Максимум:            {max(differences):.2f} ms")
        print(f"   Среднее:             {sum(differences) / len(differences):.2f} ms")
        print()
        
        # Распределение лагов
        print("📊 РАСПРЕДЕЛЕНИЕ ЛАГОВ:")
        ranges = [
            (0, 100, "< 100ms"),
            (100, 500, "100-500ms"),
            (500, 1000, "500ms-1s"),
            (1000, 5000, "1-5s"),
            (5000, float('inf'), "> 5s"),
        ]
        for min_val, max_val, label in ranges:
            count = sum(1 for lag in lags if min_val <= lag < max_val)
            percentage = (count / len(lags)) * 100
            print(f"   {label:15} {count:3} запросов ({percentage:5.1f}%)")
        print()
        
        # Примеры записей
        print("📝 ПРИМЕРЫ ИЗМЕРЕНИЙ (первые 5):")
        for i, result in enumerate(inserted_results[:5], 1):
            print(f"\n   Запрос #{result['test_id']}:")
            print(f"      User ID:           {result['user_id']}")
            print(f"      Username:          {result['username']}")
            print(f"      Время запроса:     {result['request_timestamp']}")
            print(f"      Время вставки:     {result['insert_timestamp']}")
            print(f"      Время ответа API:  {result['api_response_time_ms']:.2f} ms")
            print(f"      Лаг вставки:       {result['insert_lag_ms']:.2f} ms")
            print(f"      Проверок в БД:     {result.get('check_count', 'N/A')}")
        
        # Показываем информацию о не найденных записях
        if not_found_results:
            print()
            print("⚠️  НЕ НАЙДЕННЫЕ ЗАПИСИ:")
            print(f"   Всего не найдено:    {len(not_found_results)}")
            if len(not_found_results) <= 10:
                for result in not_found_results:
                    print(f"      • User ID: {result['user_id']}, Username: {result['username']}")
            else:
                print(f"      (показаны первые 5 из {len(not_found_results)})")
                for result in not_found_results[:5]:
                    print(f"      • User ID: {result['user_id']}, Username: {result['username']}")
            print()
            print("💡 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
            print("   • Записи еще обрабатываются Kafka Consumer (батчинг до 5 сек)")
            print("   • Kafka Consumer не запущен или не работает (проверьте: make logs-api | grep consumer)")
            print("   • Проблемы с Zookeeper/Kafka координатором (CoordinatorNotAvailableError)")
            print("   • Fallback механизм работает, но батчинг задерживает вставку (до 5 сек)")
            print("   • Проблемы с подключением к ClickHouse")
            print("   • ⚠️  ВСЕ ПОЛЬЗОВАТЕЛИ ПОЛУЧИЛИ ОДИНАКОВЫЙ ID (4283686118)")
            print("     → Это временный ID при ошибке генерации ID в ClickHouse")
            print("     → Проверьте подключение к ClickHouse и логи API")
            print()
            print("🔧 РЕКОМЕНДАЦИИ:")
            print("   1. Проверьте статус ClickHouse: docker ps | grep clickhouse")
            print("   2. Проверьте логи API: make logs-api | grep -i 'fallback\\|error\\|warning\\|ID'")
            print("   3. Проверьте логи ClickHouse: docker-compose logs clickhouse | tail -50")
            print("   4. Проверьте подключение к ClickHouse:")
            print("      curl 'http://localhost:8123/?query=SELECT%201'")
            print("   5. Проверьте количество записей:")
            print("      curl 'http://localhost:8123/?query=SELECT%20count()%20FROM%20music_recommend.users'")
            print("   6. Перезапустите сервисы: make restart")
        
        print()
        print("=" * 80)


async def main():
    """Главная функция"""
    num_requests = int(sys.argv[1]) if len(sys.argv) > 1 else NUM_REQUESTS
    
    async with LagMeasurement() as measurement:
        await measurement.run_measurements(num_requests)
        measurement.print_statistics()
        
        # Сохраняем результаты в JSON
        output_file = f"load_tests_investigation/insert_lag_results_{int(time.time())}.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(measurement.results, f, indent=2, ensure_ascii=False)
            print(f"💾 Результаты сохранены в: {output_file}")
        except Exception as e:
            print(f"⚠️  Не удалось сохранить результаты: {e}")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
