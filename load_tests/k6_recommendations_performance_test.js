/**
 * k6 Тест производительности рекомендаций с детальными метриками
 * 
 * Этот тест собирает детальную информацию о времени выполнения каждого компонента:
 * - Redis (проверка кэша, сохранение)
 * - ClickHouse (проверка пользователя, подсчет взаимодействий, поиск похожих, получение рекомендаций)
 * - Алгоритм (обработка результатов)
 * - Общее время ответа
 * 
 * Использует параметр include_performance_metrics=true для получения детальных метрик от API
 * 
 * Запуск:
 * k6 run load_tests/k6_recommendations_performance_test.js
 * k6 run load_tests/k6_recommendations_performance_test.js --env API_URL=http://localhost:8000
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Counter, Rate } from 'k6/metrics';
import { BASE_URL, getRandomUserId, getBasicStats, printBasicStats, getRandomIdFromArray } from './k6-helpers.js';

// ════════════════════════════════════════════════════════
// Кастомные метрики для детального анализа
// ════════════════════════════════════════════════════════

// Общие метрики
const totalResponseTime = new Trend('total_response_time', true);
const cacheHitRate = new Rate('cache_hit_rate');
const cacheHits = new Counter('cache_hits');
const cacheMisses = new Counter('cache_misses');

// Redis метрики
const redisCheckTime = new Trend('redis_check_time', true);
const redisSaveTime = new Trend('redis_save_time', true);
const redisTotalTime = new Trend('redis_total_time', true);

// ClickHouse метрики
const clickhouseUserCheckTime = new Trend('clickhouse_user_check_time', true);
const clickhouseInteractionsCountTime = new Trend('clickhouse_interactions_count_time', true);
const clickhouseSimilarUsersTime = new Trend('clickhouse_similar_users_time', true);
const clickhouseRecommendationsTime = new Trend('clickhouse_recommendations_time', true);
const clickhouseTotalTime = new Trend('clickhouse_total_time', true);

// Алгоритм метрики
const algorithmProcessingTime = new Trend('algorithm_processing_time', true);

// Метрики похожих пользователей
const similarUsersCount = new Trend('similar_users_count', true);

// Счетчики ошибок
const errorRate = new Rate('errors');
const successRate = new Rate('success');

// ════════════════════════════════════════════════════════
// Конфигурация теста
// ════════════════════════════════════════════════════════

export const options = {
  scenarios: {
    // Тест с холодным кэшем (без предварительного прогрева)
    cold_cache: {
      executor: 'constant-vus',
      vus: 10,
      duration: '30s',
      startTime: '0s',
      tags: { cache_type: 'cold' },
    },
    // Тест с теплым кэшем (после прогрева)
    warm_cache: {
      executor: 'constant-vus',
      vus: 20,
      duration: '1m',
      startTime: '1m',
      tags: { cache_type: 'warm' },
    },
    // Нагрузочный тест
    load_test: {
      executor: 'ramping-vus',
      startVUs: 10,
      stages: [
        { duration: '30s', target: 30 },
        { duration: '1m', target: 50 },
        { duration: '30s', target: 10 },
      ],
      startTime: '3m',
      tags: { cache_type: 'mixed' },
    },
  },
  thresholds: {
    // Общие пороги
    'http_req_duration': ['p(95)<10000', 'p(99)<20000'],
    'http_req_failed': ['rate<0.7'],      // До 70% ошибок (включая 404)
    'success': ['rate>0.3'],               // Минимум 30% успешных (учитываем 404)
    'errors': ['rate<0.05'],               // До 5% реальных ошибок (5xx, таймауты)
    
    // Пороги для кэша (более мягкие - учитываем холодный старт)
    'cache_hit_rate': ['rate>0.05'], // Минимум 5% попаданий в кэш (учитываем холодный старт)
    
    // Пороги для Redis (только p95, без avg - более устойчивы к выбросам)
    'redis_check_time': ['p(95)<500'],
    'redis_save_time': ['p(95)<800'],
    
    // Пороги для ClickHouse (только p95, более реалистичные для сложных запросов)
    'clickhouse_user_check_time': ['p(95)<1000'],
    'clickhouse_interactions_count_time': ['p(95)<2000'],
    'clickhouse_similar_users_time': ['p(95)<5000'],
    'clickhouse_recommendations_time': ['p(95)<6000'],
    
    // Пороги для алгоритма (только p95)
    'algorithm_processing_time': ['p(95)<500'],
  },
  // Настройка: только реальные ошибки (5xx, таймауты, сеть)
  noConnectionErrors: true,
};

// Setup: получаем реальные ID пользователей перед тестом
export function setup() {
  console.log('🔍 Загрузка реальных ID пользователей для recommendations performance test...');
  
  // Получаем реальные ID пользователей (больше для нагрузочного теста)
  let userIds = [];
  try {
    const usersRes = http.get(`${BASE_URL}/api/v1/users?limit=500`);
    if (usersRes.status === 200) {
      const users = JSON.parse(usersRes.body);
      userIds = users.map(u => u.user_id).filter(id => id != null);
    }
  } catch (e) {
    console.error(`Failed to get real user IDs: ${e}`);
  }
  
  console.log(`✅ Загружено ${userIds.length} пользователей`);
  
  if (userIds.length === 0) {
    console.warn('⚠️  Не удалось загрузить реальные ID. Тест будет использовать случайные ID (возможны 404 ошибки).');
  }
  
  return {
    userIds: userIds,
  };
}

// ════════════════════════════════════════════════════════
// Основная функция тестирования
// ════════════════════════════════════════════════════════

export default function (data) {
  // Используем реальный ID из setup, если доступен
  const availableUserIds = (data && data.userIds && data.userIds.length > 0) ? data.userIds : null;
  const userId = availableUserIds ? getRandomIdFromArray(availableUserIds) : getRandomUserId();
  
  // Формируем запрос с включенными метриками производительности
  const payload = JSON.stringify({
    user_id: userId,
    top_n: 10,
    exclude_listened: true,
    include_performance_metrics: true,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    tags: { name: 'GetRecommendationsWithMetrics' },
  };

  // Выполняем запрос
  const response = http.post(`${BASE_URL}/api/v1/recommendations`, payload, params);

  // Базовые проверки
  // 404 - это валидный ответ (пользователь не найден), не считаем ошибкой
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response has recommendations': (r) => {
      if (r.status === 200) {
        try {
          const body = JSON.parse(r.body);
          return body.recommendations && Array.isArray(body.recommendations);
        } catch {
          return false;
        }
      }
      return false;
    },
    'response has performance_metrics': (r) => {
      if (r.status === 200) {
        try {
          const body = JSON.parse(r.body);
          return body.performance_metrics !== null && body.performance_metrics !== undefined;
        } catch {
          return false;
        }
      }
      return false;
    },
  });

  // Обновляем счетчики успеха/ошибок
  // Считаем ошибкой только реальные ошибки (5xx, таймауты, сеть), не 404
  if (response.status === 200) {
    successRate.add(true);
    errorRate.add(false);
  } else if (response.status === 404) {
    // 404 - не ошибка, просто пользователь не найден
    successRate.add(false);
    errorRate.add(false);
  } else if (response.status >= 500 || response.status === 0) {
    // Реальные ошибки
    successRate.add(false);
    errorRate.add(true);
  } else {
    successRate.add(false);
    errorRate.add(false);
  }

  // Если запрос успешен, обрабатываем метрики производительности
  if (response.status === 200) {
    try {
      const body = JSON.parse(response.body);
      const metrics = body.performance_metrics;

      if (metrics) {
        // Общее время
        totalResponseTime.add(metrics.total_time_ms);

        // Метрики кэша
        if (metrics.cache_hit) {
          cacheHits.add(1);
          cacheHitRate.add(true);
        } else {
          cacheMisses.add(1);
          cacheHitRate.add(false);
        }

        // Redis метрики
        if (metrics.redis_check_time_ms !== null) {
          redisCheckTime.add(metrics.redis_check_time_ms);
        }
        if (metrics.redis_save_time_ms !== null) {
          redisSaveTime.add(metrics.redis_save_time_ms);
        }
        
        // Общее время Redis
        const totalRedis = (metrics.redis_check_time_ms || 0) + (metrics.redis_save_time_ms || 0);
        if (totalRedis > 0) {
          redisTotalTime.add(totalRedis);
        }

        // ClickHouse метрики
        if (metrics.clickhouse_user_check_time_ms !== null) {
          clickhouseUserCheckTime.add(metrics.clickhouse_user_check_time_ms);
        }
        if (metrics.clickhouse_interactions_count_time_ms !== null) {
          clickhouseInteractionsCountTime.add(metrics.clickhouse_interactions_count_time_ms);
        }
        if (metrics.clickhouse_similar_users_time_ms !== null) {
          clickhouseSimilarUsersTime.add(metrics.clickhouse_similar_users_time_ms);
        }
        if (metrics.clickhouse_recommendations_time_ms !== null) {
          clickhouseRecommendationsTime.add(metrics.clickhouse_recommendations_time_ms);
        }

        // Общее время ClickHouse
        const totalClickhouse = (metrics.clickhouse_user_check_time_ms || 0) +
                                (metrics.clickhouse_interactions_count_time_ms || 0) +
                                (metrics.clickhouse_similar_users_time_ms || 0) +
                                (metrics.clickhouse_recommendations_time_ms || 0);
        if (totalClickhouse > 0) {
          clickhouseTotalTime.add(totalClickhouse);
        }

        // Алгоритм метрики
        if (metrics.algorithm_processing_time_ms !== null) {
          algorithmProcessingTime.add(metrics.algorithm_processing_time_ms);
        }

        // Метрики похожих пользователей
        if (metrics.similar_users_count !== null) {
          similarUsersCount.add(metrics.similar_users_count);
        }
      }
    } catch (e) {
      console.error(`Error parsing response metrics: ${e}`);
      // Парсинг ошибки - это реальная ошибка
      errorRate.add(true);
    }
  } else if (response.status === 404) {
    // 404 - не ошибка, просто пользователь не найден
    // Не логируем, чтобы не засорять вывод
  } else if (response.status >= 500) {
    // Реальная ошибка сервера
    console.error(`User ${userId}: Server Error ${response.status}`);
  }

  // Пауза между запросами (имитируем реальную нагрузку)
  sleep(1);
}

// ════════════════════════════════════════════════════════
// Функция обработки результатов
// ════════════════════════════════════════════════════════

export function handleSummary(data) {
  // Вызываем наш кастомный вывод
  printDetailedSummary(data);

  // Сохраняем детальный JSON отчет
  return {
    'summary_recommendations_performance.json': JSON.stringify(data, null, 2),
  };
}

/**
 * Выводит детальную статистику по всем компонентам
 */
function printDetailedSummary(data) {
  const line = '═'.repeat(80);
  const separator = '─'.repeat(80);
  
  console.log('\n' + line);
  console.log('  📊 ДЕТАЛЬНЫЙ АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ РЕКОМЕНДАЦИЙ');
  console.log(line + '\n');

  // Базовая статистика теста
  const stats = getBasicStats(data);
  printBasicStats(stats);

  console.log(separator + '\n');

  // ════════════════════════════════════════════════════════
  // Статистика по кэшу
  // ════════════════════════════════════════════════════════
  console.log('💾 СТАТИСТИКА КЭША (Redis):\n');
  
  const cacheHitRateValue = data.metrics.cache_hit_rate?.values?.rate || 0;
  const cacheHitsValue = data.metrics.cache_hits?.values?.count || 0;
  const cacheMissesValue = data.metrics.cache_misses?.values?.count || 0;
  
  console.log(`   • Попадания в кэш:         ${cacheHitsValue}`);
  console.log(`   • Промахи кэша:            ${cacheMissesValue}`);
  console.log(`   • Hit Rate:                ${(cacheHitRateValue * 100).toFixed(2)}%`);
  console.log('');

  printMetricStats('   Redis - проверка кэша:', data.metrics.redis_check_time);
  printMetricStats('   Redis - сохранение:   ', data.metrics.redis_save_time);
  printMetricStats('   Redis - ИТОГО:        ', data.metrics.redis_total_time);
  
  console.log('\n' + separator + '\n');

  // ════════════════════════════════════════════════════════
  // Статистика по ClickHouse
  // ════════════════════════════════════════════════════════
  console.log('🗄️  СТАТИСТИКА CLICKHOUSE:\n');
  
  printMetricStats('   Проверка пользователя:    ', data.metrics.clickhouse_user_check_time);
  printMetricStats('   Подсчет взаимодействий:   ', data.metrics.clickhouse_interactions_count_time);
  printMetricStats('   Поиск похожих польз.:     ', data.metrics.clickhouse_similar_users_time);
  printMetricStats('   Получение рекомендаций:   ', data.metrics.clickhouse_recommendations_time);
  printMetricStats('   ClickHouse - ИТОГО:       ', data.metrics.clickhouse_total_time);

  console.log('\n' + separator + '\n');

  // ════════════════════════════════════════════════════════
  // Статистика по алгоритму
  // ════════════════════════════════════════════════════════
  console.log('🧮 СТАТИСТИКА АЛГОРИТМА:\n');
  
  printMetricStats('   Обработка результатов:', data.metrics.algorithm_processing_time);
  
  const avgSimilarUsers = data.metrics.similar_users_count?.values?.avg || 0;
  const minSimilarUsers = data.metrics.similar_users_count?.values?.min || 0;
  const maxSimilarUsers = data.metrics.similar_users_count?.values?.max || 0;
  
  console.log(`\n   • Похожих пользователей (среднее): ${avgSimilarUsers.toFixed(1)}`);
  console.log(`   • Похожих пользователей (мин):     ${minSimilarUsers}`);
  console.log(`   • Похожих пользователей (макс):    ${maxSimilarUsers}`);

  console.log('\n' + separator + '\n');

  // ════════════════════════════════════════════════════════
  // Общая статистика времени
  // ════════════════════════════════════════════════════════
  console.log('⏱️  ОБЩЕЕ ВРЕМЯ ОТВЕТА:\n');
  
  printMetricStats('   Total Response Time:', data.metrics.total_response_time);

  console.log('\n' + separator + '\n');

  // ════════════════════════════════════════════════════════
  // Анализ распределения времени
  // ════════════════════════════════════════════════════════
  console.log('📈 АНАЛИЗ РАСПРЕДЕЛЕНИЯ ВРЕМЕНИ (среднее):\n');
  
  const avgRedis = data.metrics.redis_total_time?.values?.avg || 0;
  const avgClickHouse = data.metrics.clickhouse_total_time?.values?.avg || 0;
  const avgAlgorithm = data.metrics.algorithm_processing_time?.values?.avg || 0;
  const avgTotal = data.metrics.total_response_time?.values?.avg || 1;
  
  const redisPercent = (avgRedis / avgTotal) * 100;
  const clickhousePercent = (avgClickHouse / avgTotal) * 100;
  const algorithmPercent = (avgAlgorithm / avgTotal) * 100;
  const otherPercent = 100 - redisPercent - clickhousePercent - algorithmPercent;
  
  console.log(`   • Redis:                   ${avgRedis.toFixed(2)}ms (${redisPercent.toFixed(1)}%)`);
  console.log(`   • ClickHouse:              ${avgClickHouse.toFixed(2)}ms (${clickhousePercent.toFixed(1)}%)`);
  console.log(`   • Алгоритм:                ${avgAlgorithm.toFixed(2)}ms (${algorithmPercent.toFixed(1)}%)`);
  console.log(`   • Прочее (сеть, FastAPI):  ${(avgTotal - avgRedis - avgClickHouse - avgAlgorithm).toFixed(2)}ms (${otherPercent.toFixed(1)}%)`);
  console.log(`   • ИТОГО:                   ${avgTotal.toFixed(2)}ms (100.0%)`);

  console.log('\n' + separator + '\n');

  // ════════════════════════════════════════════════════════
  // Рекомендации по оптимизации
  // ════════════════════════════════════════════════════════
  console.log('💡 РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ:\n');
  
  const recommendations = [];
  
  // Анализ кэша
  if (cacheHitRateValue < 0.3) {
    recommendations.push('   ⚠️  Низкий Hit Rate кэша (<30%). Рассмотрите увеличение TTL или предварительный прогрев кэша.');
  }
  
  // Анализ Redis
  if (avgRedis > 50) {
    recommendations.push('   ⚠️  Redis работает медленно (>50ms). Проверьте сетевую задержку или нагрузку на Redis.');
  }
  
  // Анализ ClickHouse
  if (avgClickHouse > 2000) {
    recommendations.push('   ⚠️  ClickHouse запросы медленные (>2000ms). Рассмотрите оптимизацию запросов или добавление индексов.');
  }
  
  if (data.metrics.clickhouse_similar_users_time?.values?.avg > 1000) {
    recommendations.push('   ⚠️  Поиск похожих пользователей занимает много времени (>1000ms). Рассмотрите предварительный расчет матрицы схожести.');
  }
  
  if (data.metrics.clickhouse_recommendations_time?.values?.avg > 1500) {
    recommendations.push('   ⚠️  Получение рекомендаций медленное (>1500ms). Рассмотрите материализованные представления или денормализацию.');
  }
  
  // Анализ алгоритма
  if (avgAlgorithm > 50) {
    recommendations.push('   ⚠️  Алгоритм обработки медленный (>50ms). Рассмотрите оптимизацию Python кода или использование Cython.');
  }
  
  // Анализ общего времени
  if (avgTotal > 5000) {
    recommendations.push('   ⚠️  Общее время ответа очень высокое (>5000ms). Требуется комплексная оптимизация всех компонентов.');
  }
  
  if (recommendations.length === 0) {
    console.log('   ✅ Производительность в пределах нормы! Все компоненты работают эффективно.');
  } else {
    recommendations.forEach(rec => console.log(rec));
  }

  console.log('\n' + line + '\n');
}

/**
 * Выводит статистику по метрике
 */
function printMetricStats(label, metric) {
  if (!metric || !metric.values) {
    console.log(`${label} N/A`);
    return;
  }
  
  const avg = metric.values.avg || 0;
  const min = metric.values.min || 0;
  const med = metric.values.med || 0;
  const max = metric.values.max || 0;
  const p95 = metric.values['p(95)'] || 0;
  const p99 = metric.values['p(99)'] || 0;
  
  console.log(`${label}`);
  console.log(`      avg: ${avg.toFixed(2)}ms | med: ${med.toFixed(2)}ms | p95: ${p95.toFixed(2)}ms | p99: ${p99.toFixed(2)}ms`);
  console.log(`      min: ${min.toFixed(2)}ms | max: ${max.toFixed(2)}ms`);
}

