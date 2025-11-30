> PYTEST 126 passed, 12 skipped, 10 warnings in 35.65s | 33.13s 
> ...... 126 passed, 12 skipped, 11 warnings in 39.76s
> ...... 124 passed, 7 skipped, 10 warnings in 27.29s 

# k6 run load_tests/k6_diagnostics_test.js 

```
═══════════════════════════════════════════════════════════
            🔍 ДИАГНОСТИКА ПРОИЗВОДИТЕЛЬНОСТИ              
═══════════════════════════════════════════════════════════
📊 Общая статистика:                         
• Виртуальных пользователей: 10   

• Всего запросов:   
- 1262     # ADDED CLICKHOUSE INDEXES
- 1207
- 1185         
- 1230   
- 1250
- 1300
- 1255 

• Общий процент ошибок:    
- 0.00 %
- 59.66%  # FIXED RANDOM IDS !!! 
- 60.00% 
- 59.76%
- 59.76% 
- 59.77%        

📈 Время ответа по эндпоинтам:                 
📋 GET /users (list):     
- Среднее: 48ms | p95: 129ms | Max: 461ms    # ADDED CLICKHOUSE INDEXES
- Среднее: 78ms | p95: 238ms | Max: 493ms
- Среднее: 75ms | p95: 196ms | Max: 254ms    # FIXED RANDOM IDS !!!
- Среднее: 70ms | p95: 204ms | Max: 329ms
- Среднее: 65ms | p95: 242ms | Max: 411ms
- Среднее: 39ms | p95: 73ms  | Max: 389ms 
- Среднее: 48ms | p95: 124ms | Max: 156ms  

🎵 GET /tracks (list):      
- Среднее: 41ms | p95: 189ms | Max: 470ms    # ADDED CLICKHOUSE INDEXES
- Среднее: 75ms | p95: 191ms | Max: 530ms
- Среднее: 85ms | p95: 232ms | Max: 338ms    # FIXED RANDOM IDS !!!
- Среднее: 58ms | p95: 149ms | Max: 324ms
- Среднее: 54ms | p95: 164ms | Max: 341ms
- Среднее: 24ms | p95: 53ms  | Max: 116ms  
- Среднее: 50ms | p95: 139ms | Max: 184ms

🎯 GET /recommendations (HEAVY):
- Среднее: 7ms | p95: 55ms | Max: 194ms      # ADDED CLICKHOUSE INDEXES
- Среднее: 57ms | p95: 188ms | Max: 644ms
- Среднее: 56ms | p95: 128ms | Max: 343ms    # FIXED RANDOM IDS !!!
- Среднее: 50ms | p95: 112ms | Max: 356ms
- Среднее: 29ms | p95: 98ms  | Max: 234ms  
- Среднее: 48ms | p95: 105ms | Max: 134ms

👤 GET /users/{id}:        
- Среднее: 46ms | p95: 139ms           # ADDED CLICKHOUSE INDEXES
- Среднее: 80ms | p95: 296ms     
- Среднее: 73ms | p95: 226ms           # FIXED RANDOM IDS !!!
- Среднее: 50ms | p95: 135ms
- Среднее: 40ms | p95: 94ms
- Среднее: 21ms | p95: 47ms
- Среднее: 43ms | p95: 81ms

🎵 GET /tracks/{id}:          
   Среднее: 40ms | p95: 138ms       # ADDED CLICKHOUSE INDEXES
   Среднее: 77ms | p95: 239ms
   Среднее: 61ms | p95: 158ms       # FIXED RANDOM IDS !!!
   Среднее: 44ms | p95: 120ms
   Среднее: 39ms | p95: 89ms
   Среднее: 23ms | p95: 46ms
   Среднее: 35ms | p95: 68ms

🔍 АНАЛИЗ И РЕКОМЕНДАЦИИ:                   
✅ Хорошая производительность!         # ADDED CLICKHOUSE INDEXES  
❌ Высокий процент ошибок              # FIXED RANDOM IDS !!!

------------------------------------------------------
# FIXED RANDOM IDS and ADDED CLICKHOUSE INDEXES
✅ Нет реальных ошибок!                     
• Все запросы успешно обработаны        
• 404 (Not Found) - это нормально для случайных ID  
------------------------------------------------------

running (0m58.9s), 00/10 VUs, 252 complete and 0 interrupted iterations
running (0m58.8s), 00/10 VUs, 237 ...
running (1m01.1s), 00/10 VUs, 230 complete and 0 interrupted iterations
running (1m02.5s), 00/10 VUs, 244 complete and 0 interrupted iterations
running (1m01.8s), 00/10 VUs, 250 complete and 0 interrupted iterations
running (1m01.2s), 00/10 VUs, 260 complete and 0 interrupted iterations

default ✓ [======================================] 10 VUs  1m0s 
```



# k6 run load_tests/k6_smoke_test.js

```
═══════════════════════════════════════════════════════════
                🔥 SMOKE TEST ЗАВЕРШЁН                     
═══════════════════════════════════════════════════════════

📊 Статистика:                                 
Всего запросов:                                 84                    
Среднее время ответа: 
- [28.38ms, 41.38ms, 27.85ms]                    # ADDED CLICKHOUSE INDEXES
- [39.61ms, 51.80ms, 26.03ms]
- [50.54m, 30.32ms, 25.62ms, 44.60ms ]
- [24.29ms, 37.53ms, 107.00ms]   
- 29.81ms  
- 28.69    

95 перцентиль:     
- [62.34ms, 128.38ms, 62.92ms]                    # ADDED CLICKHOUSE INDEXES
- [88.34ms, 196.02ms, 56.97ms]
- [125.85ms, 73.44ms, 54.90ms, 232.59ms]
- [59.86ms, 107.00ms]
- 64.46ms
- 84.120ms
- 84.20ms

Процент ошибок:        0.00%     
Успешные проверки:     100.00%   
✅ PASSED: API работает нормально. Можно запускать полноценные тесты! 

running (10.9s), 0/3 VUs, 12 complete and 0 interrupted iterations
[running (11.2s) 0/3 VUs 12, ]
[running (09.9s) 12, ]
[running (09.5s), 0/3 VUs, 12 ..., running (11.1s)..., ]
running (10.9s), 0/3 VUs, 12 complete and 0 interrupted iterations
running (10.9s), 0/3 VUs, 12 complete and 0 interrupted iterations
running (11.5s), 0/3 VUs, 9 complete and 0 interrupted iterations

default ✓ [======================================] 3 VUs  10s
```



# k6 run load_tests/k6_spike_test.js

```
═══════════════════════════════════════════════════════════ 
             ⚡ SPIKE TEST ЗАВЕРШЁН                        
═══════════════════════════════════════════════════════════

📊 Статистика:                          
• Пиковая нагрузка:      50 VUs      
• Всего запросов:     
- 4013                   # ADDED CLICKHOUSE INDEXES
- [1141, 3322]   
- [3177, ]               # FIX RANDOM IDS
- [3708, 3498]
- [4400, 4522, 3123]
- 4453     
- 4508      
- 4465 

• Среднее время:    
- 300.85ms                  # ADDED CLICKHOUSE INDEXES
- [1831.55ms,  418.27ms]
- [453.82ms, ]              # FIX RANDOM IDS
- [342.30ms, 382.81ms]
- [244.62ms, 230.39ms, 459.24ms]  
- 242.78ms   
- 235.26ms  
- 240.12ms

• 95 перцентиль: 
- 708.20ms                   # ADDED CLICKHOUSE INDEXES
- [3875.84ms, 1137.40ms] 
- [1166.98ms, ]   # FIX RANDOM IDS
- [903.32ms, 958.97ms]
- [559.38ms, 463.50ms, 1086.44ms]    
- 630.53ms
- 727.85ms
- 665.08ms

• 99 перцентиль:         
- 0.00ms   

• Процент ошибок:    
- [0.00%,  0.00%] # ADDED CLICKHOUSE INDEXES
- [60.72%, ]      # FIX RANDOM IDS
- [58.98%, 59.52%]
- [59.93%, 59.44%, 58.66%]  
- 60.61% 
- 59.49%
- 59.08%


✅ PASSED: Система устойчива к пиковым нагрузкам!              # ADDED CLICKHOUSE INDEXES
❌ FAILED: Слишком много ошибок при пиковой нагрузке. Требуется оптимизация!  # FIX RANDOM IDS

💡 Spike test показывает, как система ведет себя при резком росте трафика.
Небольшая деградация производительности - это нормально.  

running (1m16.6s), 00/50 VUs, 4011 complete and 0 interrupted iterations
[running (1m14.8s), 00/50 VUs, 3498 complete ...]
[running (1m17.8s) - 4400, running (1m17.5s) - 4522, running (1m17.4s) - 3123]
running (1m20.3s), 00/50 VUs, 4453 complete and 0 interrupted iterations
running (1m20.2s), 00/50 VUs, 4508 complete and 0 interrupted iterations  
running (1m20.3s), 00/50 VUs, 4465 complete ...

default ✓ [======================================] 00/50 VUs  1m20s
```



# k6 run load_tests/k6_quick_performance_test.js 

```
INFO[0000] ✅ Загружено 100 пользователей                 
User 49687669: ❌ Error 404                    source=console   # FIX RANDOM IDS
...

═══════════════════════════════════════════════════════════════════════════════
   ⚡ БЫСТРЫЙ ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ РЕКОМЕНДАЦИЙ
═══════════════════════════════════════════════════════════════════════════════
INFO[0000] 📊 Обработано запросов: 11  |  10                     
───────────────────────────────────────────────────────────────────────────────
💾 КЭШ:                                        
• Попадания в кэш:  
- 1.25ms          # ADDED CLICKHOUSE INDEXES
- 10     
- 0

• Промахи кэша:  0 

• Hit Rate:         100%   | 0%                     
─────────────────────────────────────────────────────────────────────────────── 
⏱️  СРЕДНЕЕ ВРЕМЯ ВЫПОЛНЕНИЯ:                 
Redis:                                     
• Проверка кэша:              
- 1.25ms          # ADDED CLICKHOUSE INDEXES
- 6.96ms 
- 0.00ms    

• Сохранение:                 0.00ms | 0.00ms | 0.00ms    

• ИТОГО Redis:                6.96ms | 0.00ms    
   
ClickHouse:
• Проверка пользователя:      0.00ms    
• Подсчет взаимодействий:     0.00ms    
• Поиск похожих польз.:       0.00ms    
• Получение рекомендаций:     0.00ms    
• ИТОГО ClickHouse:           0.00ms    

Алгоритм:                                 
• Обработка результатов:      0.00ms    


📊 ОБЩЕЕ ВРЕМЯ:                            
• Total Response Time:        1.35ms | 7.13ms | 0.00ms    

───────────────────────────────────────────────────────────────────────────────
📈 РАСПРЕДЕЛЕНИЕ ВРЕМЕНИ:                      
• Redis:            
- 92.9%                          # ADDED CLICKHOUSE INDEXES
- 97.5%  | 0.0%  
• ClickHouse:       0.0%   | 0.0% | 0.0%  
• Алгоритм:         0.0%   | 0.0%  | 0.0%  
• Прочее:           7.1%   | 2.5%  | 100.0%   
───────────────────────────────────────────────────────────────────────────────
📊 СТАТИСТИКА:         
• Всего запросов:             11                       
• Успешных запросов:          20 | 0            
• Ошибок:                     0  | 20           

• Среднее время HTTP:
- 5.70ms                   # ADDED CLICKHOUSE INDEXES       
- 20.06ms, 13.04ms
- [62.99ms, ]
- [52.02ms, 32.18ms]
- [25.03ms, 29.59ms]
- 28.76ms
- 22.36ms
- 45.79ms

• p95 HTTP:  
- 13.51ms                  # ADDED CLICKHOUSE INDEXES
- 50.53ms, 40.44ms
- [116.80ms, ]                 
- [108.04ms, 56.78ms]
- [38.80ms, 50.28ms] 
- 52.03ms
- 31.17ms
- 127.97ms  

running (00m00.1s), 0/1 VUs, 10 complete and 0 interrupted iterations
running (00m00.3s), 0/1 VUs, 10 complete and 0 interrupted iterations
running (00m00.2s), 0/1 VUs, 10 complete and 0 interrupted iterations
running (00m00.5s), 0/1 VUs, 10 complete ...

default ✓ [======================================] 1 VUs  00m00.3s/10m0s  10/10 shared iters
```



# k6 run load_tests/k6_recommendations_performance_test.js - LONG

```
scenarios: (100.00%) 3 scenarios, 50 max VUs, 5m30s max duration (incl. graceful stop):
   * cold_cache: 10 looping VUs for 30s (gracefulStop: 30s)
   * warm_cache: 20 looping VUs for 1m0s (startTime: 1m0s, gracefulStop: 30s)
   * load_test: Up to 50 looping VUs for 2m0s over 3 stages (gracefulRampDown: 30s, startTime: 3m0s, gracefulStop: 30s)

═══════════════════════════════════════════════════════════════════════════════
📊 ДЕТАЛЬНЫЙ АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ РЕКОМЕНДАЦИЙ  
════════════════════════════════════════════════════════════════════════════════  
📊 Общая статистика:                           
• Виртуальных юзеров:    50                

• Длительность теста:    
-  4m 44s      # ADDED CLICKHOUSE INDEXES 
- [4m 44s, ]
- [4m 48s, ]
- 5m 0s

• Всего запросов:      
- 5317            # ADDED CLICKHOUSE INDEXES
- 5072  
- [5076]
- [5178, ]
- 5072
- 5205
- 5261 

• RPS (req/sec):   
- 18.71           # ADDED CLICKHOUSE INDEXES
- 17.81
- [17.84, ]
- [17.95, ]      
- 16.86   
- 17.48
- 17.29 

• Процент ошибок:
- 0%
- [99.90%, ]
- [99.88%, ]
- 99.94%
- 99.83%
- 99.90%     
                                               
⏱️  Время ответа:                             
• Минимум:           
- 2ms         # ADDED CLICKHOUSE INDEXES
- -1705ms  
- [0ms, ]  
- [-1410ms, ]
- 12ms
- 11ms              

• Среднее:
- 14ms      # ADDED CLICKHOUSE INDEXES
- 61ms
- [64ms, ]
- [43ms, ]
- 66ms
- 28ms
- 38ms

• Медиана:  
- 4ms       # ADDED CLICKHOUSE INDEXES
- 5ms
- [39ms, ]             
- [26ms, ]
- 33ms
- 18ms              

• 95 перцентиль:  
- 23ms      # ADDED CLICKHOUSE INDEXES
- 54ms
- [195ms, ]       
- [132ms, ]
- 194ms
- 77ms
- 135ms

• 99 перцентиль:         0ms               

• Максимум:       
- 3107ms       # ADDED CLICKHOUSE INDEXES
- 6866ms
- [1199ms, ]       
- [633ms, ]
- 1847ms
- 546ms
- 2754ms
                                               
💾 СТАТИСТИКА КЭША (Redis):                  
• Попадания в кэш:
- 5278                     # ADDED CLICKHOUSE INDEXES
- 4966
- 0              
• Промахи кэша:  
- 38                       # ADDED CLICKHOUSE INDEXES  
- 105
- 5 || 3 || 9 || 5

• Hit Rate:
- 99.29%                   # ADDED CLICKHOUSE INDEXES
- 97.93%
- 0.00% 

                                               
Redis - проверка кэша:    
   avg: 3.07ms | med: 1.21ms | p95: 11.37ms | p99: 0.00ms  
   min: 0.63ms | max: 59.42ms 
   ----------------------------------------------------------     # ADDED CLICKHOUSE INDEXES
   ----------------------------------------------------------
   avg: 2.85ms | med: 2.22ms | p95: 6.15ms | p99: 0.00ms  
   min: 0.76ms | max: 6.83ms 
   ----------------------------------------------------------
   avg: 1.85ms | med: 1.35ms | p95: 3.42ms  | p99: 0.00ms
   min: 0.84ms | max: 3.50ms  
   ----------------------------------------------------------
   avg: 1.98ms | med: 1.44ms | p95: 3.22ms  | p99: 0.00ms 
   min: 1.09ms | max: 3.42ms
   ----------------------------------------------------------
   avg: 3.80ms | med: 1.16ms | p95: 13.34ms | p99: 0.00ms
   min: 0.63ms | max: 14.00ms
   ----------------------------------------------------------
   avg: 3.63ms | med: 1.84ms | p95: 8.38ms  | p99: 0.00ms
   min: 0.55ms | max: 9.25ms 

Redis - сохранение:   
   avg: 4.63ms | med: 3.39ms | p95: 11.11ms | p99: 0.00ms  
   min: 1.14ms | max: 13.22ms
   ----------------------------------------------------------     # ADDED CLICKHOUSE INDEXES
   -----------------------------------------------------------
   avg: 8.81ms | med: 5.36ms | p95: 18.20ms | p99: 0.00ms  
   min: 2.20ms | max: 19.82ms         
   ----------------------------------------------------------
   avg: 5.20ms | med: 4.97ms | p95: 7.40ms | p99: 0.00ms
   min: 3.17ms | max: 7.50ms
   ----------------------------------------------------------        
   avg: 7.02ms | med: 4.95ms | p95: 11.14ms | p99: 0.00ms 
   min: 4.29ms | max: 11.82ms
   ----------------------------------------------------------   
   avg: 6.41ms | med: 3.63ms | p95: 14.66ms | p99: 0.00ms
   min: 1.66ms | max: 16.44ms              
   ----------------------------------------------------------
   avg: 7.52ms | med: 7.01ms | p95: 12.70ms | p99: 0.00ms
   min: 3.47ms | max: 13.93ms

Redis - ИТОГО:     
   avg: 3.10ms | med: 1.22ms | p95: 11.59ms | p99: 0.00ms  
   min: 0.63ms | max: 59.42ms
   ----------------------------------------------------------     # ADDED CLICKHOUSE INDEXES
   ----------------------------------------------------------
   5.85ms | med: 1.55ms | p95: 22.37ms | p99: 0.00ms  source=console
   min: 0.53ms | max: 239.80ms
   ----------------------------------------------------------
   avg: 11.66ms | med: 12.19ms | p95: 21.38ms | p99: 0.00ms  
   min: 3.22ms | max: 23.25ms   
   ----------------------------------------------------------
   avg: 7.05ms | med: 6.83ms | p95: 10.20ms | p99: 0.00ms  
   min: 4.06ms | max: 10.27ms
   ----------------------------------------------------------                       
   avg: 9.00ms | med: 7.70ms | p95: 12.39ms | p99: 0.00ms 
   min: 6.39ms | max: 12.91ms
   ----------------------------------------------------------
   avg: 10.20ms | med: 9.58ms | p95: 18.36ms | p99: 0.00ms
   min: 2.82ms  | max: 19.20ms              
   ----------------------------------------------------------
   avg: 11.14ms | med: 8.61ms | p95: 21.07ms | p99: 0.00ms
   min: 4.02ms  | max: 23.18ms


🗄️  СТАТИСТИКА CLICKHOUSE:
Проверка пользователя:
   avg: 43.66ms | med: 27.12ms | p95: 130.67ms | p99: 0.00ms  
   min: 11.62ms | max: 137.26ms
   ----------------------------------------------------------     # ADDED CLICKHOUSE INDEXES
   avg: 162.03ms | med: 113.47ms | p95: 452.59ms | p99: 0.00ms
   min: 14.06ms | max: 646.95ms 
   ----------------------------------------------------------
   avg: 33.39ms | med: 19.60ms | p95: 57.61ms | p99: 0.00ms  
   min: 18.75ms | max: 61.83ms 
   ----------------------------------------------------------
   avg: 34.64ms | med: 33.90ms | p95: 45.85ms | p99: 0.00ms  
   min: 24.32ms | max: 47.28ms 
   ----------------------------------------------------------
   avg: 24.24ms | med: 21.92ms | p95: 30.82ms | p99: 0.00ms
   min: 19.00ms | max: 31.81ms
   ----------------------------------------------------------
   avg: 22.75ms | med: 23.35ms | p95: 32.50ms | p99: 0.00ms
   min: 10.58ms | max: 35.89ms             
   ----------------------------------------------------------
   avg: 51.03ms | med: 35.18ms | p95: 114.30ms | p99: 0.00ms
   min: 16.08ms | max: 131.23ms

Подсчет взаимодействий:
   avg: 52.87ms | med: 40.87ms | p95: 136.87ms | p99: 0.00ms  
   min: 11.35ms | max: 183.79ms
   ----------------------------------------------------------     # ADDED CLICKHOUSE INDEXES
   avg: 189.57ms | med: 134.77ms | p95: 475.92ms | p99: 0.00ms  
   min: 13.34ms | max: 1043.46ms
   ----------------------------------------------------------
   avg: 60.54ms | med: 56.03ms | p95: 96.95ms | p99: 0.00ms  
   min: 24.11ms | max: 101.50ms
   ----------------------------------------------------------
   avg: 43.21ms | med: 29.21ms | p95: 92.67ms | p99: 0.00ms  
   min: 19.39ms | max: 105.40ms 
   ----------------------------------------------------------
   avg: 40.27ms | med: 31.37ms | p95: 56.59ms | p99: 0.00ms 
   min: 30.04ms | max: 59.39ms
   ----------------------------------------------------------
   avg: 41.39ms | med: 46.65ms | p95: 71.27ms | p99: 0.00ms
   min: 19.50ms | max: 79.07ms             
   ----------------------------------------------------------
   avg: 124.36ms | med: 38.80ms | p95: 346.81ms | p99: 0.00ms 
   min: 24.36ms  | max: 400.16ms

Поиск похожих польз.:   
   avg: 182.49ms | med: 89.29ms | p95: 331.98ms | p99: 0.00ms
   min: 32.88ms | max: 2247.22ms
   ----------------------------------------------------------     # ADDED CLICKHOUSE INDEXES
   avg: 578.56ms | med: 463.24ms | p95: 1433.31ms | p99: 0.00ms  
   min: 59.83ms | max: 2585.81ms
   ----------------------------------------------------------
   avg: 127.13ms | med: 84.02ms | p95: 226.27ms | p99: 0.00ms  
   min: 55.29ms | max: 242.08ms 
   ----------------------------------------------------------         
   avg: 94.53ms | med: 86.04ms | p95: 164.35ms | p99: 0.00ms  
   min: 39.27ms | max: 182.61ms
   ----------------------------------------------------------   
   avg: 93.89ms | med: 56.50ms | p95: 166.54ms | p99: 0.00ms 
   min: 46.41ms | max: 178.77ms
   ----------------------------------------------------------    
   avg: 72.12ms | med: 63.12ms | p95: 129.29ms | p99: 0.00ms  
   min: 35.25ms | max: 142.90ms            
   ----------------------------------------------------------
   avg: 231.81ms | med: 143.98ms | p95: 488.95ms | p99: 0.00ms
   min: 54.85ms  | max: 522.82ms

Получение рекомендаций:
   avg: 354.08ms | med: 211.29ms | p95: 998.95ms | p99: 0.00ms
   min: 66.45ms | max: 1521.59ms
   ----------------------------------------------------------     # ADDED CLICKHOUSE INDEXES
   avg: 2453.42ms | med: 2451.73ms | p95: 5136.03ms | p99: 0.00ms  
   min: 266.96ms | max: 6807.67ms 
   ----------------------------------------------------------
   avg: 507.39ms | med: 504.40ms | p95: 731.36ms | p99: 0.00ms  
   min: 275.55ms | max: 764.56ms 
   ---------------------------------------------------------------
   avg: 260.65ms | med: 259.14ms | p95: 378.26ms | p99: 0.00ms  
   min: 147.29ms | max: 381.28ms 
   ---------------------------------------------------------------
   avg: 245.16ms | med: 211.60ms | p95: 346.85ms | p99: 0.00ms
   min: 161.98ms | max: 361.88ms 
   ---------------------------------------------------------------
   avg: 229.81ms | med: 225.16ms | p95: 349.68ms | p99: 0.00ms
   min: 112.35ms | max: 375.19ms           
   ---------------------------------------------------------------
   avg: 757.93ms | med: 490.06ms | p95: 1540.38ms | p99: 0.00ms
   min: 153.58ms | max: 1654.74ms

ClickHouse - ИТОГО:   
   avg: 623.49ms | med: 426.10ms | p95: 1533.25ms | p99: 0.00ms  
   min: 124.31ms | max: 3016.55ms
   ----------------------------------------------------------     # ADDED CLICKHOUSE INDEXES
   avg: 2453.42ms | med: 2451.73ms | p95: 5136.03ms | p99: 0.00ms
   min: 266.96ms | max: 6807.67ms
   --------------------------------------------------------------- 
   avg: 640.03ms | med: 598.56ms | p95: 1068.78ms | p99: 0.00ms  
   min: 373.69ms | max: 1169.97ms
   --------------------------------------------------------------- 
   avg: 433.03ms | med: 427.97ms | p95: 606.19ms | p99: 0.00ms  
   min: 253.78ms | max: 620.18ms 
   ---------------------------------------------------------------
   avg: 403.56ms | med: 308.38ms | p95: 590.61ms | p99: 0.00ms
   min: 280.34ms | max: 621.97ms
   ---------------------------------------------------------------
   avg: 366.08ms | med: 353.39ms | p95: 527.87ms | p99: 0.00ms  
   min: 218.49ms | max: 537.23ms           
   ---------------------------------------------------------------
   avg: 1165.13ms | med: 930.37ms | p95: 2426.88ms | p99: 0.00ms
   min: 302.43ms | max: 2708.96ms          


🧮 СТАТИСТИКА АЛГОРИТМА:                        
Обработка результатов:
   avg: 0.91ms | med: 0.61ms | p95: 2.61ms | p99: 0.00ms  
   min: 0.30ms | max: 3.60ms
   ----------------------------------------------------------     # ADDED CLICKHOUSE INDEXES
   avg: 1.02ms | med: 0.59ms | p95: 2.31ms | p99: 0.00ms  
   min: 0.32ms | max: 12.63ms
   ---------------------------------------------------------------
   avg: 0.71ms | med: 0.58ms | p95: 1.18ms | p99: 0.00ms  
   min: 0.49ms | max: 1.31ms
   ---------------------------------------------------------------
   avg: 0.88ms | med: 0.66ms | p95: 1.97ms | p99: 0.00ms  
   min: 0.38ms | max: 2.39ms 
   ---------------------------------------------------------------
   avg: 0.42ms | med: 0.37ms | p95: 0.55ms | p99: 0.00ms  
   min: 0.32ms | max: 0.57ms
   ---------------------------------------------------------------       
   avg: 0.53ms | med: 0.46ms | p95: 0.94ms | p99: 0.00ms
   min: 0.25ms | max: 1.04ms               
   ---------------------------------------------------------------
   avg: 3.00ms | med: 0.53ms | p95: 9.22ms | p99: 0.00ms  
   min: 0.39ms | max: 10.82ms 

• Похожих пользователей (среднее): 17.3   || 15.8 || 15.0 || 15.3    || 12.3   || 16.8   
• Похожих пользователей (мин):     4      || 5    || 13   || 12      || 11     || 9     || 6
• Похожих пользователей (макс):    34     || 39   || 18   || 12      || 14     || 28    || 14

⏱️  ОБЩЕЕ ВРЕМЯ ОТВЕТА:                       
Total Response Time:   
   avg: 7.80ms | med: 1.34ms | p95: 13.01ms | p99: 0.00ms
   min: 0.69ms | max: 3069.77ms
   ----------------------------------------------------------     # ADDED CLICKHOUSE INDEXES
   avg: 56.99ms | med: 1.69ms | p95: 30.68ms | p99: 0.00ms
   min: 0.59ms | max: 6842.29ms
   ---------------------------------------------------------------
   avg: 660.33ms | med: 627.88ms | p95: 1088.77ms | p99: 0.00ms  
   min: 388.30ms | max: 1193.99ms
   ---------------------------------------------------------------
   avg: 441.08ms | med: 435.78ms | p95: 616.50ms | p99: 0.00ms  
   min: 259.37ms | max: 629.65ms
   ---------------------------------------------------------------
   avg: 413.13ms | med: 321.78ms  | p95: 599.50ms   | p99: 0.00ms 
   min: 287.25ms | max: 630.36ms
   ---------------------------------------------------------------
   avg: 376.94ms | med: 357.63ms  | p95: 539.15ms  | p99: 0.00ms  
   min: 221.65ms | max: 542.89ms           
   ---------------------------------------------------------------
   avg: 1179.78ms | med: 943.75ms | p95: 2456.45ms | p99: 0.00ms
   min: 313.70ms  | max: 2743.56ms


📈 АНАЛИЗ РАСПРЕДЕЛЕНИЯ ВРЕМЕНИ (среднее):     
• Redis:
- 3.10ms (39.8%)            # ADDED CLICKHOUSE INDEXES
- 5.85ms (10.3%)
- 11.66ms (1.8%)
- 9.00ms (2.2%)      
- 10.20ms (2.7%)  
- 11.14ms (0.9%)

• ClickHouse:
- 623.49ms (7989.7%)        # ADDED CLICKHOUSE INDEXES
- 2453.42ms (4304.7%)
- 640.03ms (96.9%)
- 433.03ms (98.2%)
- 403.56ms (97.7%)
- 366.08ms (97.1%)
- 1165.13ms (98.8%)

• Алгоритм:   
- 0.91ms (11.6%)           # ADDED CLICKHOUSE INDEXES
- 1.02ms (1.8%)
- 0.71ms (0.1%)
- 0.88ms (0.2%)
- 0.42ms (0.1%)
- 0.53ms (0.1%)      
- 3.00ms (0.3%)

• Прочее (сеть, FastAPI):
- -619.70ms (-7941.1%)     # ADDED CLICKHOUSE INDEXES
- -2403.30ms (-4216.8%)
- 7.93ms (1.2%)
- 0.13ms (0.0%)  
- 0.14ms (0.0%)
- 0.12ms (0.0%)      
- 0.51ms (0.0%)

• ИТОГО:
- 7.80ms (100.0%)            # ADDED CLICKHOUSE INDEXES
- 56.99ms (100.0%)
- 660.33ms (100.0%)
- 441.08ms (100.0%)
- 413.13ms (100.0%)
- 376.94ms (100.0%)
- 1179.78ms (100.0%)  


💡 РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ:          
✅ Производительность в пределах нормы! Все компоненты работают эффективно  
----------------------------------------------------------------------------------------------- # ADDED CLICKHOUSE INDEXES    
⚠️  ClickHouse запросы медленные (>2000ms). Рассмотрите оптимизацию запросов или добавление индексов. 
⚠️  Получение рекомендаций медленное (>1500ms). Рассмотрите материализованные представления или денормализацию.
--------------------------------------------------------------------------------------------------------------
⚠️  Низкий Hit Rate кэша (<30%). Рассмотрите увеличение TTL или предварительный прогрев кэша.  # FIX RANDOM IDS

running (4m48.4s), 00/50 VUs, 5178 ...
running (5m00.9s), 00/50 VUs, 5072 complete and 0 interrupted iterations
running (5m01.0s), 00/50 VUs, 5261 complete and 0 interrupted iterations  
running (5m01.0s), 00/50 VUs, 5205 ...

cold_cache ✓ [======================================] 10 VUs     30s
warm_cache ✓ [======================================] 20 VUs     1m0s
load_test  ✓ [======================================] 00/50 VUs  2m0s

ERRO[0301] thresholds on metrics 'cache_hit_rate, errors, http_req_failed, success' have been crossed
```



# [ERROR] k6 run load_tests/k6_stress_test.js - VERY LONG

ERRO[1741] thresholds on metrics 'http_req_failed' have been crossed
ERRO[1741] TypeError: Cannot read property 'toFixed' of undefined or null

```
scenarios: (100.00%) 1 scenario, 500 max VUs, 29m30s max duration (incl. graceful stop):
* default: Up to 500 looping VUs for 29m0s over 7 stages (gracefulRampDown: 30s, gracefulStop: 30s) ceful stop): ampDown: 30s, gracefulStop: 30s) interrupted iterations

scenarios: (100.00%) 1 scenario, 500 max VUs, 291/500 VUs  02m06.6s/29m00.0sm30s max duration (incl. graceful stop):
* default: Up to 500 looping VUs for 29interrupted iterations m0s over 7 stages (gracefulRampDown: 30s, gracefulSto/500 VUs  02m06.9s/29m00.0s p: 30s)


running (02m06.6s), 051/500 VUs, 3987 complete and 0 interrupted iterations
default   [=>------------------------------------] 051/500 VUs  02m06.6s/29m00.0s

running (02m07.4s), 051/500 VUs, 3998 complete and 0 interrupted iterations

WARN[0293] The test has generated metrics with 100036 unique time series, which is higher than the suggested limit of 100000 and could cause high memory usage. Consider not using high-cardinality values like unique IDs as metric tags or, if you need them in the URL, use the name metric tag or URL grouping. See https://grafana.com/docs/k6/latest/using-k6/tags-and-groups/ for details.  component=metrics-engine-ior details.  component=metrics-engine-ingester                                                               limit of 100000 and could cause high me

WARN[0493] The test has generated metrics with 200035 unique time series, which is higher than the suggested rouping. See https://grafana.com/docs/k
limit of 100000 and could cause high memory usage. Consider not using high-cardinality values like unique IDs, use the name metric tag or URL grouping. See https://grafana.com/docs/k6/latest/using-k6/tags-and-groups/ for details.  component=metrics-engine-ingester

WARN[0493] The test has generated metrics with 200035 unique time series, which is higher than the suggested limit of 100000 and could cause high memory usage. Consider not using high-cardinality values like unique IDs as metric tags or, if you need them in the URL, use the name metric tag or URL grouping. See https://grafana.com/docs/k6/latest/using-k6/tags-and-groups/ for details.  component=metrics-engine-ingester

WARN[0917] The test has generated metrics with 400006 unique time series, which is higher than the suggested limit of 100000 and could cause high memory usage. Consider not using high-cardinality v

════════════════════════════════════════════════════════
📊 РЕЗУЛЬТАТЫ СТРЕСС-ТЕСТИРОВАНИЯ
════════════════════════════════════════════════════════
⏱️  Длительность:           
- 1642.21s        # ADDED CLICKHOUSE INDEXES
- 1740.35s       
- 1740.23s   
- 1740.44s

👥 Максимальная нагрузка:   500 пользователей    

📤 Всего запросов:          
- 123905          # ADDED CLICKHOUSE INDEXES
- 110930
- 102821
- 138461

📈 RPS:                     
- 75.45           # ADDED CLICKHOUSE INDEXES
- 63.74         
- 59.084661
- 79.56                    

📊 Время ответа:                              
• Среднее: 
- 2703.58ms       # ADDED CLICKHOUSE INDEXES
- 3247.24ms
- 3541.18ms
- 2501.01ms

• 95%: 
- 8046.37ms       # ADDED CLICKHOUSE INDEXES
- 9627.86ms
- 7305.90ms    
- 5953.82ms

ERRO[1741] TypeError: Cannot read property 'toFixed' of undefined or null
running at handleSummary (file:///home/recommend/load_tests/k6_stress_test.js:74:70(129))  hint="script exception"

█ THRESHOLDS

http_req_duration
✓ 'p(95)<10000' p(95)=8.04s     # ADDED CLICKHOUSE INDEXES
✓ 'p(95)<10000' p(95)=9.62s 
- 5.95s
- 7.3s  

http_req_failed
✗ 'rate<0.20' rate=87.52%
✗ 'rate<0.20' rate=82.62% || 75.02% || 74.87% || 


█ TOTAL RESULTS

checks_total.......: 
- 123905 75.450015/s
- 110930                       
- 102821 59.084661/s

checks_succeeded...: 
- 50.19% 62196 out of 123905
- 69.81% 77445 out of 110930   
- 99.93% 102752 out of 102821
- 99.83% 138235 out of 138461

checks_failed......: 
- 49.80% 61709 out of 123905
- 30.18% 33485 out of 110930
- 0.06%  69 out of 102821
- 0.16%  226 out of 138461

✗ statistics status ok
↳  50% — ✓ 15745 / ✗ 15488
✗ 100 users list status ok
↳  49% — ✓ 15401 / ✗ 15447
✗ recommendations status ok
↳  50% — ✓ 31050 / ✗ 30774
---------------------------------
✗ recommendations status ok
↳  69% — ✓ 38918 / ✗ 16815
✗ statistics status ok
↳  69% — ✓ 19308 / ✗ 8313
✗ 100 users list status ok
↳  69% — ✓ 19219 / ✗ 8357
---------------------------------
✗ recommendations status ok
↳  99% — ✓ 51138 / ✗ 39       || ✓ 69258 / ✗ 127
✗ 100 users list status ok      
↳  99% — ✓ 25750 / ✗ 10       || ✓ 34475 / ✗ 57
✗ statistics status ok
↳  99% — ✓ 25864 / ✗ 20       || ✓ 34502 / ✗ 42

HTTP
http_req_duration..............: 
avg=2.7s  min=-4231ns  med=1.09s max=56.4s  p(90)=6.96s p(95)=8.04s
avg=3.24s min=11.51ms  med=2.46s max=40.33s p(90)=7.64s p(95)=9.62s
avg=3.54s min=10.86ms  med=3.51s max=32.87s p(90)=6.67s p(95)=7.3s
avg=2.5s  min=10.52ms  med=2.01s max=34.73s p(90)=5.23s p(95)=5.95s

{ expected_response:true }...: 
- avg=3.15s min=47.92µs  med=1.44s max=38.06s p(90)=7.12s p(95)=8.12s
- avg=3.95s min=17.53ms  med=3.57s max=40.33s p(90)=8.51s p(95)=10.46s
- avg=3.49s min=16.03ms  med=3.44s max=32.87s p(90)=6.59s p(95)=7.23s
- avg=2.42s min=15.8ms   med=1.9s  max=34.73s p(90)=5.12s p(95)=5.82s

http_req_failed................: 
- 87.52% 108452 out of 123905
- 82.62% 91657 out of 110930
- 74.87% 76989 out of 102821
- 75.02% 103883 out of 138461

http_reqs......................: 
- 123905 75.450015/s
- 110930 63.740061/s
- 102821 59.084661/s
- 138461 79.55533/s

EXECUTION
iteration_duration.............: 
avg=3.35s min=512.02ms med=1.65s max=1m0s    p(90)=7.77s p(95)=8.85s
avg=3.75s min=512.82ms med=2.97s max=40.83s  p(90)=8.15s p(95)=10.13s
avg=4.04s min=511.58ms med=4.01s max=33.37s  p(90)=7.17s p(95)=7.8s
avg=3s    min=511.26ms med=2.51s max=35.23s p(90)=5.74s  p(95)=6.45s

iterations.....................: 
- 123905 75.450015/s
- 110930
- 102821 || 
vus............................: 2      min=1               max=500
vus_max........................: 500    min=500             max=500

NETWORK
data_received..................: 
- 255 MB 155 kB/s
- 307 MB 176 kB/s
- 400 MB 230 kB/s     
- 536 MB 308 kB/s

data_sent......................:  
- 13 MB  7.7 kB/s
- 11 MB  6.5 kB/s
- 11 MB  6.0 kB/s
- 14 MB  8.1 kB/s

running (27m22.2s), 000/500 VUs, 123905 complete and 0 interrupted iterations
running (29m00.3s), 000/500 VUs, 110930 complete and 0 interrupted iterations
running (29m00.2s), 000/500 VUs, 102821 complete and 0 interrupted iterations

default ✓ [======================================] 000/500 VUs  29m0s
ERRO[1741] thresholds on metrics 'http_req_failed' have been crossed
```

