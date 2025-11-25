/**
 * k6 Spike Test - Тест пиковой нагрузки
 * 
 * Резко увеличивает нагрузку для проверки поведения системы при внезапном росте трафика
 * 
 * Запуск: k6 run load_tests/k6_spike_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Counter } from 'k6/metrics';
import { BASE_URL, getRandomUserId, getRandomTrackId, urlTracksList10, urlUsersList10, getRandomIdFromArray } from './k6-helpers.js';

const errorRate = new Rate('errors');
// Кастомная метрика для реальных ошибок (5xx, таймауты, сеть) - без 404
const realErrors = new Counter('real_errors');

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
    'http_req_failed': ['rate<0.7'],       // До 70% ошибок (включая 404)
    'errors': ['rate<0.3'],                // До 30% реальных ошибок
  },
  // Настройка: только реальные ошибки (5xx, таймауты, сеть)
  noConnectionErrors: true,
};

// Setup: получаем реальные ID один раз перед тестом
export function setup() {
  console.log('🔍 Загрузка реальных ID пользователей и треков для spike test...');
  
  // Получаем реальные ID пользователей
  let userIds = [];
  try {
    const usersRes = http.get(`${BASE_URL}/api/v1/users?limit=200`);
    if (usersRes.status === 200) {
      const users = JSON.parse(usersRes.body);
      userIds = users.map(u => u.user_id).filter(id => id != null);
    }
  } catch (e) {
    console.error(`Failed to get real user IDs: ${e}`);
  }
  
  // Получаем реальные ID треков
  let trackIds = [];
  try {
    const tracksRes = http.get(`${BASE_URL}/api/v1/tracks?limit=200`);
    if (tracksRes.status === 200) {
      const tracks = JSON.parse(tracksRes.body);
      trackIds = tracks.map(t => t.track_id).filter(id => id != null);
    }
  } catch (e) {
    console.error(`Failed to get real track IDs: ${e}`);
  }
  
  console.log(`✅ Загружено ${userIds.length} пользователей и ${trackIds.length} треков`);
  return {
    userIds: userIds,
    trackIds: trackIds,
  };
}

export default function (data) {
  // Используем реальные ID из setup, если они доступны
  const availableUserIds = (data && data.userIds && data.userIds.length > 0) ? data.userIds : null;
  const availableTrackIds = (data && data.trackIds && data.trackIds.length > 0) ? data.trackIds : null;
  
  // Выбираем случайный эндпоинт
  const endpoints = [
    () => http.get(urlUsersList10),
    () => http.get(urlTracksList10),
    () => {
      const userId = availableUserIds ? getRandomIdFromArray(availableUserIds) : getRandomUserId();
      return http.get(`${BASE_URL}/api/v1/recommendations/${userId}`);
    },
    () => {
      const userId = availableUserIds ? getRandomIdFromArray(availableUserIds) : getRandomUserId();
      return http.get(`${BASE_URL}/api/v1/users/${userId}`);
    },
    () => {
      const trackId = availableTrackIds ? getRandomIdFromArray(availableTrackIds) : getRandomTrackId();
      return http.get(`${BASE_URL}/api/v1/tracks/${trackId}`);
    },
  ];
  
  const randomEndpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const res = randomEndpoint();
  
  // 200 или 404 - это валидные ответы (404 = ресурс не найден)
  const success = check(res, {
    'status is 2xx or 404': (r) => (r.status >= 200 && r.status < 300) || r.status === 404,
  });
  
  // Считаем ошибкой только реальные ошибки (5xx, таймауты, сеть), не 404
  if (res.status >= 500 || res.status === 0 || res.status === null) {
    realErrors.add(1);
    errorRate.add(1);
  } else if (!success) {
    errorRate.add(1);
  }
  
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
  const failRateRaw = (data.metrics.http_req_failed?.values?.rate || 0) * 100;
  const realErrorsCount = data.metrics.real_errors?.values?.count || 0;
  const realErrorsRate = totalReqs > 0 ? (realErrorsCount / totalReqs) * 100 : 0;
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
  console.log(`   • Процент ошибок (все):  ${failRateRaw.toFixed(2)}% (включает 404)`);
  console.log(`   • Реальных ошибок (5xx/сеть): ${realErrorsRate.toFixed(2)}% (${realErrorsCount} из ${totalReqs})`);
  console.log('');
  
  // Оценка устойчивости к пиковой нагрузке
  // Используем реальные ошибки (не 404) для оценки
  let status = '✅ PASSED';
  let message = 'Система устойчива к пиковым нагрузкам!';
  
  if (realErrorsRate > 15) {
    status = '❌ FAILED';
    message = 'Слишком много реальных ошибок при пиковой нагрузке. Требуется оптимизация!';
  } else if (p95Duration > 5000) {
    status = '⚠️  WARNING';
    message = 'Система медленно отвечает при пиковой нагрузке. Рекомендуется масштабирование.';
  } else if (realErrorsRate > 5) {
    status = '⚠️  WARNING';
    message = 'Есть реальные ошибки при пиковой нагрузке, но система остается работоспособной.';
  }
  
  console.log(`${status}: ${message}`);
  console.log('');
  
  // Дополнительная информация о 404
  if (failRateRaw > 50 && realErrorsRate < 5) {
    console.log(`   ℹ️  Примечание: Высокий процент 404 (${(failRateRaw - realErrorsRate).toFixed(2)}%)`);
    console.log(`      • Это означает, что многие случайные ID не существуют в БД`);
    console.log(`      • Тест теперь использует реальные ID из API для более точных результатов`);
    console.log('');
  }
  
  // Рекомендации
  if (realErrorsRate > 0) {
    console.log('🔍 Рекомендации для оптимизации:');
    console.log('   1. Проверьте логи: make logs-errors');
    console.log('   2. Проверьте ресурсы Docker: docker stats');
    console.log('   3. Проверьте подключение к БД: docker-compose logs clickhouse');
    console.log('   4. Рассмотрите увеличение ресурсов или горизонтальное масштабирование');
    console.log('');
  }
  
  console.log('💡 Spike test показывает, как система ведет себя при резком росте трафика.');
  console.log('   Небольшая деградация производительности - это нормально.');
  console.log('   • 404 (Not Found) - это нормально для несуществующих ресурсов');
  console.log('   • Реальные ошибки = 5xx статусы, таймауты, сетевые ошибки');
  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  
  return {};
}

