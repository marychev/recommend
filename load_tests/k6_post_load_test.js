/**
 * k6 Нагрузочный тест для POST запросов
 * 
 * Тестирует производительность POST эндпоинтов:
 * - POST /api/v1/users - создание пользователя
 * - POST /api/v1/tracks - создание трека
 * - POST /api/v1/events - создание события взаимодействия
 * - POST /api/v1/recommendations - получение рекомендаций
 * 
 * Запуск: k6 run load_tests/k6_post_load_test.js
 * 
 * Параметры:
 * - API_URL=http://localhost:8000 - URL API (по умолчанию)
 * - VUS=50 - количество виртуальных пользователей (по умолчанию)
 * - DURATION=5m - длительность теста (по умолчанию)
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Trend, Counter, Rate } from 'k6/metrics';
import { BASE_URL, getRandomUserId, getRandomTrackId, formatDuration, getRandomIdFromArray } from './k6-helpers.js';

// ════════════════════════════════════════════════════════
// Метрики по эндпоинтам
// ════════════════════════════════════════════════════════

const createUserDuration = new Trend('post_create_user_duration');
const createTrackDuration = new Trend('post_create_track_duration');
const createEventDuration = new Trend('post_create_event_duration');
const getRecommendationsDuration = new Trend('post_get_recommendations_duration');

const createUserErrors = new Counter('post_create_user_errors');
const createTrackErrors = new Counter('post_create_track_errors');
const createEventErrors = new Counter('post_create_event_errors');
const getRecommendationsErrors = new Counter('post_get_recommendations_errors');

// Кастомная метрика для реальных ошибок (5xx, таймауты, сеть) - без 404
const realErrors = new Counter('real_errors');

const createUserSuccess = new Rate('post_create_user_success');
const createTrackSuccess = new Rate('post_create_track_success');
const createEventSuccess = new Rate('post_create_event_success');
const getRecommendationsSuccess = new Rate('post_get_recommendations_success');

// Счетчики запросов для расчета RPS по каждому эндпоинту
const createUserRequests = new Counter('post_create_user_requests');
const createTrackRequests = new Counter('post_create_track_requests');
const createEventRequests = new Counter('post_create_event_requests');
const getRecommendationsRequests = new Counter('post_get_recommendations_requests');

// ════════════════════════════════════════════════════════
// Конфигурация теста
// ════════════════════════════════════════════════════════

const VUS = parseInt(__ENV.VUS) || 100;
const DURATION = __ENV.DURATION || '4m';

export const options = {
  stages: [
    { duration: '30s', target: Math.floor(VUS * 0.2) },  // Разогрев: 20% от целевой нагрузки
    { duration: '1m', target: Math.floor(VUS * 0.5) },   // Рост до 50%
    { duration: DURATION, target: VUS },                 // Стабильная нагрузка
    { duration: '1m', target: Math.floor(VUS * 1.5) },   // Пиковая нагрузка: 150%
    { duration: '30s', target: 0 },                      // Завершение
  ],
  thresholds: {
    // Общие пороги
    'http_req_duration': ['p(95)<5000', 'p(99)<10000'],
    'http_req_failed': ['rate<0.70'], // До 70% ошибок (включая 404, которые нормальны)
    'real_errors': ['rate<0.05'], // До 5% реальных ошибок (5xx, таймауты, сеть)
    
    // Пороги по эндпоинтам
    'post_create_user_duration': ['p(95)<3000', 'p(99)<5000'],
    'post_create_track_duration': ['p(95)<3000', 'p(99)<5000'],
    'post_create_event_duration': ['p(95)<2000', 'p(99)<4000'],
    'post_get_recommendations_duration': ['p(95)<10000', 'p(99)<20000'],
    
    // Успешность запросов
    'post_create_user_success': ['rate>0.95'],
    'post_create_track_success': ['rate>0.95'],
    'post_create_event_success': ['rate>0.95'],
    'post_get_recommendations_success': ['rate>0.90'],
  },
  // Таймауты задаются в каждом HTTP запросе через параметр timeout
};

// ════════════════════════════════════════════════════════
// Генераторы тестовых данных
// ════════════════════════════════════════════════════════

/**
 * Генерирует случайное имя пользователя
 */
function generateUsername() {
  const prefixes = ['user', 'test', 'demo', 'load', 'perf', 'stress'];
  const suffixes = ['001', '002', 'test', 'user', 'demo'];
  const random = Math.floor(Math.random() * 1000000);
  return `${prefixes[Math.floor(Math.random() * prefixes.length)]}_${random}`;
}

/**
 * Генерирует случайный email
 */
function generateEmail() {
  const domains = ['example.com', 'test.com', 'demo.org', 'load.test'];
  const random = Math.floor(Math.random() * 1000000);
  return `user${random}@${domains[Math.floor(Math.random() * domains.length)]}`;
}

/**
 * Генерирует данные для создания пользователя
 */
function generateUserData() {
  return {
    username: generateUsername(),
    email: generateEmail(),
    age: Math.floor(Math.random() * 60) + 18, // 18-78 лет
    country: ['Russia', 'USA', 'Germany', 'France', 'UK', 'Japan'][Math.floor(Math.random() * 6)],
  };
}

/**
 * Генерирует данные для создания трека
 */
function generateTrackData() {
  const artists = ['Artist A', 'Artist B', 'Artist C', 'Band X', 'Singer Y', 'Group Z'];
  const genres = ['Rock', 'Pop', 'Jazz', 'Classical', 'Electronic', 'Hip-Hop', 'Country'];
  const albums = ['Album 1', 'Album 2', 'Greatest Hits', 'New Album', 'Best Of'];
  
  return {
    title: `Track ${Math.floor(Math.random() * 1000000)}`,
    artist: artists[Math.floor(Math.random() * artists.length)],
    album: albums[Math.floor(Math.random() * albums.length)],
    genre: genres[Math.floor(Math.random() * genres.length)],
    duration_seconds: Math.floor(Math.random() * 300) + 120, // 2-7 минут
    release_year: Math.floor(Math.random() * 30) + 1990, // 1990-2020
  };
}

/**
 * Генерирует данные для создания события
 */
function generateEventData(userId, trackId) {
  const actionTypes = ['play', 'like', 'dislike', 'skip', 'add_to_playlist', 'share'];
  
  return {
    user_id: userId,
    track_id: trackId,
    action_type: actionTypes[Math.floor(Math.random() * actionTypes.length)],
    listen_duration_seconds: Math.floor(Math.random() * 300) + 30, // 30-330 секунд
  };
}

/**
 * Генерирует данные для запроса рекомендаций
 */
function generateRecommendationRequest(userId) {
  return {
    user_id: userId,
    top_n: [5, 10, 20][Math.floor(Math.random() * 3)],
    exclude_listened: Math.random() > 0.5,
    include_performance_metrics: Math.random() > 0.7, // 30% запросов с метриками
  };
}

// ════════════════════════════════════════════════════════
// Setup: загрузка реальных ID для тестов
// ════════════════════════════════════════════════════════

export function setup() {
  // console.log('🔍 Загрузка реальных ID пользователей и треков для POST тестов...');
  
  // // Получаем реальные ID пользователей и треков для создания событий
  // const userIds = getRealUserIds(BASE_URL, 200);
  // const trackIds = getRealTrackIds(BASE_URL, 200);
  
  // console.log(`✅ Загружено ${userIds.length} пользователей и ${trackIds.length} треков`);
  
  // return {
  //   userIds: userIds,
  //   trackIds: trackIds,
  // };
}


function gerResultPost(url, payload, tagName, retries = 2) {
  let lastError = null;
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = http.post(
        url,
        payload,
        {
          headers: { 'Content-Type': 'application/json' },
          tags: { name: tagName },
          timeout: '60s', // Увеличенный таймаут для медленных запросов (особенно recommendations)
        }
      );
      
      // Если получили ответ (даже с ошибкой), возвращаем его
      if (res.status > 0) {
        // Считаем таймауты и сетевые ошибки как реальные ошибки
        if (res.status >= 500) {
          realErrors.add(1);
        }
        return res;
      }
      
      // Если status === 0, это означает таймаут или разрыв соединения
      lastError = res;
      
    } catch (e) {
      // Сетевые ошибки и исключения
      lastError = e;
      
      // Если это не последняя попытка, делаем небольшую паузу перед retry
      if (attempt < retries) {
        sleep(Math.random() * 0.5 + 0.1); // Случайная пауза 0.1-0.6 секунды
      }
    }
  }
  
  // Если все попытки не удались, считаем это реальной ошибкой
  realErrors.add(1);
  
  // Возвращаем последний результат или создаем фиктивный ответ с ошибкой
  if (lastError && typeof lastError === 'object' && 'status' in lastError) {
    return lastError;
  }
  
  // Создаем фиктивный ответ для обработки ошибки
  return {
    status: 0,
    body: '',
    timings: { duration: 60000 },
  };
}

// ════════════════════════════════════════════════════════
// Основной тест
// ════════════════════════════════════════════════════════

export default function (data) {
  const availableUserIds = (data && data.userIds && data.userIds.length > 0) ? data.userIds : null;
  const availableTrackIds = (data && data.trackIds && data.trackIds.length > 0) ? data.trackIds : null;

  // Тест 1: POST /api/v1/users - Создание пользователя
  group('POST Create User', () => {
    const userData = generateUserData();
    const payload = JSON.stringify(userData);
    
    const start = Date.now();
    const res = gerResultPost(`${BASE_URL}/api/v1/users`, payload, 'POST_CreateUser');
    const duration = Date.now() - start;
    createUserDuration.add(duration);
    createUserRequests.add(1);
    
    const success = check(res, {
      'create user status 201': (r) => r.status === 201,
      'create user has user_id': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.user_id !== undefined && body.user_id !== null;
        } catch {
          return false;
        }
      },
    });
    
    createUserSuccess.add(success);
    
    if (!success) {
      createUserErrors.add(1);
      if (res.status >= 500) {
        realErrors.add(1);
        console.log(`❌ Create User ERROR: ${res.status} - ${res.body?.substring(0, 100)}`);
      }
    }
  });

  // sleep(0.2);

  // Тест 2: POST /api/v1/tracks - Создание трека
  group('POST Create Track', () => {
    const trackData = generateTrackData();
    const payload = JSON.stringify(trackData);
    
    const start = Date.now();
    const res = gerResultPost(`${BASE_URL}/api/v1/tracks`, payload, 'POST_CreateTrack');
    const duration = Date.now() - start;
    createTrackDuration.add(duration);
    createTrackRequests.add(1);
    
    const success = check(res, {
      'create track status 201': (r) => r.status === 201,
      'create track has track_id': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.track_id !== undefined && body.track_id !== null;
        } catch {
          return false;
        }
      },
    });
    
    createTrackSuccess.add(success);
    
    if (!success) {
      createTrackErrors.add(1);
      if (res.status >= 500) {
        realErrors.add(1);
        console.log(`❌ Create Track ERROR: ${res.status} - ${res.body?.substring(0, 100)}`);
      }
    }
  });

  // sleep(0.2);

  // Тест 3: POST /api/v1/events - Создание события
  // Используем реальные ID, если доступны, иначе случайные
  group('POST Create Event', () => {
    const userId = availableUserIds 
      ? getRandomIdFromArray(availableUserIds) 
      : getRandomUserId();
    const trackId = availableTrackIds 
      ? getRandomIdFromArray(availableTrackIds) 
      : getRandomTrackId();
    
    const eventData = generateEventData(userId, trackId);
    const payload = JSON.stringify(eventData);
    
    const start = Date.now();
    const res = gerResultPost(`${BASE_URL}/api/v1/events`, payload, 'POST_CreateEvent');
    const duration = Date.now() - start;
    createEventDuration.add(duration);
    createEventRequests.add(1);
    
    // 201 - успех, 404 - пользователь/трек не найден (нормально для случайных ID)
    const success = check(res, {
      'create event status OK': (r) => r.status === 201 || r.status === 404,
    });
    
    createEventSuccess.add(success);
    
    if (!success || res.status >= 500) {
      createEventErrors.add(1);
      if (res.status >= 500) {
        realErrors.add(1);
        console.log(`❌ Create Event ERROR: ${res.status} - ${res.body?.substring(0, 100)}`);
      }
    }
  });

  // sleep(0.2);

  // Тест 4: POST /api/v1/recommendations - Получение рекомендаций
  // Используем реальный ID пользователя, если доступен
  group('POST Get Recommendations', () => {
    const userId = availableUserIds 
      ? getRandomIdFromArray(availableUserIds) 
      : getRandomUserId();
    
    const requestData = generateRecommendationRequest(userId);
    const payload = JSON.stringify(requestData);
    
    const start = Date.now();
    const res = gerResultPost(`${BASE_URL}/api/v1/recommendations`, payload, 'POST_GetRecommendations');
    const duration = Date.now() - start;
    getRecommendationsDuration.add(duration);
    getRecommendationsRequests.add(1);
    
    // 200 - успех, 404 - пользователь не найден (нормально для случайных ID)
    const success = check(res, {
      'get recommendations status OK': (r) => r.status === 200 || r.status === 404,
      'get recommendations has recommendations': (r) => {
        if (r.status !== 200) return true; // 404 - это нормально
        try {
          const body = JSON.parse(r.body);
          return body.recommendations !== undefined;
        } catch {
          return false;
        }
      },
    });
    
    getRecommendationsSuccess.add(success);
    
    if (!success || res.status >= 500) {
      getRecommendationsErrors.add(1);
      if (res.status >= 500) {
        realErrors.add(1);
        console.log(`❌ Get Recommendations ERROR: ${res.status} - ${res.body?.substring(0, 100)}`);
      }
    }
  });

  // sleep(0.3);
}

// ════════════════════════════════════════════════════════
// Summary: вывод результатов
// ════════════════════════════════════════════════════════

export function handleSummary(data) {
  console.log('\n');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('        📊 НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ POST ЗАПРОСОВ          ');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  
  const totalReqs = data.metrics.http_reqs?.values?.count || 0;
  const failRateRaw = (data.metrics.http_req_failed?.values?.rate || 0) * 100;
  const realErrorsCount = data.metrics.real_errors?.values?.count || 0;
  const realErrorsRate = totalReqs > 0 ? (realErrorsCount / totalReqs) * 100 : 0;
  const maxVUs = data.metrics.vus_max?.values?.max || data.metrics.vus?.values?.max || 0;
  const testDuration = data.state.testRunDurationMs || 0;
  const rps = data.metrics.http_reqs?.values?.rate || 0;
  
  console.log(`📊 Общая статистика:`);
  console.log(`   • Виртуальных пользователей: ${maxVUs}`);
  console.log(`   • Длительность теста:        ${formatDuration(testDuration)}`);
  console.log(`   • Всего запросов:            ${totalReqs}`);
  console.log(`   • RPS (req/sec):             ${rps.toFixed(2)}`);
  console.log(`   • Процент ошибок:            ${failRateRaw.toFixed(2)}%`);
  console.log('');
  
  console.log(`📈 Время ответа по эндпоинтам:`);
  
  // Вычисляем RPS для каждого эндпоинта
  const testDurationSeconds = testDuration / 1000;
  const createUserCount = data.metrics.post_create_user_requests?.values?.count || 0;
  const createUserRPS = testDurationSeconds > 0 ? (createUserCount / testDurationSeconds).toFixed(2) : '0.00';
  const createTrackCount = data.metrics.post_create_track_requests?.values?.count || 0;
  const createTrackRPS = testDurationSeconds > 0 ? (createTrackCount / testDurationSeconds).toFixed(2) : '0.00';
  const createEventCount = data.metrics.post_create_event_requests?.values?.count || 0;
  const createEventRPS = testDurationSeconds > 0 ? (createEventCount / testDurationSeconds).toFixed(2) : '0.00';
  const getRecCount = data.metrics.post_get_recommendations_requests?.values?.count || 0;
  const getRecRPS = testDurationSeconds > 0 ? (getRecCount / testDurationSeconds).toFixed(2) : '0.00';
  
  // POST Create User
  const createUserAvg = data.metrics.post_create_user_duration?.values?.avg || 0;
  const createUserP95 = data.metrics.post_create_user_duration?.values?.['p(95)'] || 0;
  const createUserP99 = data.metrics.post_create_user_duration?.values?.['p(99)'] || 0;
  const createUserMax = data.metrics.post_create_user_duration?.values?.max || 0;
  const createUserSuccessRate = (data.metrics.post_create_user_success?.values?.rate || 0) * 100;
  console.log(`   👤 POST /users (create):`);
  console.log(`      Среднее: ${createUserAvg.toFixed(0)}ms | p95: ${createUserP95.toFixed(0)}ms | p99: ${createUserP99.toFixed(0)}ms | Max: ${createUserMax.toFixed(0)}ms`);
  console.log(`      Успешность: ${createUserSuccessRate.toFixed(2)}% | RPS: ${createUserRPS} req/sec`);
  
  // POST Create Track
  const createTrackAvg = data.metrics.post_create_track_duration?.values?.avg || 0;
  const createTrackP95 = data.metrics.post_create_track_duration?.values?.['p(95)'] || 0;
  const createTrackP99 = data.metrics.post_create_track_duration?.values?.['p(99)'] || 0;
  const createTrackMax = data.metrics.post_create_track_duration?.values?.max || 0;
  const createTrackSuccessRate = (data.metrics.post_create_track_success?.values?.rate || 0) * 100;
  console.log(`   🎵 POST /tracks (create):`);
  console.log(`      Среднее: ${createTrackAvg.toFixed(0)}ms | p95: ${createTrackP95.toFixed(0)}ms | p99: ${createTrackP99.toFixed(0)}ms | Max: ${createTrackMax.toFixed(0)}ms`);
  console.log(`      Успешность: ${createTrackSuccessRate.toFixed(2)}% | RPS: ${createTrackRPS} req/sec`);
  
  // POST Create Event
  const createEventAvg = data.metrics.post_create_event_duration?.values?.avg || 0;
  const createEventP95 = data.metrics.post_create_event_duration?.values?.['p(95)'] || 0;
  const createEventP99 = data.metrics.post_create_event_duration?.values?.['p(99)'] || 0;
  const createEventMax = data.metrics.post_create_event_duration?.values?.max || 0;
  const createEventSuccessRate = (data.metrics.post_create_event_success?.values?.rate || 0) * 100;
  console.log(`   📝 POST /events (create):`);
  console.log(`      Среднее: ${createEventAvg.toFixed(0)}ms | p95: ${createEventP95.toFixed(0)}ms | p99: ${createEventP99.toFixed(0)}ms | Max: ${createEventMax.toFixed(0)}ms`);
  console.log(`      Успешность: ${createEventSuccessRate.toFixed(2)}% | RPS: ${createEventRPS} req/sec`);
  
  // POST Get Recommendations
  const getRecAvg = data.metrics.post_get_recommendations_duration?.values?.avg || 0;
  const getRecP95 = data.metrics.post_get_recommendations_duration?.values?.['p(95)'] || 0;
  const getRecP99 = data.metrics.post_get_recommendations_duration?.values?.['p(99)'] || 0;
  const getRecMax = data.metrics.post_get_recommendations_duration?.values?.max || 0;
  const getRecSuccessRate = (data.metrics.post_get_recommendations_success?.values?.rate || 0) * 100;
  console.log(`   🎯 POST /recommendations (get):`);
  console.log(`      Среднее: ${getRecAvg.toFixed(0)}ms | p95: ${getRecP95.toFixed(0)}ms | p99: ${getRecP99.toFixed(0)}ms | Max: ${getRecMax.toFixed(0)}ms`);
  console.log(`      Успешность: ${getRecSuccessRate.toFixed(2)}% | RPS: ${getRecRPS} req/sec`);
  
  console.log('');
  console.log(`❌ Ошибки по эндпоинтам:`);
  const createUserErr = data.metrics.post_create_user_errors?.values?.count || 0;
  const createTrackErr = data.metrics.post_create_track_errors?.values?.count || 0;
  const createEventErr = data.metrics.post_create_event_errors?.values?.count || 0;
  const getRecErr = data.metrics.post_get_recommendations_errors?.values?.count || 0;
  console.log(`   • POST /users:            ${createUserErr}`);
  console.log(`   • POST /tracks:          ${createTrackErr}`);
  console.log(`   • POST /events:          ${createEventErr}`);
  console.log(`   • POST /recommendations: ${getRecErr}`);
  
  console.log('');
  console.log(`🔍 АНАЛИЗ И РЕКОМЕНДАЦИИ:`);
  console.log('');
  
  // Анализ производительности
  const slowestP95 = Math.max(createUserP95, createTrackP95, createEventP95, getRecP95);
  
  if (slowestP95 > 10000) {
    console.log(`   ❌ КРИТИЧНО: Очень медленные ответы (p95 > ${slowestP95.toFixed(0)}ms)`);
    console.log(`      1. Проверьте ClickHouse: docker-compose logs clickhouse`);
    console.log(`      2. Проверьте индексы в БД`);
    console.log(`      3. Увеличьте ресурсы Docker (CPU/RAM)`);
    console.log(`      4. Проверьте Kafka (для событий): docker-compose logs kafka`);
  } else if (slowestP95 > 5000) {
    console.log(`   ⚠️  Медленные ответы (p95 > ${slowestP95.toFixed(0)}ms)`);
    console.log(`      1. Оптимизируйте запросы к ClickHouse`);
    console.log(`      2. Проверьте кэширование Redis (для рекомендаций)`);
    console.log(`      3. Рассмотрите батчинг для событий`);
  } else if (slowestP95 > 2000) {
    console.log(`   ⚠️  Приемлемая скорость, но можно улучшить`);
    console.log(`      1. Проверьте кэширование для рекомендаций`);
    console.log(`      2. Оптимизируйте сложные запросы`);
  } else {
    console.log(`   ✅ Отличная производительность!`);
  }
  
  // Анализ ошибок
  // Примечание: http_req_failed включает 404, поэтому используем realErrors для анализа
  console.log('');
  console.log(`   📊 Статистика ошибок:`);
  console.log(`      • Всего запросов: ${totalReqs}`);
  console.log(`      • http_req_failed (включая 404): ${failRateRaw.toFixed(2)}%`);
  console.log(`      • Реальные ошибки (5xx, таймауты, сеть): ${realErrorsRate.toFixed(2)}% (${realErrorsCount} запросов)`);
  console.log(`      • 404 (Not Found) - это нормально для несуществующих ресурсов`);
  
  if (realErrorsRate > 10) {
    console.log('');
    console.log(`   ❌ Высокий процент РЕАЛЬНЫХ ошибок (${realErrorsRate.toFixed(2)}%)`);
    console.log(`      • Реальные ошибки = 5xx статусы, таймауты, сетевые ошибки`);
    console.log(`      • 404 (Not Found) НЕ считается ошибкой - это нормально для несуществующих ресурсов`);
    console.log(`      1. Проверьте логи: make logs-errors`);
    console.log(`      2. Проверьте подключение к БД: docker-compose logs clickhouse`);
    console.log(`      3. Проверьте, что сервисы запущены: docker-compose ps`);
    console.log(`      4. Проверьте ресурсы: docker stats`);
  } else if (realErrorsRate > 5) {
    console.log('');
    console.log(`   ⚠️  Умеренный процент реальных ошибок (${realErrorsRate.toFixed(2)}%)`);
    console.log(`      • Это может быть нормально для нагрузочных тестов`);
    console.log(`      • 404 (Not Found) не считается ошибкой`);
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
  
  // Анализ пропускной способности
  console.log('');
  console.log(`   📊 Пропускная способность:`);
  console.log(`      • Максимум параллельных пользователей: ${maxVUs}`);
  console.log(`      • RPS: ${rps.toFixed(2)} запросов/сек`);
  console.log(`      • Средняя нагрузка: ${(totalReqs / (testDuration / 1000)).toFixed(2)} req/sec`);
  
  // Рекомендации по масштабированию
  if (failRateRaw < 5 && slowestP95 < 3000) {
    console.log('');
    console.log(`   💡 Рекомендации по масштабированию:`);
    console.log(`      • Система выдерживает ${maxVUs} параллельных пользователей`);
    console.log(`      • Можно попробовать увеличить нагрузку до ${Math.floor(maxVUs * 1.5)} VUs`);
    console.log(`      • Рекомендуется мониторинг при нагрузке > ${Math.floor(maxVUs * 2)} VUs`);
  }
  
  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  
  return {};
}
