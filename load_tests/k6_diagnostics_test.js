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
import { BASE_URL, getRandomUserId, getRandomTrackId, urlUsersList10, urlTracksList10, getRandomIdFromArray } from './k6-helpers.js';

// Метрики по эндпоинтам
const usersListDuration = new Trend('users_list_duration');
const tracksListDuration = new Trend('tracks_list_duration');
const recommendationsDuration = new Trend('recommendations_duration');
const userByIdDuration = new Trend('user_by_id_duration');
const trackByIdDuration = new Trend('track_by_id_duration');

const usersListErrors = new Counter('users_list_errors');
const tracksListErrors = new Counter('tracks_list_errors');
const recommendationsErrors = new Counter('recommendations_errors');
// Кастомная метрика для реальных ошибок (5xx, таймауты, сеть) - без 404
const realErrors = new Counter('real_errors');

export const options = {
  vus: 10,
  duration: '1m',
  thresholds: {}, // БЕЗ thresholds - только диагностика
  // Настройка: только реальные ошибки (5xx, таймауты, сеть)
  noConnectionErrors: true,
  // Настраиваем, что считать ошибкой
  // 404 (Not Found) - это валидный ответ для несуществующих ресурсов
};

// Setup: получаем реальные ID один раз перед тестом
export function setup() {
  console.log('🔍 Загрузка реальных ID пользователей и треков...');
  
  // Получаем реальные ID пользователей
  let userIds = [];
  try {
    const usersRes = http.get(`${BASE_URL}/api/v1/users?limit=100`);
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
    const tracksRes = http.get(`${BASE_URL}/api/v1/tracks?limit=100`);
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
      // Считаем только реальные ошибки (5xx)
      if (res.status >= 500 || res.status === 0) {
        realErrors.add(1);
      }
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
      // Считаем только реальные ошибки (5xx)
      if (res.status >= 500 || res.status === 0) {
        realErrors.add(1);
      }
      console.log(`❌ 10 Tracks List ERROR: ${res.status} - ${res.body?.substring(0, 100)}`);
    }
  });

  sleep(0.3);

  // Тест 3: Recommendations (самый тяжелый)
  // Используем реальный ID, если доступен, иначе случайный
  group('Recommendations', () => {
    const userId = availableUserIds ? getRandomIdFromArray(availableUserIds) : getRandomUserId();
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/v1/recommendations/${userId}`, {
      tags: { name: 'Recommendations' },
    });
    recommendationsDuration.add(Date.now() - start);
    
    // 200 или 404 - это валидные ответы (404 = пользователь не найден)
    const success = check(res, {
      'recommendations status OK': (r) => r.status === 200 || r.status === 404,
    });
    
    // Считаем ошибкой только 5xx статусы и сетевые ошибки (не 404!)
    if (res.status >= 500) {
      recommendationsErrors.add(1);
      realErrors.add(1);
      console.log(`❌ Recommendations ERROR: ${res.status} - ${res.body?.substring(0, 100)}`);
    } else if (res.status === 0 || res.status === null) {
      // Сетевые ошибки
      recommendationsErrors.add(1);
      realErrors.add(1);
      console.log(`❌ Recommendations NETWORK ERROR`);
    }
  });

  sleep(0.3);

  // Тест 4: User by ID
  // Используем реальный ID, если доступен
  group('User by ID', () => {
    const userId = availableUserIds ? getRandomIdFromArray(availableUserIds) : getRandomUserId();
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/v1/users/${userId}`, {
      tags: { name: 'UserById' },
    });
    userByIdDuration.add(Date.now() - start);
    
    check(res, {
      'user by id status OK': (r) => r.status === 200 || r.status === 404,
    });
  });

  sleep(0.3);

  // Тест 5: Track by ID
  // Используем реальный ID, если доступен
  group('Track by ID', () => {
    const trackId = availableTrackIds ? getRandomIdFromArray(availableTrackIds) : getRandomTrackId();
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/v1/tracks/${trackId}`, {
      tags: { name: 'TrackById' },
    });
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
  const failRateRaw = (data.metrics.http_req_failed?.values?.rate || 0) * 100;
  const realErrorsCount = data.metrics.real_errors?.values?.count || 0;
  const realErrorsRate = totalReqs > 0 ? (realErrorsCount / totalReqs) * 100 : 0;
  
  console.log(`📊 Общая статистика:`);
  console.log(`   • Виртуальных пользователей: 10`);
  console.log(`   • Всего запросов:            ${totalReqs}`);
  console.log(`   • Процент ошибок (все):      ${failRateRaw.toFixed(2)}% (включает 404)`);
  console.log(`   • Реальных ошибок (5xx/сеть): ${realErrorsRate.toFixed(2)}% (${realErrorsCount} из ${totalReqs})`);
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
  // Примечание: http_req_failed включает 404, поэтому используем realErrors для анализа
  if (realErrorsRate > 5) {
    console.log('');
    console.log(`   ❌ Высокий процент РЕАЛЬНЫХ ошибок (${realErrorsRate.toFixed(2)}%)`);
    console.log(`      • Реальные ошибки = 5xx статусы, таймауты, сетевые ошибки`);
    console.log(`      • 404 (Not Found) НЕ считается ошибкой - это нормально для несуществующих ресурсов`);
    console.log(`      1. Проверьте логи: make logs-errors`);
    console.log(`      2. Проверьте подключение к БД: docker-compose logs clickhouse`);
    console.log(`      3. Проверьте, что сервисы запущены: docker-compose ps`);
    console.log(`      4. Проверьте ресурсы: docker stats`);
    console.log(`      5. Проверьте доступность API: curl ${BASE_URL}/health`);
  } else if (realErrorsRate > 0) {
    console.log('');
    console.log(`   ⚠️  Небольшой процент реальных ошибок (${realErrorsRate.toFixed(2)}%)`);
    console.log(`      • Это может быть нормально для нагрузочных тестов`);
    console.log(`      • 404 (Not Found) не считается ошибкой`);
  } else {
    console.log('');
    console.log(`   ✅ Нет реальных ошибок!`);
    console.log(`      • Все запросы успешно обработаны`);
    console.log(`      • 404 (Not Found) - это нормально для случайных ID`);
  }
  
  // Дополнительная информация о 404
  if (failRateRaw > 50 && realErrorsRate < 5) {
    console.log('');
    console.log(`   ℹ️  Примечание: Высокий процент 404 (${(failRateRaw - realErrorsRate).toFixed(2)}%)`);
    console.log(`      • Это означает, что многие случайные ID не существуют в БД`);
    console.log(`      • Тест теперь использует реальные ID из API для более точных результатов`);
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

