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

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Базовая нагрузка
    { duration: '10s', target: 500 },  // Резкий скачок до 500 пользователей
    { duration: '1m', target: 500 },   // Удержание пиковой нагрузки
    { duration: '10s', target: 10 },   // Резкое снижение
    { duration: '30s', target: 0 },    // Завершение
  ],
  thresholds: {
    'http_req_duration': ['p(95)<5000'],  // Более мягкие требования при пике
    'http_req_failed': ['rate<0.15'],      // Допускаем до 15% ошибок при пике
    'errors': ['rate<0.15'],
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

function getRandomUserId() {
  return Math.floor(Math.random() * 100000) + 1;
}

function getRandomTrackId() {
  return Math.floor(Math.random() * 50000) + 1;
}

export default function () {
  // Выбираем случайный эндпоинт
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
  
  sleep(0.5);
}

