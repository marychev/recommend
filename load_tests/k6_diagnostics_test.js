/**
 * k6 Diagnostics Test - Диагностический тест для выявления проблем
 * 
 * Минимальная нагрузка для выявления узких мест системы
 * БЕЗ thresholds - только сбор метрик
 * 
 * Запуск: k6 run load_tests/k6_diagnostics_test.js
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Trend, Counter } from 'k6/metrics';
import { BASE_URL, getRandomUserId, getRandomTrackId, urlUsersList10, urlTracksList10 } from './k6-helpers.js';

// Метрики по эндпоинтам
const usersListDuration = new Trend('users_list_duration');
const tracksListDuration = new Trend('tracks_list_duration');
const recommendationsDuration = new Trend('recommendations_duration');
const userByIdDuration = new Trend('user_by_id_duration');
const trackByIdDuration = new Trend('track_by_id_duration');

const usersListErrors = new Counter('users_list_errors');
const tracksListErrors = new Counter('tracks_list_errors');
const recommendationsErrors = new Counter('recommendations_errors');

export const options = {
  vus: 10,
  duration: '1m',
  thresholds: {}, // БЕЗ thresholds - только диагностика
};


export default function () {
  // Тест 1: Users List
  group('Users List', () => {
    const start = Date.now();
    const res = http.get(urlUsersList10);
    usersListDuration.add(Date.now() - start);
    
    const success = check(res, {
      '10 users list status 200': (r) => r.status === 200,
    });
    
    if (!success) {
      usersListErrors.add(1);
      console.log(`❌ 10 Users List ERROR: ${res.status} - ${res.body?.substring(0, 100)}`);
    }
  });

  sleep(0.3);

  // Тест 2: Tracks List
  group('Tracks List', () => {
    const start = Date.now();
    const res = http.get(urlTracksList10);
    tracksListDuration.add(Date.now() - start);
    
    const success = check(res, {
      '10 tracks list status 200': (r) => r.status === 200,
    });
    
    if (!success) {
      tracksListErrors.add(1);
      console.log(`❌ 10 Tracks List ERROR: ${res.status} - ${res.body?.substring(0, 100)}`);
    }
  });

  sleep(0.3);

  // Тест 3: Recommendations (самый тяжелый)
  group('Recommendations', () => {
    const userId = getRandomUserId();
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/v1/recommendations/${userId}`);
    recommendationsDuration.add(Date.now() - start);
    
    const success = check(res, {
      'recommendations status OK': (r) => r.status === 200 || r.status === 404,
    });
    
    if (!success) {
      recommendationsErrors.add(1);
      console.log(`❌ Recommendations ERROR: ${res.status} - ${res.body?.substring(0, 100)}`);
    }
  });

  sleep(0.3);

  // Тест 4: User by ID
  group('User by ID', () => {
    const userId = getRandomUserId();
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/v1/users/${userId}`);
    userByIdDuration.add(Date.now() - start);
    
    check(res, {
      'user by id status OK': (r) => r.status === 200 || r.status === 404,
    });
  });

  sleep(0.3);

  // Тест 5: Track by ID
  group('Track by ID', () => {
    const trackId = getRandomTrackId();
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/v1/tracks/${trackId}`);
    trackByIdDuration.add(Date.now() - start);
    
    check(res, {
      'track by id status OK': (r) => r.status === 200 || r.status === 404,
    });
  });

  sleep(1);
}

export function handleSummary(data) {
  console.log('\n');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('           🔍 ДИАГНОСТИКА ПРОИЗВОДИТЕЛЬНОСТИ               ');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  
  const totalReqs = data.metrics.http_reqs?.values?.count || 0;
  const failRate = (data.metrics.http_req_failed?.values?.rate || 0) * 100;
  
  console.log(`📊 Общая статистика:`);
  console.log(`   • Виртуальных пользователей: 10`);
  console.log(`   • Всего запросов:            ${totalReqs}`);
  console.log(`   • Общий процент ошибок:      ${failRate.toFixed(2)}%`);
  console.log('');
  
  console.log(`📈 Время ответа по эндпоинтам:`);
  
  // Users List
  const usersListAvg = data.metrics.users_list_duration?.values?.avg || 0;
  const usersListP95 = data.metrics.users_list_duration?.values?.['p(95)'] || 0;
  const usersListMax = data.metrics.users_list_duration?.values?.max || 0;
  console.log(`   📋 GET /users (list):`);
  console.log(`      Среднее: ${usersListAvg.toFixed(0)}ms | p95: ${usersListP95.toFixed(0)}ms | Max: ${usersListMax.toFixed(0)}ms`);
  
  // Tracks List
  const tracksListAvg = data.metrics.tracks_list_duration?.values?.avg || 0;
  const tracksListP95 = data.metrics.tracks_list_duration?.values?.['p(95)'] || 0;
  const tracksListMax = data.metrics.tracks_list_duration?.values?.max || 0;
  console.log(`   🎵 GET /tracks (list):`);
  console.log(`      Среднее: ${tracksListAvg.toFixed(0)}ms | p95: ${tracksListP95.toFixed(0)}ms | Max: ${tracksListMax.toFixed(0)}ms`);
  
  // Recommendations
  const recAvg = data.metrics.recommendations_duration?.values?.avg || 0;
  const recP95 = data.metrics.recommendations_duration?.values?.['p(95)'] || 0;
  const recMax = data.metrics.recommendations_duration?.values?.max || 0;
  console.log(`   🎯 GET /recommendations (HEAVY):`);
  console.log(`      Среднее: ${recAvg.toFixed(0)}ms | p95: ${recP95.toFixed(0)}ms | Max: ${recMax.toFixed(0)}ms`);
  
  // User by ID
  const userByIdAvg = data.metrics.user_by_id_duration?.values?.avg || 0;
  const userByIdP95 = data.metrics.user_by_id_duration?.values?.['p(95)'] || 0;
  console.log(`   👤 GET /users/{id}:`);
  console.log(`      Среднее: ${userByIdAvg.toFixed(0)}ms | p95: ${userByIdP95.toFixed(0)}ms`);
  
  // Track by ID
  const trackByIdAvg = data.metrics.track_by_id_duration?.values?.avg || 0;
  const trackByIdP95 = data.metrics.track_by_id_duration?.values?.['p(95)'] || 0;
  console.log(`   🎵 GET /tracks/{id}:`);
  console.log(`      Среднее: ${trackByIdAvg.toFixed(0)}ms | p95: ${trackByIdP95.toFixed(0)}ms`);
  
  console.log('');
  console.log(`❌ Ошибки по эндпоинтам:`);
  const usersListErr = data.metrics.users_list_errors?.values?.count || 0;
  const tracksListErr = data.metrics.tracks_list_errors?.values?.count || 0;
  const recErr = data.metrics.recommendations_errors?.values?.count || 0;
  console.log(`   • Users List:        ${usersListErr}`);
  console.log(`   • Tracks List:       ${tracksListErr}`);
  console.log(`   • Recommendations:   ${recErr}`);
  
  console.log('');
  console.log(`🔍 АНАЛИЗ И РЕКОМЕНДАЦИИ:`);
  console.log('');
  
  // Анализ самого медленного эндпоинта
  const slowest = Math.max(usersListP95, tracksListP95, recP95, userByIdP95, trackByIdP95);
  
  if (slowest > 10000) {
    console.log(`   ❌ КРИТИЧНО: Очень медленные ответы (>${slowest.toFixed(0)}ms)`);
    console.log(`      1. Проверьте ClickHouse: docker-compose logs clickhouse`);
    console.log(`      2. Проверьте Redis: docker-compose logs redis`);
    console.log(`      3. Проверьте индексы в БД`);
    console.log(`      4. Увеличьте ресурсы Docker (CPU/RAM)`);
  } else if (slowest > 5000) {
    console.log(`   ⚠️  Медленные ответы (${slowest.toFixed(0)}ms)`);
    console.log(`      1. Оптимизируйте запросы к ClickHouse`);
    console.log(`      2. Проверьте кэширование Redis`);
    console.log(`      3. Рассмотрите индексацию`);
  } else if (slowest > 2000) {
    console.log(`   ⚠️  Приемлемая скорость, но можно улучшить`);
    console.log(`      1. Проверьте кэширование для рекомендаций`);
    console.log(`      2. Оптимизируйте сложные запросы`);
  } else {
    console.log(`   ✅ Хорошая производительность!`);
  }
  
  // Анализ ошибок
  if (failRate > 10) {
    console.log('');
    console.log(`   ❌ Высокий процент ошибок (${failRate.toFixed(2)}%)`);
    console.log(`      1. Проверьте логи: make logs-errors`);
    console.log(`      2. Проверьте подключение к БД`);
    console.log(`      3. Проверьте, что данные сгенерированы: make db-stats`);
  }
  
  // Анализ рекомендаций
  if (recP95 > usersListP95 * 5) {
    console.log('');
    console.log(`   ⚠️  Рекомендации в ${(recP95 / usersListP95).toFixed(1)}x медленнее других endpoints`);
    console.log(`      • Это НОРМАЛЬНО - ML алгоритмы требуют времени`);
    console.log(`      • Убедитесь, что кэширование Redis работает`);
    console.log(`      • Повторные запросы должны быть ~50x быстрее (из кэша)`);
  }
  
  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  
  return {};
}

