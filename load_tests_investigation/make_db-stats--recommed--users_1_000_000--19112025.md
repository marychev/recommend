# make db-stats 

```
📊 Статистика таблиц: 
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
    ┃ table                                          ┃ size      ┃ rows             ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
 1. │ .inner_id.73d6a436-1664-4c67-a25f-d0280546eac4 │ 8.85 MiB  │ 965.43 thousand  │
    ├────────────────────────────────────────────────┼───────────┼──────────────────┤
 2. │ .inner_id.7dfa226f-0ac6-40fb-bf53-b8dd18b1c4ed │ 8.59 MiB  │ 992.35 thousand  │
    ├────────────────────────────────────────────────┼───────────┼──────────────────┤
 3. │ popular_tracks                                 │ ᴺᵁᴸᴸ      │ ᴺᵁᴸᴸ             │
    ├────────────────────────────────────────────────┼───────────┼──────────────────┤
 4. │ similar_users                                  │ ᴺᵁᴸᴸ      │ ᴺᵁᴸᴸ             │
    ├────────────────────────────────────────────────┼───────────┼──────────────────┤
 5. │ track_statistics_mv                            │ 8.59 MiB  │ 992.35 thousand  │
    ├────────────────────────────────────────────────┼───────────┼──────────────────┤
 6. │ tracks                                         │ 11.62 MiB │ 500.00 thousand  │
    ├────────────────────────────────────────────────┼───────────┼──────────────────┤
 7. │ user_recommendations                           │ 0.00 B    │ 0.00             │
    ├────────────────────────────────────────────────┼───────────┼──────────────────┤
 8. │ user_statistics_mv                             │ 8.85 MiB  │ 965.43 thousand  │
    ├────────────────────────────────────────────────┼───────────┼──────────────────┤
 9. │ user_track_interactions                        │ 13.80 MiB │ 1.00 million     │
    ├────────────────────────────────────────────────┼───────────┼──────────────────┤
10. │ user_track_matrix                              │ 10.04 MiB │ 1000.00 thousand │
    ├────────────────────────────────────────────────┼───────────┼──────────────────┤
11. │ user_track_matrix_mv                           │ ᴺᵁᴸᴸ      │ ᴺᵁᴸᴸ             │
    ├────────────────────────────────────────────────┼───────────┼──────────────────┤
12. │ users                                          │ 6.19 MiB  │ 300.00 thousand  │
    └────────────────────────────────────────────────┴───────────┴──────────────────┘
```




# k6 run load_tests/k6_diagnostics_test.js 

```
     execution: local
        script: load_tests/k6_diagnostics_test.js
        output: -

     scenarios: (100.00%) 1 scenario, 10 max VUs, 1m30s max duration (incl. graceful stop):
              * default: 10 looping VUs for 1m0s (gracefulStop: 30s)

WARN[0000] Error from API server                         error="listen tcp 127.0.0.1:6565: bind: address already in use"
INFO[0061]                                               source=console
INFO[0061] ═══════════════════════════════════════════════════════════  source=console
INFO[0061]            🔍 ДИАГНОСТИКА ПРОИЗВОДИТЕЛЬНОСТИ                 source=console
INFO[0061] ═══════════════════════════════════════════════════════════  source=console
INFO[0061]                                               source=console
INFO[0061] 📊 Общая статистика:                           source=console
INFO[0061]    • Виртуальных пользователей: 10            source=console
INFO[0061]    • Всего запросов:            1255          source=console
INFO[0061]    • Общий процент ошибок:      59.76%        source=console
INFO[0061]                                               source=console
INFO[0061] 📈 Время ответа по эндпоинтам:                 source=console
INFO[0061]    📋 GET /users (list):                       source=console
INFO[0061]       Среднее: 48ms | p95: 124ms | Max: 156ms  source=console
INFO[0061]    🎵 GET /tracks (list):                      source=console
INFO[0061]       Среднее: 50ms | p95: 139ms | Max: 184ms  source=console
INFO[0061]    🎯 GET /recommendations (HEAVY):            source=console
INFO[0061]       Среднее: 48ms | p95: 105ms | Max: 134ms  source=console
INFO[0061]    👤 GET /users/{id}:                         source=console
INFO[0061]       Среднее: 43ms | p95: 81ms               source=console
INFO[0061]    🎵 GET /tracks/{id}:                        source=console
INFO[0061]       Среднее: 35ms | p95: 68ms               source=console
INFO[0061]                                               source=console
INFO[0061] ❌ Ошибки по эндпоинтам:                       source=console
INFO[0061]    • Users List:        0                     source=console
INFO[0061]    • Tracks List:       0                     source=console
INFO[0061]    • Recommendations:   0                     source=console
INFO[0061]                                               source=console
INFO[0061] 🔍 АНАЛИЗ И РЕКОМЕНДАЦИИ:                      source=console
INFO[0061]                                               source=console
INFO[0061]    ✅ Хорошая производительность!              source=console
INFO[0061]                                               source=console
INFO[0061]    ❌ Высокий процент ошибок (59.76%)          source=console
INFO[0061]       1. Проверьте логи: make logs-errors     source=console
INFO[0061]       2. Проверьте подключение к БД           source=console
INFO[0061]       3. Проверьте, что данные сгенерированы: make db-stats  source=console
INFO[0061]                                               source=console
INFO[0061] ═══════════════════════════════════════════════════════════  source=console
INFO[0061]                                               source=console

running (1m01.9s), 00/10 VUs, 251 complete and 0 interrupted iterations
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
INFO[0011]                                               source=console
INFO[0011] ═══════════════════════════════════════════════════════════  source=console
INFO[0011]                🔥 SMOKE TEST ЗАВЕРШЁН                        source=console
INFO[0011] ═══════════════════════════════════════════════════════════  source=console
INFO[0011]                                               source=console
INFO[0011] 📊 Статистика:                                 source=console
INFO[0011]    • Всего запросов:        63                source=console
INFO[0011]    • Среднее время ответа:  188.43ms          source=console
INFO[0011]    • 95 перцентиль:         83.55ms           source=console
INFO[0011]    • Процент ошибок:        0.00%             source=console
INFO[0011]    • Успешные проверки:     100.00%           source=console
INFO[0011]                                               source=console
INFO[0011] ✅ PASSED: API работает нормально. Можно запускать полноценные тесты!  source=console
INFO[0011]                                               source=console
INFO[0011] ═══════════════════════════════════════════════════════════  source=console
INFO[0011]                                               source=console

running (11.5s), 0/3 VUs, 9 complete and 0 interrupted iterations
default ✓ [======================================] 3 VUs  10s

```



# [ERROR] k6 run load_tests/k6_spike_test.js

```
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
INFO[0080]    • Всего запросов:        4465              source=console
INFO[0080]    • Среднее время:         240.12ms          source=console
INFO[0080]    • 95 перцентиль:         665.08ms          source=console
INFO[0080]    • 99 перцентиль:         0.00ms            source=console
INFO[0080]    • Процент ошибок:        59.08%            source=console
INFO[0080]                                               source=console
INFO[0080] ❌ FAILED: Слишком много ошибок при пиковой нагрузке. Требуется оптимизация!  source=console

INFO[0080] 💡 Spike test показывает, как система ведет себя при резком росте трафика.  source=console
INFO[0080]    Небольшая деградация производительности - это нормально.  source=console
INFO[0080]                                               source=console
INFO[0080] ═══════════════════════════════════════════════════════════  source=console
INFO[0080]                                               source=console

running (1m20.3s), 00/50 VUs, 4465 complete and 0 interrupted iterations
default ✓ [======================================] 00/50 VUs  1m20s

ERRO[0080] thresholds on metrics 'http_req_failed' have been crossed

```



#  k6 run load_tests/k6_quick_performance_test.js 

```
     execution: local
        script: load_tests/k6_quick_performance_test.js
        output: -

     scenarios: (100.00%) 1 scenario, 1 max VUs, 10m30s max duration (incl. graceful stop):
              * default: 10 iterations shared among 1 VUs (maxDuration: 10m0s, gracefulStop: 30s)

WARN[0000] Error from API server                         error="listen tcp 127.0.0.1:6565: bind: address already in use"
INFO[0000] User 66132174: ❌ Error 404                    source=console
INFO[0000] User 4687223: ❌ Error 404                     source=console
INFO[0000] User 1511442: ❌ Error 404                     source=console
INFO[0000] User 48279227: ❌ Error 404                    source=console
INFO[0000] User 69739721: ❌ Error 404                    source=console
INFO[0000] User 60746070: ❌ Error 404                    source=console
INFO[0000] User 44678808: ❌ Error 404                    source=console
INFO[0000] User 82732675: ❌ Error 404                    source=console
INFO[0000] User 20641414: ❌ Error 404                    source=console
INFO[0000] User 29612953: ❌ Error 404                    source=console
INFO[0000]
═══════════════════════════════════════════════════════════════════════════════  source=console
INFO[0000]   ⚡ БЫСТРЫЙ ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ РЕКОМЕНДАЦИЙ  source=console
INFO[0000] ═══════════════════════════════════════════════════════════════════════════════  source=console
INFO[0000] 📊 Обработано запросов: 10                     source=console
INFO[0000] ───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0000] 💾 КЭШ:                                        source=console
INFO[0000]    • Попадания в кэш:  0                      source=console
INFO[0000]    • Промахи кэша:     0                      source=console
INFO[0000]    • Hit Rate:         0%                     source=console
INFO[0000]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0000] ⏱️  СРЕДНЕЕ ВРЕМЯ ВЫПОЛНЕНИЯ:                 source=console
INFO[0000]    Redis:                                     source=console
INFO[0000]       • Проверка кэша:              0.00ms    source=console
INFO[0000]       • Сохранение:                 0.00ms    source=console
INFO[0000]       • ИТОГО Redis:                0.00ms    source=console
INFO[0000]
   ClickHouse:                               source=console
INFO[0000]       • Проверка пользователя:      0.00ms    source=console
INFO[0000]       • Подсчет взаимодействий:     0.00ms    source=console
INFO[0000]       • Поиск похожих польз.:       0.00ms    source=console
INFO[0000]       • Получение рекомендаций:     0.00ms    source=console
INFO[0000]       • ИТОГО ClickHouse:           0.00ms    source=console
INFO[0000]
   Алгоритм:                                 source=console
INFO[0000]       • Обработка результатов:      0.00ms    source=console
INFO[0000]
   📊 ОБЩЕЕ ВРЕМЯ:                            source=console
INFO[0000]       • Total Response Time:        0.00ms    source=console
INFO[0000]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0000] 📈 РАСПРЕДЕЛЕНИЕ ВРЕМЕНИ:                      source=console
INFO[0000]    • Redis:            0.0%  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  source=console
INFO[0000]    • ClickHouse:       0.0%  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  source=console
INFO[0000]    • Алгоритм:         0.0%  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  source=console
INFO[0000]    • Прочее:           100.0%  ███████████████████████████████████████  source=console
INFO[0000]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0000] 📊 СТАТИСТИКА:                                 source=console
INFO[0000]    • Успешных запросов:          0            source=console
INFO[0000]    • Ошибок:                     20           source=console
INFO[0000]    • Среднее время HTTP:         45.79ms      source=console
INFO[0000]    • p95 HTTP:                   127.97ms     source=console
INFO[0000]
═══════════════════════════════════════════════════════════════════════════════  source=console

running (00m00.5s), 0/1 VUs, 10 complete and 0 interrupted iterations
default ✓ [======================================] 1 VUs  00m00.5s/10m0s  10/10 shared iters

```




# k6 run load_tests/k6_recommendations_performance_test.js

```
     scenarios: (100.00%) 3 scenarios, 50 max VUs, 5m30s max duration (incl. graceful stop):
              * cold_cache: 10 looping VUs for 30s (gracefulStop: 30s)
              * warm_cache: 20 looping VUs for 1m0s (startTime: 1m0s, gracefulStop: 30s)
              * load_test: Up to 50 looping VUs for 2m0s over 3 stages (gracefulRampDown: 30s, startTime: 3m0s, gracefulStop: 30s)

WARN[0000] Error from API server                         error="listen tcp 127.0.0.1:6565: bind: address already in use"
INFO[0301]
═══════════════════════════════════════════════════════════════════════════════  source=console
INFO[0301]   📊 ДЕТАЛЬНЫЙ АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ РЕКОМЕНДАЦИЙ  source=console
INFO[0301] ═══════════════════════════════════════════════════════════════════════════════  source=console
INFO[0301] 📊 Общая статистика:                           source=console
INFO[0301]    • Длительность теста:    5m 0s             source=console
INFO[0301]    • Виртуальных юзеров:    50                source=console
INFO[0301]    • Всего запросов:        5205              source=console
INFO[0301]    • RPS (req/sec):         17.29             source=console
INFO[0301]    • Процент ошибок:        99.90%            source=console
INFO[0301]                                               source=console
INFO[0301] ⏱️  Время ответа:                             source=console
INFO[0301]    • Минимум:               11ms              source=console
INFO[0301]    • Среднее:               38ms              source=console
INFO[0301]    • Медиана:               18ms              source=console
INFO[0301]    • 95 перцентиль:         135ms             source=console
INFO[0301]    • 99 перцентиль:         0ms               source=console
INFO[0301]    • Максимум:              2754ms            source=console
INFO[0301]                                               source=console
INFO[0301] ───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0301] 💾 СТАТИСТИКА КЭША (Redis):                    source=console
INFO[0301]    • Попадания в кэш:         0               source=console
INFO[0301]    • Промахи кэша:            5               source=console
INFO[0301]    • Hit Rate:                0.00%           source=console
INFO[0301]                                               source=console
INFO[0301]    Redis - проверка кэша:                     source=console
INFO[0301]       avg: 3.63ms | med: 1.84ms | p95: 8.38ms | p99: 0.00ms  source=console
INFO[0301]       min: 0.55ms | max: 9.25ms               source=console
INFO[0301]    Redis - сохранение:                        source=console
INFO[0301]       avg: 7.52ms | med: 7.01ms | p95: 12.70ms | p99: 0.00ms  source=console
INFO[0301]       min: 3.47ms | max: 13.93ms              source=console
INFO[0301]    Redis - ИТОГО:                             source=console
INFO[0301]       avg: 11.14ms | med: 8.61ms | p95: 21.07ms | p99: 0.00ms  source=console
INFO[0301]       min: 4.02ms | max: 23.18ms              source=console
INFO[0301]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0301] 🗄️  СТАТИСТИКА CLICKHOUSE:                     source=console
INFO[0301]    Проверка пользователя:                     source=console
INFO[0301]       avg: 51.03ms | med: 35.18ms | p95: 114.30ms | p99: 0.00ms  source=console
INFO[0301]       min: 16.08ms | max: 131.23ms            source=console
INFO[0301]    Подсчет взаимодействий:                    source=console
INFO[0301]       avg: 124.36ms | med: 38.80ms | p95: 346.81ms | p99: 0.00ms  source=console
INFO[0301]       min: 24.36ms | max: 400.16ms            source=console
INFO[0301]    Поиск похожих польз.:                      source=console
INFO[0301]       avg: 231.81ms | med: 143.98ms | p95: 488.95ms | p99: 0.00ms  source=console
INFO[0301]       min: 54.85ms | max: 522.82ms            source=console
INFO[0301]    Получение рекомендаций:                    source=console
INFO[0301]       avg: 757.93ms | med: 490.06ms | p95: 1540.38ms | p99: 0.00ms  source=console
INFO[0301]       min: 153.58ms | max: 1654.74ms          source=console
INFO[0301]    ClickHouse - ИТОГО:                        source=console
INFO[0301]       avg: 1165.13ms | med: 930.37ms | p95: 2426.88ms | p99: 0.00ms  source=console
INFO[0301]       min: 302.43ms | max: 2708.96ms          source=console
INFO[0301]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0301] 🧮 СТАТИСТИКА АЛГОРИТМА:                        source=console
INFO[0301]    Обработка результатов:                     source=console
INFO[0301]       avg: 3.00ms | med: 0.53ms | p95: 9.22ms | p99: 0.00ms  source=console
INFO[0301]       min: 0.39ms | max: 10.82ms              source=console
INFO[0301]
   • Похожих пользователей (среднее): 10.0   source=console
INFO[0301]    • Похожих пользователей (мин):     6       source=console
INFO[0301]    • Похожих пользователей (макс):    14      source=console
INFO[0301]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0301] ⏱️  ОБЩЕЕ ВРЕМЯ ОТВЕТА:                       source=console
INFO[0301]    Total Response Time:                       source=console
INFO[0301]       avg: 1179.78ms | med: 943.75ms | p95: 2456.45ms | p99: 0.00ms  source=console
INFO[0301]       min: 313.70ms | max: 2743.56ms          source=console
INFO[0301]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0301] 📈 АНАЛИЗ РАСПРЕДЕЛЕНИЯ ВРЕМЕНИ (среднее):     source=console
INFO[0301]    • Redis:                   11.14ms (0.9%)  source=console
INFO[0301]    • ClickHouse:              1165.13ms (98.8%)  source=console
INFO[0301]    • Алгоритм:                3.00ms (0.3%)   source=console
INFO[0301]    • Прочее (сеть, FastAPI):  0.51ms (0.0%)   source=console
INFO[0301]    • ИТОГО:                   1179.78ms (100.0%)  source=console
INFO[0301]
───────────────────────────────────────────────────────────────────────────────  source=console
INFO[0301] 💡 РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ:                source=console
INFO[0301]    ⚠️  Низкий Hit Rate кэша (<30%). Рассмотрите увеличение TTL или предварительный прогрев кэша.  source=console
INFO[0301]
═══════════════════════════════════════════════════════════════════════════════  source=console

running (5m01.0s), 00/50 VUs, 5205 complete and 0 interrupted iterations
cold_cache ✓ [======================================] 10 VUs     30s
warm_cache ✓ [======================================] 20 VUs     1m0s
load_test  ✓ [======================================] 00/50 VUs  2m0s

ERRO[0301] thresholds on metrics 'cache_hit_rate, errors, http_req_failed, success' have been crossed
```





# [ERROR] k6 run load_tests/k6_stress_test.js 

```
     scenarios: (100.00%) 1 scenario, 500 max VUs, 29m30s max duration (incl. graceful stop):
              * default: Up to 500 looping VUs for 29m0s over 7 stages (gracefulRampDown: 30s, gracefulStop: 30s)

WARN[0000] Error from API server                         error="listen tcp 127.0.0.1:6565: bind: address already in use"
WARN[0189] The test has generated metrics with 100036 unique time series, which is higher than the suggested limit of 100000 and could cause high memory usage. Consider not using high-cardinality values like unique IDs as metric tags or, if you need them in the URL, use the name metric tag or URL grouping. See https://grafana.com/docs/k6/latest/using-k6/tags-and-groups/ for details.  component=metrics-engine-ingester

WARN[0324] The test has generated metrics with 200008 unique time series, which is higher than the suggested limit of 100000 and could cause high memory usage. Consider not using high-cardinality values like unique IDs as metric tags or, if you need them in the URL, use the name metric tag or URL grouping. See https://grafana.com/docs/k6/latest/using-k6/tags-and-groups/ for details.  component=metrics-engine-ingester

WARN[0634] The test has generated metrics with 400123 unique time series, which is higher than the suggested limit of 100000 and could cause high memory usage. Consider not using high-cardinality values like unique IDs as metric tags or, if you need them in the URL, use the name metric tag or URL grouping. See https://grafana.com/docs/k6/latest/using-k6/tags-and-groups/ for details.  component=metrics-engine-ingester

WARN[1292] The test has generated metrics with 800029 unique time series, which is higher than the suggested limit of 100000 and could cause high memory usage. Consider not using high-cardinality values like unique IDs as metric tags or, if you need them in the URL, use the name metric tag or URL grouping. See https://grafana.com/docs/k6/latest/using-k6/tags-and-groups/ for details.  component=metrics-engine-ingester

╔════════════════════════════════════════════════════╗  source=console
INFO[1740] ║        📊 РЕЗУЛЬТАТЫ СТРЕСС-ТЕСТИРОВАНИЯ         ║  source=console
INFO[1740] ╚════════════════════════════════════════════════════╝  source=console
INFO[1741] ⏱️  Длительность: 1740.44s                    source=console
INFO[1741] 👥 Максимальная нагрузка: 500 пользователей    source=console
INFO[1741] 📤 Всего запросов: 138461                      source=console
INFO[1741] 📈 RPS: 79.56                                  source=console
INFO[1741]
📊 Время ответа:                              source=console
INFO[1741]    • Среднее: 2501.01ms                       source=console
INFO[1741]    • 95%: 5953.82ms                           source=console
ERRO[1741] TypeError: Cannot read property 'toFixed' of undefined or null
running at handleSummary (file:///home/recommend/load_tests/k6_stress_test.js:74:70(129))  hint="script exception"


  █ THRESHOLDS

    http_req_duration
    ✓ 'p(95)<10000' p(95)=5.95s

    http_req_failed
    ✗ 'rate<0.20' rate=75.02%


  █ TOTAL RESULTS

    checks_total.......: 138461 79.55533/s
    checks_succeeded...: 99.83% 138235 out of 138461
    checks_failed......: 0.16%  226 out of 138461

    ✗ recommendations status ok
      ↳  99% — ✓ 69258 / ✗ 127
    ✗ 100 users list status ok
      ↳  99% — ✓ 34475 / ✗ 57
    ✗ statistics status ok
      ↳  99% — ✓ 34502 / ✗ 42

    CUSTOM
    requests.......................: 138461 79.55533/s

    HTTP
    http_req_duration..............: avg=2.5s  min=10.52ms  med=2.01s max=34.73s p(90)=5.23s p(95)=5.95s
      { expected_response:true }...: avg=2.42s min=15.8ms   med=1.9s  max=34.73s p(90)=5.12s p(95)=5.82s
    http_req_failed................: 75.02% 103883 out of 138461
    http_reqs......................: 138461 79.55533/s

    EXECUTION
    iteration_duration.............: avg=3s    min=511.26ms med=2.51s max=35.23s p(90)=5.74s p(95)=6.45s
    iterations.....................: 138461 79.55533/s
    vus............................: 2      min=1                max=500
    vus_max........................: 500    min=500              max=500

    NETWORK
    data_received..................: 536 MB 308 kB/s
    data_sent......................: 14 MB  8.1 kB/s


running (29m00.4s), 000/500 VUs, 138461 complete and 0 interrupted iterations
default ✓ [======================================] 000/500 VUs  29m0s

ERRO[1741] thresholds on metrics 'http_req_failed' have been crossed
```
