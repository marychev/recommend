/**
 * k6 Soak Test - Тест на выносливость
 * 
 * Длительный тест с умеренной нагрузкой для выявления утечек памяти и деградации производительности
 * 
 * Запуск: k6 run load_tests/k6_soak_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { BASE_URL, getRandomUserId } from './k6-helpers.js';

const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

export const options = {
  stages: [
    { duration: '5m', target: 50 },    // Разогрев до 50 пользователей
    { duration: '60m', target: 50 },   // Стабильная нагрузка 1 час
    { duration: '5m', target: 0 },     // Плавное завершение
  ],
  thresholds: {
    'http_req_duration': ['p(95)<2000', 'p(99)<5000'],
    'http_req_failed': ['rate<0.05'],
    'errors': ['rate<0.05'],
    'response_time': ['p(95)<2000'],
  },
};


export default function () {
  // Реалистичный сценарий использования
  
  // 1. Получить список пользователей
  let res = http.get(`${BASE_URL}/api/v1/users?limit=50`);
  let success = check(res, {
    'users list ok': (r) => r.status === 200,
  });
  errorRate.add(!success);
  responseTime.add(res.timings.duration);
  sleep(2);
  
  // 2. Получить конкретного пользователя
  const userId = getRandomUserId();
  res = http.get(`${BASE_URL}/api/v1/users/${userId}`);
  success = check(res, {
    'user ok': (r) => r.status === 200 || r.status === 404,
  });
  errorRate.add(!success);
  responseTime.add(res.timings.duration);
  sleep(1);
  
  // 3. Получить рекомендации
  res = http.get(`${BASE_URL}/api/v1/recommendations/${userId}`);
  success = check(res, {
    'recommendations ok': (r) => r.status === 200 || r.status === 404,
  });
  errorRate.add(!success);
  responseTime.add(res.timings.duration);
  sleep(3);
  
  // 4. Просмотр треков
  res = http.get(`${BASE_URL}/api/v1/tracks?limit=30`);
  success = check(res, {
    'tracks list ok': (r) => r.status === 200,
  });
  errorRate.add(!success);
  responseTime.add(res.timings.duration);
  sleep(2);
  
  // 5. Получить статистику
  res = http.get(`${BASE_URL}/api/v1/users/${userId}/statistics`);
  success = check(res, {
    'statistics ok': (r) => r.status === 200 || r.status === 404,
  });
  errorRate.add(!success);
  responseTime.add(res.timings.duration);
  sleep(5);
}

export function handleSummary(data) {
  console.log('\n╔═══════════════════════════════════════════════════╗');
  console.log('║       🕐 РЕЗУЛЬТАТЫ ТЕСТА НА ВЫНОСЛИВОСТЬ       ║');
  console.log('╚═══════════════════════════════════════════════════╝\n');
  
  const duration = data.state.testRunDurationMs / 1000 / 60; // в минутах
  
  console.log(`⏱️  Длительность: ${duration.toFixed(2)} минут`);
  console.log(`👥 Виртуальных пользователей: ${data.metrics.vus?.values?.value}`);
  console.log(`📤 Всего запросов: ${data.metrics.http_reqs?.values?.count}`);
  console.log(`📈 Средний RPS: ${data.metrics.http_reqs?.values?.rate.toFixed(2)}`);
  
  console.log(`\n📊 Время ответа за весь период:`);
  console.log(`   • Минимальное: ${data.metrics.http_req_duration?.values?.min.toFixed(2)}ms`);
  console.log(`   • Среднее: ${data.metrics.http_req_duration?.values?.avg.toFixed(2)}ms`);
  console.log(`   • Максимальное: ${data.metrics.http_req_duration?.values?.max.toFixed(2)}ms`);
  console.log(`   • 95%: ${data.metrics.http_req_duration?.values?.['p(95)'].toFixed(2)}ms`);
  
  const errorRateValue = (data.metrics.http_req_failed?.values?.rate || 0) * 100;
  console.log(`\n❌ Процент ошибок: ${errorRateValue.toFixed(2)}%`);
  
  // Проверка на деградацию производительности
  const avgResponseTime = data.metrics.http_req_duration?.values?.avg;
  const p95ResponseTime = data.metrics.http_req_duration?.values?.['p(95)'];
  
  if (p95ResponseTime > 3000) {
    console.log('\n⚠️  ВНИМАНИЕ: Обнаружена деградация производительности!');
    console.log('   95% запросов превышают 3 секунды.');
  }
  
  if (errorRateValue > 5) {
    console.log('\n⚠️  ВНИМАНИЕ: Высокий процент ошибок!');
  }
  
  return {
    'soak_test_results.json': JSON.stringify(data),
  };
}

