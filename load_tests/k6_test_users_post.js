import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { textSummary, EVENTS_STAGES_OPTIONS, BASE_URL } from './k6_test_events_post.js';

// Кастомные метрики
const TITLE = "Users POST Load Test Results"
const userErrors = new Counter('user_errors');
const userSuccessRate = new Rate('user_success_rate');
const userResponseTime = new Trend('user_response_time');

export const options = {
  stages: EVENTS_STAGES_OPTIONS,
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% запросов < 500ms, 99% < 1000ms
    http_req_failed: ['rate<0.05'],                  // Меньше 5% ошибок
    user_success_rate: ['rate>0.95'],                // Больше 95% успешных запросов
  },
};

const API_URL = `${BASE_URL}/api/v1/users`;

// Генерация случайных данных для пользователя
function generateUserData() {
  const usernames = [
    'john_doe', 'jane_smith', 'alex_jones', 'maria_garcia', 'david_wilson',
    'sarah_brown', 'michael_taylor', 'emily_davis', 'james_miller', 'lisa_anderson'
  ];
  const countries = ['Russia', 'USA', 'UK', 'Germany', 'France', 'Japan', 'Canada', 'Australia'];
  
  const username = `${usernames[Math.floor(Math.random() * usernames.length)]}_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
  const email = `${username.replace(/[^a-z0-9]/g, '')}@example.com`;
  const age = Math.floor(Math.random() * 60) + 18; // 18-78 лет
  const country = countries[Math.floor(Math.random() * countries.length)];

  return {
    username: username,
    email: email,
    age: age,
    country: country,
  };
}

export default function () {
  const payload = JSON.stringify(generateUserData());
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: '60s', // Увеличенный таймаут для предотвращения таймаутов при высокой нагрузке
  };

  const startTime = Date.now();
  const response = http.post(API_URL, payload, params);
  const responseTime = Date.now() - startTime;

  // Проверка ответа
  const success = check(response, {
    'status is 201': (r) => r.status === 201,
    'response has user_id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.user_id !== undefined && body.user_id > 0;
      } catch (e) {
        return false;
      }
    },
    'response has username': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.username !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  // Обновление метрик
  userSuccessRate.add(success);
  userResponseTime.add(responseTime);
  
  if (!success) {
    userErrors.add(1);
  }

  // sleep(2); // Пауза между запросами (создание пользователей реже)
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }, TITLE),
  };
}
