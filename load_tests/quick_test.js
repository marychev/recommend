/**
 * k6 Быстрый тест для проверки API
 * 
 * Короткий тест для проверки, что API работает и готов к нагрузочному тестированию
 * 
 * Запуск: k6 run load_tests/quick_test.js
 */

import http from 'k6/http';
import { check, group } from 'k6';
import { 
  BASE_URL,
  getBasicStats,
  printHeader,
  printBasicStats,
  evaluateResults,
  formatPercent 
} from './k6-helpers.js';

export const options = {
  vus: 5,
  duration: '30s',
  thresholds: {
    'http_req_duration': ['p(95)<3000'],
    'http_req_failed': ['rate<0.1'],
  },
};

export default function () {
  group('API Health Check', () => {
    const res = http.get(`${BASE_URL}/`);
    check(res, {
      'root endpoint is 200': (r) => r.status === 200,
    });
  });

  group('Users API', () => {
    const res = http.get(`${BASE_URL}/api/v1/users?limit=10`);
    check(res, {
      'users list is 200': (r) => r.status === 200,
      'users list returns data': (r) => JSON.parse(r.body).length > 0,
    });
  });

  group('Tracks API', () => {
    const res = http.get(`${BASE_URL}/api/v1/tracks?limit=10`);
    check(res, {
      'tracks list is 200': (r) => r.status === 200,
      'tracks list returns data': (r) => JSON.parse(r.body).length > 0,
    });
  });

  group('Recommendations API', () => {
    const res = http.post(
      `${BASE_URL}/api/v1/recommendations`,
      JSON.stringify({ user_id: 1, top_n: 10 }),
      { headers: { 'Content-Type': 'application/json' } }
    );
    check(res, {
      'recommendations endpoint responds': (r) => r.status === 200 || r.status === 404,
    });
  });
}

export function handleSummary(data) {
  printHeader('✅ БЫСТРАЯ ПРОВЕРКА API ЗАВЕРШЕНА');
  
  const stats = getBasicStats(data);
  
  console.log(`📊 Результаты:`);
  console.log(`   • Всего запросов:        ${stats.totalReqs}`);
  console.log(`   • Среднее время ответа:  ${stats.avgDuration.toFixed(0)}ms`);
  console.log(`   • 95 перцентиль:         ${stats.p95Duration.toFixed(0)}ms`);
  console.log(`   • Процент ошибок:        ${formatPercent(stats.failRate)}`);
  console.log('');
  
  // Оценка готовности
  if (stats.failRate < 0.1 && stats.p95Duration < 3000) {
    console.log(`✅ API готов к нагрузочному тестированию!`);
  } else {
    console.log(`⚠️  Обнаружены проблемы. Проверьте API перед полноценным тестированием.`);
    console.log('');
    console.log(`💡 Запустите диагностику: make load-test-diagnostics`);
  }
  
  console.log('');
  console.log('═'.repeat(63));
  console.log('');
  
  return {};
}

