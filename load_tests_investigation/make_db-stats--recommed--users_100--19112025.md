# make db-stats 

```
📊 Статистика таблиц: 
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
    ┃ table                                          ┃ size      ┃ rows            ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
 1. │ .inner_id.35b47f70-dfea-4a32-8079-d435bdb6697e │ 7.25 MiB  │ 813.11 thousand │
    ├────────────────────────────────────────────────┼───────────┼─────────────────┤
 2. │ .inner_id.e5a7dd6b-e87c-4ac5-9271-053a9286133e │ 5.63 MiB  │ 776.27 thousand │
    ├────────────────────────────────────────────────┼───────────┼─────────────────┤
 3. │ popular_tracks                                 │ ᴺᵁᴸᴸ      │ ᴺᵁᴸᴸ            │
    ├────────────────────────────────────────────────┼───────────┼─────────────────┤
 4. │ similar_users                                  │ ᴺᵁᴸᴸ      │ ᴺᵁᴸᴸ            │
    ├────────────────────────────────────────────────┼───────────┼─────────────────┤
 5. │ track_statistics_mv                            │ 5.63 MiB  │ 776.27 thousand │
    ├────────────────────────────────────────────────┼───────────┼─────────────────┤
 6. │ tracks                                         │ 2.83 MiB  │ 50.00 thousand  │
    ├────────────────────────────────────────────────┼───────────┼─────────────────┤
 7. │ user_recommendations                           │ 0.00 B    │ 0.00            │
    ├────────────────────────────────────────────────┼───────────┼─────────────────┤
 8. │ user_statistics_mv                             │ 7.25 MiB  │ 813.11 thousand │
    ├────────────────────────────────────────────────┼───────────┼─────────────────┤
 9. │ user_track_interactions                        │ 11.04 MiB │ 850.00 thousand │
    ├────────────────────────────────────────────────┼───────────┼─────────────────┤
10. │ user_track_matrix                              │ 8.24 MiB  │ 849.92 thousand │
    ├────────────────────────────────────────────────┼───────────┼─────────────────┤
11. │ user_track_matrix_mv                           │ ᴺᵁᴸᴸ      │ ᴺᵁᴸᴸ            │
    ├────────────────────────────────────────────────┼───────────┼─────────────────┤
12. │ users                                          │ 3.18 MiB  │ 100.00 thousand │
    └────────────────────────────────────────────────┴───────────┴─────────────────┘
```



# k6 run load_tests/k6_diagnostics_test.js 

```
     execution: local
        script: load_tests/k6_diagnostics_test.js
        output: -

     scenarios: (100.00%) 1 scenario, 10 max VUs, 1m30s max duration (incl. graceful stop):
              * default: 10 looping VUs for 1m0s (gracefulStop: 30s)

INFO[0062]                                               				source=console
INFO[0062] ═══════════════════════════════════════════════════════════  source=console
INFO[0062]            🔍 ДИАГНОСТИКА ПРОИЗВОДИТЕЛЬНОСТИ                 source=console
INFO[0062] ═══════════════════════════════════════════════════════════  source=console
INFO[0062]                                               				source=console
INFO[0062] 📊 Общая статистика:                           				source=console
INFO[0062]    • Виртуальных пользователей: 10            	source=console
INFO[0062]    • Всего запросов:            1105          	source=console
INFO[0062]    • Общий процент ошибок:      0.00%         	source=console
INFO[0062]                                               	source=console
INFO[0062] 📈 Время ответа по эндпоинтам:                 		sourceource=console
INFO[0062]    📋 GET /users (list):                       		source=console
INFO[0062]       Среднее: 48ms | p95: 183ms | Max: 346ms  		source=console
INFO[0062]    🎵 GET /tracks (list):                      		source=console
INFO[0062]       Среднее: 46ms | p95: 161ms | Max: 294ms  		source=console
INFO[0062]    🎯 GET /recommendations (HEAVY):            		source=console
INFO[0062]       Среднее: 398ms | p95: 1158ms | Max: 1439ms  	source=console
INFO[0062]    👤 GET /users/{id}:                         		source=console
INFO[0062]       Среднее: 38ms | p95: 152ms              		source=console
INFO[0062]    🎵 GET /tracks/{id}:                        		source=console
INFO[0062]       Среднее: 30ms | p95: 95ms               		source=console
INFO[0062]                                               		source=console
INFO[0062] ❌ Ошибки по эндпоинтам:                     source=console
INFO[0062]    • Users List:        0                     source=console
INFO[0062]    • Tracks List:       0                     source=console
INFO[0062]    • Recommendations:   0                     source=console
INFO[0062]                                               source=console
INFO[0062] 🔍 АНАЛИЗ И РЕКОМЕНДАЦИИ:                    				source=console
INFO[0062]                                               				source=console
INFO[0062]    ✅ Хорошая производительность!            				source=console
INFO[0062]                                               				source=console
INFO[0062]    ⚠️  Рекомендации в 6.3x медленнее других endpoints  		source=console
INFO[0062]       • Это НОРМАЛЬНО - ML алгоритмы требуют времени  		source=console
INFO[0062]       • Убедитесь, что кэширование Redis работает  			source=console
INFO[0062]       • Повторные запросы должны быть ~50x быстрее (из кэша)  source=console
INFO[0062]                                               				source=console
INFO[0062] ═══════════════════════════════════════════════════════════  source=console
INFO[0062]                                               				source=console

running (1m02.2s), 00/10 VUs, 221 complete and 0 interrupted iterations
default ✓ [======================================] 10 VUs  1m0s

```



# k6 run load_tests/k6_smoke_test.js

```
     execution: local
        script: load_tests/k6_smoke_test.js
        output: -

     scenarios: (100.00%) 1 scenario, 3 max VUs, 40s max duration (incl. graceful stop):
              * default: 3 looping VUs for 10s (gracefulStop: 30s)

WARN[0000] Error from API server                         error="listen tcp 127.0.0.1:6565: bind: address already in use"
INFO[0010]                                               source=console
INFO[0010] ═══════════════════════════════════════════════════════════  source=console
INFO[0010]                🔥 SMOKE TEST ЗАВЕРШЁН                        source=console
INFO[0010] ═══════════════════════════════════════════════════════════  source=console
INFO[0010]                                               source=console
INFO[0010] 📊 Статистика:                                 source=console
INFO[0010]    • Всего запросов:        84                source=console
INFO[0010]    • Среднее время ответа:  22.45ms           source=console
INFO[0010]    • 95 перцентиль:         27.77ms           source=console
INFO[0010]    • Процент ошибок:        0.00%             source=console
INFO[0010]    • Успешные проверки:     100.00%           source=console
INFO[0010]                                               source=console
INFO[0010] ✅ PASSED: API работает нормально. Можно запускать полноценные тесты!  source=console
INFO[0010]                                               source=console
INFO[0010] ═══════════════════════════════════════════════════════════  source=console
INFO[0010]                                               source=console

running (10.7s), 0/3 VUs, 12 complete and 0 interrupted iterations
default ✓ [======================================] 3 VUs  10s

```



# k6 run load_tests/k6_spike_test.js

``` 

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/ 

     execution: local
        script: load_tests/k6_spike_test.js
        output: -

     scenarios: (100.00%) 1 scenario, 50 max VUs, 1m50s max duration (incl. graceful stop):
              * default: Up to 50 looping VUs for 1m20s over 5 stages (gracefulRampDown: 30s, gracefulStop: 30s)

WARN[0000] Error from API server                         error="listen tcp 127.0.0.1:6565: bind: address already in use"
INFO[0080]                                               source=console
INFO[0080] ═══════════════════════════════════════════════════════════  source=console
INFO[0080]             ⚡ SPIKE TEST ЗАВЕРШЁН                           source=console
INFO[0080] ═══════════════════════════════════════════════════════════  source=console
INFO[0080]                                               source=console
INFO[0080] 📊 Статистика:                                 source=console
INFO[0080]    • Пиковая нагрузка:      50 VUs            source=console
INFO[0080]    • Всего запросов:        1990              source=console
INFO[0080]    • Среднее время:         944.97ms          source=console
INFO[0080]    • 95 перцентиль:         3728.57ms         source=console
INFO[0080]    • 99 перцентиль:         0.00ms            source=console
INFO[0080]    • Процент ошибок:        0.00%             source=console
INFO[0080]                                               source=console
INFO[0080] ✅ PASSED: Система устойчива к пиковым нагрузкам!  							source=console
INFO[0080]                                               								source=console
INFO[0080] 💡 Spike test показывает, как система ведет себя при резком росте трафика.  	source=console
INFO[0080]    Небольшая деградация производительности - это нормально.  				source=console
INFO[0080]                                               								source=console
INFO[0080] ═══════════════════════════════════════════════════════════  source=console
INFO[0080]                                               								source=console

running (1m20.1s), 00/50 VUs, 1990 complete and 0 interrupted iterations
default ✓ [======================================] 00/50 VUs  1m20s

```





#  k6 run load_tests/k6_quick_performance_test.js 

```

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/ 

     execution: local
        script: load_tests/k6_quick_performance_test.js
        output: -

     scenarios: (100.00%) 1 scenario, 1 max VUs, 10m30s max duration (incl. graceful stop):
              * default: 10 iterations shared among 1 VUs (maxDuration: 10m0s, gracefulStop: 30s)

WARN[0000] Error from API server                         error="listen tcp 127.0.0.1:6565: bind: address already in use"
INFO[0000] User 83098: 🔍 fresh | Total: 221.7ms          source=console
INFO[0000] User 76913: 💾 cache | Total: 13.1ms           source=console
INFO[0000] User 64792: 🔍 fresh | Total: 222.0ms          source=console
INFO[0000] User 42470: 🔍 fresh | Total: 118.7ms          source=console
INFO[0000] User 48522: 🔍 fresh | Total: 227.1ms          source=console
INFO[0001] User 38276: 🔍 fresh | Total: 126.3ms          source=console
INFO[0001] User 23447: 🔍 fresh | Total: 110.0ms          source=console
INFO[0001] User 22185: 🔍 fresh | Total: 241.7ms          source=console
INFO[0001] User 65219: 🔍 fresh | Total: 166.9ms          source=console
INFO[0001] User 44033: 🔍 fresh | Total: 133.9ms          source=console
INFO[0001]
═══════════════════════════════════════════════════════════════════════════════  source=console
INFO[0001]   ⚡ БЫСТРЫЙ ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ РЕКОМЕНДАЦИЙ  source=console
INFO[0001] ═══════════════════════════════════════════════════════════════════════════════  source=console
INFO[0001] 📊 Обработано запросов: 10                     source=console
INFO[0001] ───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0001] 💾 КЭШ:                                        source=console
INFO[0001]    • Попадания в кэш:  1                      source=console
INFO[0001]    • Промахи кэша:     9                      source=console
INFO[0001]    • Hit Rate:         10.0%                  source=console
INFO[0001]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0001] ⏱️  СРЕДНЕЕ ВРЕМЯ ВЫПОЛНЕНИЯ:                 source=console
INFO[0001]    Redis:                                     source=console
INFO[0001]       • Проверка кэша:              2.17ms    source=console
INFO[0001]       • Сохранение:                 3.01ms    source=console
INFO[0001]       • ИТОГО Redis:                5.18ms    source=console
INFO[0001]
   ClickHouse:                               source=console
INFO[0001]       • Проверка пользователя:      11.33ms   source=console
INFO[0001]       • Подсчет взаимодействий:     15.34ms   source=console
INFO[0001]       • Поиск похожих польз.:       43.12ms   source=console
INFO[0001]       • Получение рекомендаций:     109.05ms  source=console
INFO[0001]       • ИТОГО ClickHouse:           178.85ms  source=console
INFO[0001]
   Алгоритм:                                 source=console
INFO[0001]       • Обработка результатов:      0.86ms    source=console
INFO[0001]
   📊 ОБЩЕЕ ВРЕМЯ:                            source=console
INFO[0001]       • Total Response Time:        158.14ms  source=console
INFO[0001]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0001] 📈 РАСПРЕДЕЛЕНИЕ ВРЕМЕНИ:                      source=console
INFO[0001]    • Redis:            3.3%  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  source=console
INFO[0001]    • ClickHouse:       113.1%  ███████████████████████████████████████  source=console
INFO[0001]    • Алгоритм:         0.5%  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  source=console
INFO[0001]    • Прочее:           0.0%  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  source=console
INFO[0001]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0001] 📊 СТАТИСТИКА:                                 source=console
INFO[0001]    • Успешных запросов:          20           source=console
INFO[0001]    • Ошибок:                     0            source=console
INFO[0001]    • Среднее время HTTP:         161.18ms     source=console
INFO[0001]    • p95 HTTP:                   238.15ms     source=console
INFO[0001]
═══════════════════════════════════════════════════════════════════════════════  source=console

running (00m01.6s), 0/1 VUs, 10 complete and 0 interrupted iterations
default ✓ [======================================] 1 VUs  00m01.6s/10m0s  10/10 shared iters

```



# k6 run load_tests/k6_recommendations_performance_test.js

```
     scenarios: (100.00%) 3 scenarios, 50 max VUs, 5m30s max duration (incl. graceful stop):
              * cold_cache: 10 looping VUs for 30s (gracefulStop: 30s)
              * warm_cache: 20 looping VUs for 1m0s (startTime: 1m0s, gracefulStop: 30s)
              * load_test: Up to 50 looping VUs for 2m0s over 3 stages (gracefulRampDown: 30s, startTime: 3m0s, gracefulStop: 30s)

WARN[0000] Error from API server                         error="listen tcp 127.0.0.1:6565: bind: address already in use"

INFO[0305]
═══════════════════════════════════════════════════════════════════════════════  source=console
INFO[0305]   📊 ДЕТАЛЬНЫЙ АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ РЕКОМЕНДАЦИЙ  source=console
INFO[0305] ═══════════════════════════════════════════════════════════════════════════════  source=console
INFO[0305] 📊 Общая статистика:                           source=console
INFO[0305]    • Длительность теста:    5m 5s             source=console
INFO[0305]    • Виртуальных юзеров:    50                source=console
INFO[0305]    • Всего запросов:        1454              source=console
INFO[0305]    • RPS (req/sec):         4.76              source=console
INFO[0305]    • Процент ошибок:        0.96%             source=console
INFO[0305]                                               source=console
INFO[0305] ⏱️  Время ответа:                             source=console
INFO[0305]    • Минимум:               3ms               source=console
INFO[0305]    • Среднее:               2861ms            source=console
INFO[0305]    • Медиана:               2349ms            source=console
INFO[0305]    • 95 перцентиль:         8142ms            source=console
INFO[0305]    • 99 перцентиль:         0ms               source=console
INFO[0305]    • Максимум:              24718ms           source=console
INFO[0305]                                               source=console
INFO[0305] ───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0305] 💾 СТАТИСТИКА КЭША (Redis):                    source=console
INFO[0305]    • Попадания в кэш:         154             source=console
INFO[0305]    • Промахи кэша:            1286            source=console
INFO[0305]    • Hit Rate:                10.69%          source=console
INFO[0305]                                               source=console
INFO[0305]    Redis - проверка кэша:                     source=console
INFO[0305]       avg: 74.94ms | med: 18.04ms | p95: 350.40ms | p99: 0.00ms  source=console
INFO[0305]       min: 0.51ms | max: 2273.09ms            source=console
INFO[0305]    Redis - сохранение:                        source=console
INFO[0305]       avg: 84.78ms | med: 15.07ms | p95: 388.98ms | p99: 0.00ms  source=console
INFO[0305]       min: 1.08ms | max: 2274.14ms            source=console
INFO[0305]    Redis - ИТОГО:                             source=console
INFO[0305]       avg: 150.65ms | med: 52.32ms | p95: 590.47ms | p99: 0.00ms  source=console
INFO[0305]       min: 0.81ms | max: 2341.74ms            source=console
INFO[0305]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0305] 🗄️  СТАТИСТИКА CLICKHOUSE:                     source=console
INFO[0305]    Проверка пользователя:                     source=console
INFO[0305]       avg: 238.62ms | med: 159.46ms | p95: 702.79ms | p99: 0.00ms  source=console
INFO[0305]       min: 6.19ms | max: 2895.19ms            source=console
INFO[0305]    Подсчет взаимодействий:                    source=console
INFO[0305]       avg: 341.49ms | med: 252.68ms | p95: 943.44ms | p99: 0.00ms  source=console
INFO[0305]       min: 7.99ms | max: 3562.23ms            source=console
INFO[0305]    Поиск похожих польз.:                      source=console
INFO[0305]       avg: 956.17ms | med: 755.88ms | p95: 2466.59ms | p99: 0.00ms  source=console
INFO[0305]       min: 27.20ms | max: 6187.51ms           source=console
INFO[0305]    Получение рекомендаций:                    source=console
INFO[0305]       avg: 1514.63ms | med: 1191.65ms | p95: 4118.77ms | p99: 0.00ms  source=console
INFO[0305]       min: 51.71ms | max: 22476.64ms          source=console
INFO[0305]    ClickHouse - ИТОГО:                        source=console
INFO[0305]       avg: 2981.02ms | med: 2418.56ms | p95: 8065.07ms | p99: 0.00ms  source=console
INFO[0305]       min: 100.56ms | max: 23906.70ms         source=console
INFO[0305]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0305] 🧮 СТАТИСТИКА АЛГОРИТМА:                        source=console
INFO[0305]    Обработка результатов:                     source=console
INFO[0305]       avg: 1.53ms | med: 0.62ms | p95: 5.97ms | p99: 0.00ms  source=console
INFO[0305]       min: 0.27ms | max: 32.91ms              source=console
INFO[0305]
   • Похожих пользователей (среднее): 49.8   source=console
INFO[0305]    • Похожих пользователей (мин):     31      source=console
INFO[0305]    • Похожих пользователей (макс):    50      source=console
INFO[0305]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0305] ⏱️  ОБЩЕЕ ВРЕМЯ ОТВЕТА:                       source=console
INFO[0305]    Total Response Time:                       source=console
INFO[0305]       avg: 2814.71ms | med: 2298.95ms | p95: 8084.57ms | p99: 0.00ms  source=console
INFO[0305]       min: 0.88ms | max: 24662.45ms           source=console
INFO[0305]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0305] 📈 АНАЛИЗ РАСПРЕДЕЛЕНИЯ ВРЕМЕНИ (среднее):     source=console
INFO[0305]    • Redis:                   150.65ms (5.4%)  source=console
INFO[0305]    • ClickHouse:              2981.02ms (105.9%)  source=console
INFO[0305]    • Алгоритм:                1.53ms (0.1%)   source=console
INFO[0305]    • Прочее (сеть, FastAPI):  -318.49ms (-11.3%)  source=console
INFO[0305]    • ИТОГО:                   2814.71ms (100.0%)  source=console
INFO[0305]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0305] 💡 РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ:                source=console
INFO[0305]    ⚠️  Низкий Hit Rate кэша (<30%). Рассмотрите увеличение TTL или предварительный прогрев кэша.  source=console
INFO[0305]    ⚠️  Redis работает медленно (>50ms). Проверьте сетевую задержку или нагрузку на Redis.  source=console
INFO[0305]    ⚠️  ClickHouse запросы медленные (>2000ms). Рассмотрите оптимизацию запросов или добавление индексов.  source=console
INFO[0305]    ⚠️  Получение рекомендаций медленное (>1500ms). Рассмотрите материализованные представления или денормализацию.  source=console
INFO[0305]
═══════════════════════════════════════════════════════════════════════════════  source=console

running (5m05.3s), 00/50 VUs, 1454 complete and 0 interrupted iterations
cold_cache ✓ [======================================] 10 VUs     30s
warm_cache ✓ [======================================] 20 VUs     1m0s
load_test  ✓ [======================================] 00/50 VUs  2m0s

```





# [ERROR] k6 run load_tests/k6_stress_test.js 

running (23m14.8s), 424/500 VUs, 17484 complete and 0 interrupted iterations (Ctrl + C)
---------------------------------------------------------------------------------------

WARN[0000] Error from API server                         error="listen tcp 127.0.0.1:6565: bind: address already in use"
---------------------------------------------------------------------------------------

WARN[0890] The test has generated metrics with 100_018 unique time series, which is higher than the suggested limit of 100_000 and could cause high memory usage. 
Consider not using high-cardinality values like unique IDs as metric tags or, if you need them in the URL, use the name metric tag or URL grouping. 
See https://grafana.com/docs/k6/latest/using-k6/tags-and-groups/ for details.  component=metrics-engine-ingester
-------------------------------------------------------------------------------------------

WARN[1238] Request Failed                                error="Get \"http://localhost:8000/api/v1/recommendations/3154\": request timeout"
----------------------------------------------------------------------------------------------


```ERROR
         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: load_tests/k6_stress_test.js
        output: -

     scenarios: (100.00%) 1 scenario, 500 max VUs, 29m30s max duration (incl. graceful stop):
              * default: Up to 500 looping VUs for 29m0s over 7 stages (gracefulRampDown: 30s, gracefulStop: 30s)

WARN[0000] Error from API server                         error="listen tcp 127.0.0.1:6565: bind: address already in use"

WARN[0890] The test has generated metrics with 100_018 unique time series, which is higher than the suggested limit of 100_000 and could cause high memory usage. 
Consider not using high-cardinality values like unique IDs as metric tags or, if you need them in the URL, use the name metric tag or URL grouping. 
See https://grafana.com/docs/k6/latest/using-k6/tags-and-groups/ for details.  component=metrics-engine-ingester


WARN[1238] Request Failed                                error="Get \"http://localhost:8000/api/v1/recommendations/3154\": request timeout"
....
WARN[1347] Request Failed                                error="Get \"http://localhost:8000/api/v1/recommendations/15038\": request timeout"
WARN[1347] Request Failed                                error="Get \"http://localhost:8000/api/v1/recommendations/92778\": request timeout"
WARN[1347] Request Failed                                error="Get \"http://localhost:8000/api/v1/recommendations/65579\": request timeout"
WARN[1347] Request Failed                                error="Get \"http://localhost:8000/api/v1/recommendations/30937\": request timeout"
WARN[1347] Request Failed                                error="Get \"http://localhost:8000/api/v1/recommendations/34168\": request timeout"
WARN[1347] Request Failed                                error="Get \"http://localhost:8000/api/v1/recommendations/57652\": request timeout"

...

running (23m14.8s), 424/500 VUs, 17484 complete and 0 interrupted iterations
default   [=============================>--------] 424/500 VUs  23m14.8s/29m00.0s

```
