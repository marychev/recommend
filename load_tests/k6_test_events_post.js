import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export const EVENTS_STAGES_OPTIONS = [
  // { duration: '10s', target: 5 },    // Разогрев: N пользователей за 30 сек
  // { duration: '30s', target: 10 },   // Нормальная нагрузка: N пользователей
  { duration: '1m', target: 100 },       // Высокая нагрузка: N пользователей
  // { duration: '30s', target: 0 },    // Снижение нагрузки
];

// Кастомные метрики
const TITLE = "Events POST Load Test Results"
const eventErrors = new Counter('event_errors');
const eventSuccessRate = new Rate('event_success_rate');
const eventResponseTime = new Trend('event_response_time');

export const options = {
  stages: EVENTS_STAGES_OPTIONS,
  thresholds: {
    // Реалистичные пороги для нагрузки 100 VUs с учетом батчинга и очереди событий
    // Events быстрее, так как отправляются в очередь асинхронно
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],  // 95% запросов < 1s, 99% < 2s
    http_req_failed: ['rate<0.05'],                  // Меньше 5% ошибок
    event_success_rate: ['rate>0.95'],               // Больше 95% успешных запросов
  },
};

const API_URL = `${BASE_URL}/api/v1/events`;

// Генерация случайных данных для события
function generateEventData() {
  const user_id = Math.floor(Math.random() * 10000) + 1;
  const track_id = Math.floor(Math.random() * 50000) + 1;
  const actionTypes = ['play', 'like', 'dislike', 'skip', 'add_to_playlist', 'share'];
  const action_type = actionTypes[Math.floor(Math.random() * actionTypes.length)];
  const listen_duration_seconds = action_type === 'play' 
    ? Math.floor(Math.random() * 300) + 10 
    : null;

  return {
    user_id: user_id,
    track_id: track_id,
    action_type: action_type,
    listen_duration_seconds: listen_duration_seconds,
  };
}

export default function () {
  const payload = JSON.stringify(generateEventData());
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: '30s',  // Таймаут для запроса (30 секунд)
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
        return body.user_id !== undefined;
      } catch (e) {
        return false;
      }
    },
    'response has track_id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.track_id !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  // Обновление метрик
  eventSuccessRate.add(success);
  eventResponseTime.add(responseTime);
  
  if (!success) {
    eventErrors.add(1);
  }

}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }, TITLE, 'event_success_rate'),
  };
}

export function textSummary(data, options, title = TITLE, successRateMetricName = 'event_success_rate') {
  const indent = options.indent || '';
  let summary = '\n';
  summary += `${indent}${title}\n`;
  summary += `${indent}${'='.repeat(title.length)}\n\n`;
  
  // Безопасное получение значений метрик
  const httpReqs = data.metrics.http_reqs?.values?.count || 0;
  const successRate = data.metrics[successRateMetricName]?.values?.rate || 0;
  const errorRate = data.metrics.http_req_failed?.values?.rate || 0;
  const avgDuration = data.metrics.http_req_duration?.values?.avg || 0;
  const p95Duration = data.metrics.http_req_duration?.values?.['p(95)'] || 0;
  const p99Duration = data.metrics.http_req_duration?.values?.['p(99)'] || 0;
  const rps = data.metrics.http_reqs?.values?.rate || 0;

  summary += `${indent}RPS (req/sec): ${rps.toFixed(2)} req/sec\n`;
  summary += `${indent}Total Requests: ${httpReqs}\n`;
  summary += `${indent}Success Rate: ${(successRate * 100).toFixed(2)}%\n`;
  summary += `${indent}Error Rate: ${(errorRate * 100).toFixed(2)}%\n`;
  summary += `${indent}Avg Response Time: ${avgDuration.toFixed(2)}ms\n`;
  summary += `${indent}P95 Response Time: ${p95Duration.toFixed(2)}ms\n`;
  summary += `${indent}P99 Response Time: ${p99Duration.toFixed(2)}ms\n`;
  return summary;
}

