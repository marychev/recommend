/**
 * k6 Базовый сценарий нагрузочного тестирования
 * 
 * Тестирует основные эндпоинты API:
 * - GET /api/v1/users
 * - GET /api/v1/tracks
 * - GET /api/v1/recommendations/{user_id}
 * 
 * Запуск: k6 run load_tests/k6_basic_load_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Кастомные метрики
const errorRate = new Rate('errors');
const usersResponseTime = new Trend('users_response_time');
const tracksResponseTime = new Trend('tracks_response_time');
const recommendationsResponseTime = new Trend('recommendations_response_time');

// Конфигурация теста
export const options = {
  stages: [
    { duration: '1m', target: 50 },   // Разогрев: 50 пользователей
    { duration: '3m', target: 100 },  // Рост до 100 пользователей
    { duration: '5m', target: 100 },  // Стабильная нагрузка
    { duration: '2m', target: 200 },  // Пиковая нагрузка
    { duration: '3m', target: 50 },   // Снижение нагрузки
    { duration: '1m', target: 0 },    // Завершение
  ],
  thresholds: {
    'http_req_duration': ['p(95)<2000', 'p(99)<5000'], // 95% запросов < 2s, 99% < 5s
    'http_req_failed': ['rate<0.05'],                   // Менее 5% ошибок
    'errors': ['rate<0.05'],
    'users_response_time': ['p(95)<1000'],
    'tracks_response_time': ['p(95)<1000'],
    'recommendations_response_time': ['p(95)<3000'],    // Рекомендации могут быть медленнее
  },
};

// Базовый URL API
const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

// Диапазоны ID для тестирования
const USER_ID_MIN = 1;
const USER_ID_MAX = 100000;
const TRACK_ID_MIN = 1;
const TRACK_ID_MAX = 50000;

/**
 * Получает случайный ID пользователя
 */
function getRandomUserId() {
  return Math.floor(Math.random() * (USER_ID_MAX - USER_ID_MIN + 1)) + USER_ID_MIN;
}

/**
 * Получает случайный ID трека
 */
function getRandomTrackId() {
  return Math.floor(Math.random() * (TRACK_ID_MAX - TRACK_ID_MIN + 1)) + TRACK_ID_MIN;
}

/**
 * Тестирование GET /api/v1/users
 */
function testGetUsers() {
  const url = `${BASE_URL}/api/v1/users?limit=50&offset=${Math.floor(Math.random() * 1000)}`;
  const res = http.get(url, { tags: { name: 'GetUsers' } });
  
  const success = check(res, {
    'GET /users status is 200': (r) => r.status === 200,
    'GET /users returns array': (r) => Array.isArray(JSON.parse(r.body)),
  });
  
  errorRate.add(!success);
  usersResponseTime.add(res.timings.duration);
  
  return res;
}

/**
 * Тестирование GET /api/v1/users/{user_id}
 */
function testGetUser() {
  const userId = getRandomUserId();
  const url = `${BASE_URL}/api/v1/users/${userId}`;
  const res = http.get(url, { tags: { name: 'GetUser' } });
  
  const success = check(res, {
    'GET /users/{id} status is 200 or 404': (r) => r.status === 200 || r.status === 404,
  });
  
  errorRate.add(!success);
  usersResponseTime.add(res.timings.duration);
  
  return res;
}

/**
 * Тестирование GET /api/v1/tracks
 */
function testGetTracks() {
  const url = `${BASE_URL}/api/v1/tracks?limit=50&offset=${Math.floor(Math.random() * 1000)}`;
  const res = http.get(url, { tags: { name: 'GetTracks' } });
  
  const success = check(res, {
    'GET /tracks status is 200': (r) => r.status === 200,
    'GET /tracks returns array': (r) => Array.isArray(JSON.parse(r.body)),
  });
  
  errorRate.add(!success);
  tracksResponseTime.add(res.timings.duration);
  
  return res;
}

/**
 * Тестирование GET /api/v1/tracks/{track_id}
 */
function testGetTrack() {
  const trackId = getRandomTrackId();
  const url = `${BASE_URL}/api/v1/tracks/${trackId}`;
  const res = http.get(url, { tags: { name: 'GetTrack' } });
  
  const success = check(res, {
    'GET /tracks/{id} status is 200 or 404': (r) => r.status === 200 || r.status === 404,
  });
  
  errorRate.add(!success);
  tracksResponseTime.add(res.timings.duration);
  
  return res;
}

/**
 * Тестирование GET /api/v1/recommendations/{user_id}
 */
function testGetRecommendations() {
  const userId = getRandomUserId();
  const url = `${BASE_URL}/api/v1/recommendations/${userId}`;
  const res = http.get(url, { tags: { name: 'GetRecommendations' } });
  
  const success = check(res, {
    'GET /recommendations status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'GET /recommendations has user_id': (r) => {
      if (r.status === 200) {
        const body = JSON.parse(r.body);
        return body.user_id === userId;
      }
      return true;
    },
  });
  
  errorRate.add(!success);
  recommendationsResponseTime.add(res.timings.duration);
  
  return res;
}

/**
 * Тестирование GET /api/v1/users/{user_id}/statistics
 */
function testGetUserStatistics() {
  const userId = getRandomUserId();
  const url = `${BASE_URL}/api/v1/users/${userId}/statistics`;
  const res = http.get(url, { tags: { name: 'GetUserStatistics' } });
  
  const success = check(res, {
    'GET /users/{id}/statistics status is 200 or 404': (r) => r.status === 200 || r.status === 404,
  });
  
  errorRate.add(!success);
  
  return res;
}

/**
 * Тестирование GET /api/v1/tracks/{track_id}/statistics
 */
function testGetTrackStatistics() {
  const trackId = getRandomTrackId();
  const url = `${BASE_URL}/api/v1/tracks/${trackId}/statistics`;
  const res = http.get(url, { tags: { name: 'GetTrackStatistics' } });
  
  const success = check(res, {
    'GET /tracks/{id}/statistics status is 200 or 404': (r) => r.status === 200 || r.status === 404,
  });
  
  errorRate.add(!success);
  
  return res;
}

/**
 * Основной сценарий тестирования
 */
export default function () {
  // Имитация реального поведения пользователя
  const scenario = Math.random();
  
  if (scenario < 0.3) {
    // 30% - просмотр списка пользователей
    testGetUsers();
    sleep(1);
    testGetUser();
  } else if (scenario < 0.6) {
    // 30% - просмотр треков
    testGetTracks();
    sleep(1);
    testGetTrack();
    sleep(0.5);
    testGetTrackStatistics();
  } else {
    // 40% - получение рекомендаций (самый частый сценарий)
    testGetRecommendations();
    sleep(2);
    testGetUserStatistics();
  }
  
  sleep(1);
}

/**
 * Функция, выполняемая в конце теста
 */
export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'summary.json': JSON.stringify(data),
  };
}

function textSummary(data, options) {
  const indent = options.indent || '';
  const enableColors = options.enableColors || false;
  
  let output = '\n' + indent + '═══════════════════════════════════════════════════════\n';
  output += indent + '              📊 РЕЗУЛЬТАТЫ НАГРУЗОЧНОГО ТЕСТА\n';
  output += indent + '═══════════════════════════════════════════════════════\n\n';
  
  // Общая статистика
  output += indent + '⏱️  Общее время выполнения: ' + (data.state.testRunDurationMs / 1000).toFixed(2) + 's\n';
  output += indent + '👥 Виртуальных пользователей: ' + data.metrics.vus?.values?.max + '\n';
  output += indent + '📤 Всего запросов: ' + data.metrics.http_reqs?.values?.count + '\n';
  output += indent + '📈 Запросов в секунду: ' + data.metrics.http_reqs?.values?.rate.toFixed(2) + '\n\n';
  
  // Время ответа
  output += indent + '📊 Время ответа (http_req_duration):\n';
  output += indent + '   • Среднее: ' + data.metrics.http_req_duration?.values?.avg.toFixed(2) + 'ms\n';
  output += indent + '   • Медиана: ' + data.metrics.http_req_duration?.values?.med.toFixed(2) + 'ms\n';
  output += indent + '   • 95 перцентиль: ' + data.metrics.http_req_duration?.values?.['p(95)'].toFixed(2) + 'ms\n';
  output += indent + '   • 99 перцентиль: ' + data.metrics.http_req_duration?.values?.['p(99)'].toFixed(2) + 'ms\n\n';
  
  // Ошибки
  const failRate = (data.metrics.http_req_failed?.values?.rate || 0) * 100;
  output += indent + '❌ Процент ошибок: ' + failRate.toFixed(2) + '%\n\n';
  
  output += indent + '═══════════════════════════════════════════════════════\n';
  
  return output;
}

