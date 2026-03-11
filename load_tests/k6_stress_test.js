/**
 * k6 Stress Test - Стресс-тестирование
 * 
 * Постепенно увеличивает нагрузку до точки отказа системы
 * 
 * Запуск: k6 run load_tests/k6_stress_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Counter } from 'k6/metrics';
import { BASE_URL, getRandomUserId } from './k6-helpers.js';

const errorRate = new Rate('errors');
const requests = new Counter('requests');

export const options = {
  stages: [
    { duration: '2m', target: 50 },    // Разогрев
    { duration: '5m', target: 100 },   // Нормальная нагрузка
    { duration: '5m', target: 200 },   // Увеличение нагрузки
    { duration: '5m', target: 300 },   // Высокая нагрузка
    { duration: '5m', target: 400 },   // Очень высокая нагрузка
    { duration: '5m', target: 500 },   // Экстремальная нагрузка
    { duration: '2m', target: 0 },     // Плавное завершение
  ],
  thresholds: {
    'http_req_duration': ['p(95)<10000'],  // Мягкие требования для стресс-теста
    'http_req_failed': ['rate<0.20'],       // Допускаем до 20% ошибок
  },
};


export default function () {
  requests.add(1);
  
  const scenario = Math.random();
  
  if (scenario < 0.5) {
    // 50% - рекомендации (самый тяжелый запрос)
    const res = http.post(
      `${BASE_URL}/api/v1/recommendations`,
      JSON.stringify({ user_id: getRandomUserId(), top_n: 10 }),
      { headers: { 'Content-Type': 'application/json' } }
    );
    check(res, {
      'recommendations status ok': (r) => r.status === 200 || r.status === 404,
    });
  } else if (scenario < 0.75) {
    // 25% - списки с большим лимитом
    const res = http.get(`${BASE_URL}/api/v1/users?limit=100&offset=${Math.floor(Math.random() * 10000)}`);
    check(res, {
      '100 users list status ok': (r) => r.status === 200,
    });
  } else {
    // 25% - статистика (тяжелые запросы)
    const res = http.get(`${BASE_URL}/api/v1/users/${getRandomUserId()}/statistics`);
    check(res, {
      'statistics status ok': (r) => r.status === 200 || r.status === 404,
    });
  }
  
  sleep(0.5);
}

export function handleSummary(data) {
  console.log('\n╔════════════════════════════════════════════════════╗');
  console.log('║        📊 РЕЗУЛЬТАТЫ СТРЕСС-ТЕСТИРОВАНИЯ         ║');
  console.log('╚════════════════════════════════════════════════════╝\n');
  
  console.log(`⏱️  Длительность: ${(data.state.testRunDurationMs / 1000).toFixed(2)}s`);
  console.log(`👥 Максимальная нагрузка: ${data.metrics.vus?.values?.max} пользователей`);
  console.log(`📤 Всего запросов: ${data.metrics.http_reqs?.values?.count}`);
  console.log(`📈 RPS: ${data.metrics.http_reqs?.values?.rate.toFixed(2)}`);
  console.log(`\n📊 Время ответа:`);
  console.log(`   • Среднее: ${data.metrics.http_req_duration?.values?.avg.toFixed(2)}ms`);
  console.log(`   • 95%: ${data.metrics.http_req_duration?.values?.['p(95)'].toFixed(2)}ms`);
  console.log(`   • 99%: ${data.metrics.http_req_duration?.values?.['p(99)'].toFixed(2)}ms`);
  console.log(`\n❌ Процент ошибок: ${((data.metrics.http_req_failed?.values?.rate || 0) * 100).toFixed(2)}%`);
  
  return {
    'stdout': JSON.stringify(data, null, 2),
    'stress_test_results.json': JSON.stringify(data),
  };
}

