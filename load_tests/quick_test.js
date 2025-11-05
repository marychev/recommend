/**
 * k6 Быстрый тест для проверки API
 * 
 * Короткий тест для проверки, что API работает и готов к нагрузочному тестированию
 * 
 * Запуск: k6 run load_tests/quick_test.js
 */

import http from 'k6/http';
import { check, group } from 'k6';

export const options = {
  vus: 5,
  duration: '30s',
  thresholds: {
    'http_req_duration': ['p(95)<3000'],
    'http_req_failed': ['rate<0.1'],
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

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
    const res = http.get(`${BASE_URL}/api/v1/recommendations/1`);
    check(res, {
      'recommendations endpoint responds': (r) => r.status === 200 || r.status === 404,
    });
  });
}

export function handleSummary(data) {
  console.log('\n╔════════════════════════════════════════════════╗');
  console.log('║      ✅ БЫСТРАЯ ПРОВЕРКА API ЗАВЕРШЕНА        ║');
  console.log('╚════════════════════════════════════════════════╝\n');
  
  const failRate = (data.metrics.http_req_failed?.values?.rate || 0) * 100;
  const avgDuration = data.metrics.http_req_duration?.values?.avg || 0;
  
  console.log(`📊 Результаты:`);
  console.log(`   • Всего запросов: ${data.metrics.http_reqs?.values?.count}`);
  console.log(`   • Среднее время ответа: ${avgDuration.toFixed(2)}ms`);
  console.log(`   • Процент ошибок: ${failRate.toFixed(2)}%`);
  
  if (failRate < 10 && avgDuration < 3000) {
    console.log(`\n✅ API готов к нагрузочному тестированию!\n`);
  } else {
    console.log(`\n⚠️  Обнаружены проблемы. Проверьте API перед полноценным тестированием.\n`);
  }
  
  return {};
}

