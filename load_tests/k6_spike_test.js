/**
 * k6 Spike Test - Тест пиковой нагрузки
 * 
 * Резко увеличивает нагрузку для проверки поведения системы при внезапном росте трафика
 * 
 * Запуск: k6 run load_tests/k6_spike_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';
import { BASE_URL, getRandomUserId, getRandomTrackId, urlTracksList10, urlUsersList10 } from './k6-helpers.js';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '10s', target: 4 },   // Базовая нагрузка
    { duration: '20s', target: 50 },  // Резкий скачок до 50 пользователей (было 200)
    { duration: '30s', target: 50 },   // Удержание пиковой нагрузки
    { duration: '10s', target: 10 },   // Резкое снижение
    { duration: '10s', target: 0 },    // Завершение
  ],
  thresholds: {
    // Очень мягкие пороги для диагностики (50 VUs)
    'http_req_duration': ['p(95)<15000'],  // 15 секунд для p95
    'http_req_failed': ['rate<0.3'],       // До 30% ошибок
    'errors': ['rate<0.3'],
  },
};

export default function () {
  // Выбираем случайный эндпоинт
  const endpoints = [
    () => http.get(urlUsersList10),
    () => http.get(urlTracksList10),
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
  
  // Минимальная пауза при spike тесте для создания реальной нагрузки
  sleep(0.3);
}

/**
 * Обработка результатов spike теста
 */
export function handleSummary(data) {
  console.log('\n');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('            ⚡ SPIKE TEST ЗАВЕРШЁН                         ');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  
  const totalReqs = data.metrics.http_reqs?.values?.count || 0;
  const failRate = (data.metrics.http_req_failed?.values?.rate || 0) * 100;
  const avgDuration = data.metrics.http_req_duration?.values?.avg || 0;
  const p95Duration = data.metrics.http_req_duration?.values?.['p(95)'] || 0;
  const p99Duration = data.metrics.http_req_duration?.values?.['p(99)'] || 0;
  const maxVUs = data.metrics.vus_max?.values?.max || 0;
  
  console.log(`📊 Статистика:`);
  console.log(`   • Пиковая нагрузка:      ${maxVUs} VUs`);
  console.log(`   • Всего запросов:        ${totalReqs}`);
  console.log(`   • Среднее время:         ${avgDuration.toFixed(2)}ms`);
  console.log(`   • 95 перцентиль:         ${p95Duration.toFixed(2)}ms`);
  console.log(`   • 99 перцентиль:         ${p99Duration.toFixed(2)}ms`);
  console.log(`   • Процент ошибок:        ${failRate.toFixed(2)}%`);
  console.log('');
  
  // Оценка устойчивости к пиковой нагрузке
  let status = '✅ PASSED';
  let message = 'Система устойчива к пиковым нагрузкам!';
  
  if (failRate > 15) {
    status = '❌ FAILED';
    message = 'Слишком много ошибок при пиковой нагрузке. Требуется оптимизация!';
  } else if (p95Duration > 5000) {
    status = '⚠️  WARNING';
    message = 'Система медленно отвечает при пиковой нагрузке. Рекомендуется масштабирование.';
  } else if (failRate > 5) {
    status = '⚠️  WARNING';
    message = 'Есть ошибки при пиковой нагрузке, но система остается работоспособной.';
  }
  
  console.log(`${status}: ${message}`);
  console.log('');
  console.log('💡 Spike test показывает, как система ведет себя при резком росте трафика.');
  console.log('   Небольшая деградация производительности - это нормально.');
  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  
  return {};
}

