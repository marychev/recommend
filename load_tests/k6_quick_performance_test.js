/**
 * k6 Быстрый тест производительности рекомендаций
 * 
 * Упрощенная версия для быстрой проверки производительности
 * Выполняет небольшое количество запросов и выводит детальную статистику
 * 
 * Запуск:
 * k6 run load_tests/k6_quick_performance_test.js
 * k6 run load_tests/k6_quick_performance_test.js --env API_URL=http://localhost:8000
 */

import http from 'k6/http';
import { check } from 'k6';
import { Trend, Counter } from 'k6/metrics';
import { BASE_URL, getRandomUserId } from './k6-helpers.js';

// ════════════════════════════════════════════════════════
// Конфигурация теста - всего 10 итераций для быстрой проверки
// ════════════════════════════════════════════════════════

export const options = {
  iterations: 10,
  vus: 1,
};

// Метрики для сбора данных
const totalTime = new Trend('perf_total_time');
const redisCheckTime = new Trend('perf_redis_check');
const redisSaveTime = new Trend('perf_redis_save');
const chUserCheckTime = new Trend('perf_ch_user_check');
const chInteractionsTime = new Trend('perf_ch_interactions');
const chSimilarUsersTime = new Trend('perf_ch_similar_users');
const chRecommendationsTime = new Trend('perf_ch_recommendations');
const algorithmTime = new Trend('perf_algorithm');
const cacheHits = new Counter('perf_cache_hits');
const cacheMisses = new Counter('perf_cache_misses');

// ════════════════════════════════════════════════════════
// Основная функция тестирования
// ════════════════════════════════════════════════════════

export default function () {
  const userId = getRandomUserId();
  
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
  };

  const response = http.post(`${BASE_URL}/api/v1/recommendations`, payload, params);

  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'has performance_metrics': (r) => {
      if (r.status === 200) {
        const body = JSON.parse(r.body);
        return body.performance_metrics !== null && body.performance_metrics !== undefined;
      }
      return false;
    },
  });

  if (response.status === 200) {
    try {
      const body = JSON.parse(response.body);
      const m = body.performance_metrics;
      
      if (m) {
        console.log(`User ${userId}: ${m.cache_hit ? '💾 cache' : '🔍 fresh'} | Total: ${m.total_time_ms.toFixed(1)}ms`);
        
        // Сохраняем метрики
        totalTime.add(m.total_time_ms);
        
        if (m.cache_hit) {
          cacheHits.add(1);
        } else {
          cacheMisses.add(1);
        }
        
        if (m.redis_check_time_ms) redisCheckTime.add(m.redis_check_time_ms);
        if (m.redis_save_time_ms) redisSaveTime.add(m.redis_save_time_ms);
        if (m.clickhouse_user_check_time_ms) chUserCheckTime.add(m.clickhouse_user_check_time_ms);
        if (m.clickhouse_interactions_count_time_ms) chInteractionsTime.add(m.clickhouse_interactions_count_time_ms);
        if (m.clickhouse_similar_users_time_ms) chSimilarUsersTime.add(m.clickhouse_similar_users_time_ms);
        if (m.clickhouse_recommendations_time_ms) chRecommendationsTime.add(m.clickhouse_recommendations_time_ms);
        if (m.algorithm_processing_time_ms) algorithmTime.add(m.algorithm_processing_time_ms);
      } else {
        console.log(`User ${userId}: ⚠️  No performance_metrics in response`);
      }
    } catch (e) {
      console.error(`Error parsing response: ${e}`);
    }
  } else {
    console.log(`User ${userId}: ❌ Error ${response.status}`);
  }
}

// ════════════════════════════════════════════════════════
// Вывод результатов
// ════════════════════════════════════════════════════════

export function handleSummary(data) {
  const line = '═'.repeat(80);
  const separator = '─'.repeat(80);
  
  console.log('\n' + line);
  console.log('  ⚡ БЫСТРЫЙ ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ РЕКОМЕНДАЦИЙ');
  console.log(line + '\n');

  const totalRequests = data.metrics.http_reqs?.values?.count || 0;
  
  if (totalRequests === 0) {
    console.log('  ❌ Нет данных для анализа');
    console.log('\n' + line + '\n');
    return {};
  }

  console.log(`📊 Обработано запросов: ${totalRequests}\n`);

  // Получаем метрики
  const hits = data.metrics.perf_cache_hits?.values?.count || 0;
  const misses = data.metrics.perf_cache_misses?.values?.count || 0;
  const totalCacheOps = hits + misses;

  console.log(separator + '\n');
  console.log('💾 КЭШ:\n');
  console.log(`   • Попадания в кэш:  ${hits}`);
  console.log(`   • Промахи кэша:     ${misses}`);
  console.log(`   • Hit Rate:         ${totalCacheOps > 0 ? ((hits / totalCacheOps) * 100).toFixed(1) : 0}%`);
  
  console.log('\n' + separator + '\n');
  console.log('⏱️  СРЕДНЕЕ ВРЕМЯ ВЫПОЛНЕНИЯ:\n');
  
  const avgTotal = data.metrics.perf_total_time?.values?.avg || 0;
  const avgRedisCheck = data.metrics.perf_redis_check?.values?.avg || 0;
  const avgRedisSave = data.metrics.perf_redis_save?.values?.avg || 0;
  const avgChUserCheck = data.metrics.perf_ch_user_check?.values?.avg || 0;
  const avgChInteractions = data.metrics.perf_ch_interactions?.values?.avg || 0;
  const avgChSimilarUsers = data.metrics.perf_ch_similar_users?.values?.avg || 0;
  const avgChRecommendations = data.metrics.perf_ch_recommendations?.values?.avg || 0;
  const avgAlgorithm = data.metrics.perf_algorithm?.values?.avg || 0;
  
  const totalRedis = avgRedisCheck + avgRedisSave;
  const totalClickhouse = avgChUserCheck + avgChInteractions + avgChSimilarUsers + avgChRecommendations;
  
  console.log('   Redis:');
  console.log(`      • Проверка кэша:              ${avgRedisCheck.toFixed(2)}ms`);
  console.log(`      • Сохранение:                 ${avgRedisSave.toFixed(2)}ms`);
  console.log(`      • ИТОГО Redis:                ${totalRedis.toFixed(2)}ms`);
  
  console.log('\n   ClickHouse:');
  console.log(`      • Проверка пользователя:      ${avgChUserCheck.toFixed(2)}ms`);
  console.log(`      • Подсчет взаимодействий:     ${avgChInteractions.toFixed(2)}ms`);
  console.log(`      • Поиск похожих польз.:       ${avgChSimilarUsers.toFixed(2)}ms`);
  console.log(`      • Получение рекомендаций:     ${avgChRecommendations.toFixed(2)}ms`);
  console.log(`      • ИТОГО ClickHouse:           ${totalClickhouse.toFixed(2)}ms`);
  
  console.log('\n   Алгоритм:');
  console.log(`      • Обработка результатов:      ${avgAlgorithm.toFixed(2)}ms`);
  
  console.log('\n   📊 ОБЩЕЕ ВРЕМЯ:');
  console.log(`      • Total Response Time:        ${avgTotal.toFixed(2)}ms`);

  console.log('\n' + separator + '\n');
  console.log('📈 РАСПРЕДЕЛЕНИЕ ВРЕМЕНИ:\n');
  
  const safeTotalTime = avgTotal || 1;
  const redisPercent = (totalRedis / safeTotalTime) * 100;
  const clickhousePercent = (totalClickhouse / safeTotalTime) * 100;
  const algorithmPercent = (avgAlgorithm / safeTotalTime) * 100;
  const otherPercent = Math.max(0, 100 - redisPercent - clickhousePercent - algorithmPercent);
  
  console.log(`   • Redis:            ${redisPercent.toFixed(1)}%  ${getBar(redisPercent)}`);
  console.log(`   • ClickHouse:       ${clickhousePercent.toFixed(1)}%  ${getBar(clickhousePercent)}`);
  console.log(`   • Алгоритм:         ${algorithmPercent.toFixed(1)}%  ${getBar(algorithmPercent)}`);
  console.log(`   • Прочее:           ${otherPercent.toFixed(1)}%  ${getBar(otherPercent)}`);

  console.log('\n' + separator + '\n');
  console.log('📊 СТАТИСТИКА:\n');
  
  console.log(`   • Успешных запросов:          ${data.metrics.checks?.values?.passes || 0}`);
  console.log(`   • Ошибок:                     ${data.metrics.checks?.values?.fails || 0}`);
  console.log(`   • Среднее время HTTP:         ${(data.metrics.http_req_duration?.values?.avg || 0).toFixed(2)}ms`);
  console.log(`   • p95 HTTP:                   ${(data.metrics.http_req_duration?.values?.['p(95)'] || 0).toFixed(2)}ms`);

  console.log('\n' + line + '\n');

  return {
    'stdout': '',
    'summary_quick_performance.json': JSON.stringify(data, null, 2),
  };
}

/**
 * Создает текстовый прогресс-бар
 */
function getBar(percent, width = 40) {
  // Защита от некорректных значений
  if (!isFinite(percent) || percent < 0) {
    percent = 0;
  }
  if (percent > 100) {
    percent = 100;
  }
  
  const filled = Math.max(0, Math.min(width, Math.round((percent / 100) * width)));
  const empty = Math.max(0, width - filled);
  return '█'.repeat(filled) + '░'.repeat(empty);
}

