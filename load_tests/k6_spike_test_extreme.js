/**
 * k6 Extreme Spike Test - Экстремальная пиковая нагрузка (500 VUs)
 * 
 * Этот тест НЕ имеет строгих thresholds - используется для наблюдения
 * за поведением системы при экстремальной нагрузке
 * 
 * Запуск: k6 run load_tests/k6_spike_test_extreme.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '10s', target: 10 },    // Базовая нагрузка
    { duration: '5s', target: 500 },    // ЭКСТРЕМАЛЬНЫЙ скачок до 500 VUs
    { duration: '30s', target: 500 },   // Удержание
    { duration: '10s', target: 10 },    // Снижение
    { duration: '10s', target: 0 },     // Завершение
  ],
  // БЕЗ THRESHOLDS - только наблюдение за метриками
  thresholds: {},
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

function getRandomUserId() {
  return Math.floor(Math.random() * 100000) + 1;
}

function getRandomTrackId() {
  return Math.floor(Math.random() * 50000) + 1;
}

export default function () {
  const endpoints = [
    () => http.get(`${BASE_URL}/api/v1/users?limit=20`),
    () => http.get(`${BASE_URL}/api/v1/tracks?limit=20`),
    () => http.get(`${BASE_URL}/api/v1/recommendations/${getRandomUserId()}`),
    () => http.get(`${BASE_URL}/api/v1/users/${getRandomUserId()}`),
    () => http.get(`${BASE_URL}/api/v1/tracks/${getRandomTrackId()}`),
  ];
  
  const randomEndpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const res = randomEndpoint();
  
  const success = check(res, {
    'status is 2xx or 404': (r) => (r.status >= 200 && r.status < 300) || r.status === 404,
  });
  
  errorRate.add(!success);
  
  sleep(0.3);
}

export function handleSummary(data) {
  console.log('\n');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('        💥 EXTREME SPIKE TEST (500 VUs) ЗАВЕРШЁН          ');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  console.log('⚠️  Это тест БЕЗ thresholds - результат всегда PASSED');
  console.log('    Используйте для наблюдения за поведением системы');
  console.log('');
  
  const totalReqs = data.metrics.http_reqs?.values?.count || 0;
  const failRate = (data.metrics.http_req_failed?.values?.rate || 0) * 100;
  const avgDuration = data.metrics.http_req_duration?.values?.avg || 0;
  const p95Duration = data.metrics.http_req_duration?.values?.['p(95)'] || 0;
  const p99Duration = data.metrics.http_req_duration?.values?.['p(99)'] || 0;
  const maxDuration = data.metrics.http_req_duration?.values?.max || 0;
  const maxVUs = data.metrics.vus_max?.values?.max || 0;
  const rps = data.metrics.http_reqs?.values?.rate || 0;
  
  console.log(`📊 Статистика экстремальной нагрузки:`);
  console.log(`   • Пиковая нагрузка:      ${maxVUs} VUs`);
  console.log(`   • Всего запросов:        ${totalReqs}`);
  console.log(`   • RPS (req/sec):         ${rps.toFixed(2)}`);
  console.log(`   • Среднее время:         ${avgDuration.toFixed(2)}ms`);
  console.log(`   • 95 перцентиль:         ${p95Duration.toFixed(2)}ms`);
  console.log(`   • 99 перцентиль:         ${p99Duration.toFixed(2)}ms`);
  console.log(`   • Максимальное время:    ${maxDuration.toFixed(2)}ms`);
  console.log(`   • Процент ошибок:        ${failRate.toFixed(2)}%`);
  console.log('');
  
  // Анализ без строгих критериев
  console.log(`🔍 Анализ:`);
  if (failRate < 5) {
    console.log(`   ✅ Отлично! Система справляется с 500 VUs`);
  } else if (failRate < 15) {
    console.log(`   ⚠️  Система работает, но с деградацией`);
  } else if (failRate < 30) {
    console.log(`   ⚠️  Высокий процент ошибок - система перегружена`);
  } else {
    console.log(`   ❌ Критическая перегрузка - требуется масштабирование`);
  }
  
  if (p95Duration < 2000) {
    console.log(`   ✅ Время ответа отличное даже при пике`);
  } else if (p95Duration < 5000) {
    console.log(`   ⚠️  Время ответа приемлемое`);
  } else if (p95Duration < 10000) {
    console.log(`   ⚠️  Медленные ответы при пиковой нагрузке`);
  } else {
    console.log(`   ❌ Очень медленные ответы - требуется оптимизация`);
  }
  
  console.log('');
  console.log('💡 Рекомендации:');
  if (failRate > 10 || p95Duration > 5000) {
    console.log('   • Рассмотрите горизонтальное масштабирование (несколько инстансов API)');
    console.log('   • Проверьте кэширование (Redis)');
    console.log('   • Оптимизируйте запросы к ClickHouse');
    console.log('   • Увеличьте ресурсы (CPU/RAM) для контейнеров');
  } else {
    console.log('   • Система хорошо справляется с нагрузкой!');
  }
  
  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  
  return {};
}

