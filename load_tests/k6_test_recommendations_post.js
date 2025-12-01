import http from 'k6/http';
import { check } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { textSummary, BASE_URL } from './k6_test_events_post.js';

const TITLE = "Recommendations POST Load Test Results"

// Кастомные метрики
const recommendationErrors = new Counter('recommendation_errors');
const recommendationSuccessRate = new Rate('recommendation_success_rate');
const recommendationResponseTime = new Trend('recommendation_response_time');

export const options = {
  stages: [{ duration: '1m', target: 100 }],
  thresholds: {
    http_req_duration: ['p(95)<2000', 'p(99)<5000'], // 95% запросов < 2s, 99% < 5s (рекомендации медленнее)
    http_req_failed: ['rate<0.05'],                    // Меньше 5% ошибок
    recommendation_success_rate: ['rate>0.95'],       // Больше 95% успешных запросов
  },
};

const API_URL = `${BASE_URL}/api/v1/recommendations`;

// Генерация случайных данных для запроса рекомендаций
function generateRecommendationRequest() {
  const user_id = Math.floor(Math.random() * 10000) + 1;
  const top_n = [5, 10, 20][Math.floor(Math.random() * 3)];
  const exclude_listened = Math.random() > 0.5;
  const include_performance_metrics = Math.random() > 0.7; // Иногда включаем метрики

  return {
    user_id: user_id,
    top_n: top_n,
    exclude_listened: exclude_listened,
    include_performance_metrics: include_performance_metrics,
  };
}

export default function () {
  const payload = JSON.stringify(generateRecommendationRequest());
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    // timeout: '30s', // Увеличенный таймаут для рекомендаций
  };

  const startTime = Date.now();
  const response = http.post(API_URL, payload, params);
  const responseTime = Date.now() - startTime;

  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response has user_id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.user_id !== undefined;
      } catch (e) {
        return false;
      }
    },
    'response has recommendations': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body.recommendations);
      } catch (e) {
        return false;
      }
    },
    'response has algorithm': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.algorithm !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  recommendationSuccessRate.add(success);
  recommendationResponseTime.add(responseTime);
  
  if (!success) {
    recommendationErrors.add(1);
  }

}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }, TITLE, 'recommendation_success_rate'),
  };
}

