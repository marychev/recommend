/**
 * K6 Быстрый тест (5 минут)
 * 
 * Упрощенная версия полного теста для быстрой проверки
 * Включает все три шага: авторизация, пользователь, рекомендации
 * 
 * Запуск:
 * k6 run load_tests/k6_quick_test.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Trend, Counter, Rate } from 'k6/metrics';

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

// Метрики
const scenarioDuration = new Trend('scenario_duration', true);
const scenarioSuccessRate = new Rate('scenario_success_rate');
const authDuration = new Trend('auth_duration', true);
const getUserDuration = new Trend('get_user_duration', true);
const recommendationsDuration = new Trend('recommendations_duration', true);

// Конфигурация
export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Разогрев до 10 пользователей
    { duration: '2m', target: 30 },    // Рост до 30
    { duration: '1m', target: 30 },    // Удержание 30
    { duration: '30s', target: 50 },   // Рост до 50
    { duration: '1m', target: 50 },    // Удержание 50
    { duration: '30s', target: 0 },    // Снижение
  ],
  thresholds: {
    'scenario_duration': ['p(95)<5000'],
    'scenario_success_rate': ['rate>0.90'],
    'http_req_duration': ['p(95)<3000'],
  },
};

function getRandomUserId() {
  return Math.floor(Math.random() * 1000) + 1;
}

export default function () {
  const startTime = Date.now();
  const userId = getRandomUserId();
  let success = true;
  
  // 1. Авторизация
  const authResult = group('Authorization', function () {
    const authPayload = JSON.stringify({
      username: `user_${userId}`,
      password: `password_${userId}`,
    });
    
    const authStart = Date.now();
    const authResponse = http.post(
      `${BASE_URL}/api/v1/auth/login`,
      authPayload,
      { headers: { 'Content-Type': 'application/json' } }
    );
    authDuration.add(Date.now() - authStart);
    
    const authSuccess = check(authResponse, {
      'auth status is 200': (r) => r.status === 200,
    });
    
    if (authSuccess && authResponse.status === 200) {
      try {
        const body = JSON.parse(authResponse.body);
        return { success: true, token: body.access_token };
      } catch (e) {
        return { success: false };
      }
    }
    return { success: false };
  });
  
  if (!authResult.success) {
    scenarioSuccessRate.add(false);
    sleep(1);
    return;
  }
  
  sleep(0.1);
  
  // 2. Получение пользователя
  const getUserResult = group('Get_User', function () {
    const getUserStart = Date.now();
    const getUserResponse = http.get(
      `${BASE_URL}/api/v1/users/${userId}`,
      { headers: { 'Authorization': `Bearer ${authResult.token}` } }
    );
    getUserDuration.add(Date.now() - getUserStart);
    
    const getUserSuccess = check(getUserResponse, {
      'get_user status is 200': (r) => r.status === 200,
    });
    
    return { success: getUserSuccess };
  });
  
  if (!getUserResult.success) {
    scenarioSuccessRate.add(false);
    sleep(1);
    return;
  }
  
  sleep(0.1);
  
  // 3. Получение рекомендаций
  const recResult = group('Get_Recommendations', function () {
    const recPayload = JSON.stringify({
      user_id: userId,
      top_n: 10,
      exclude_listened: true,
    });
    
    const recStart = Date.now();
    const recResponse = http.post(
      `${BASE_URL}/api/v1/recommendations`,
      recPayload,
      { headers: { 
        'Authorization': `Bearer ${authResult.token}`,
        'Content-Type': 'application/json',
      }}
    );
    recommendationsDuration.add(Date.now() - recStart);
    
    const recSuccess = check(recResponse, {
      'recommendations status is 200': (r) => r.status === 200,
    });
    
    return { success: recSuccess };
  });
  
  const duration = Date.now() - startTime;
  scenarioDuration.add(duration);
  scenarioSuccessRate.add(success && recResult.success);
  
  sleep(Math.random() * 1 + 1);
}

export function handleSummary(data) {
  const stats = {
    duration: data.state.testRunDurationMs / 1000,
    iterations: data.metrics.iterations?.values?.count || 0,
    requests: data.metrics.http_reqs?.values?.count || 0,
    successRate: (data.metrics.scenario_success_rate?.values?.rate || 0) * 100,
    avgScenario: data.metrics.scenario_duration?.values?.avg || 0,
    p95Scenario: data.metrics.scenario_duration?.values['p(95)'] || 0,
  };
  
  console.log('\n═══════════════════════════════════════════════════════════');
  console.log('  📊 БЫСТРЫЙ ТЕСТ - РЕЗУЛЬТАТЫ');
  console.log('═══════════════════════════════════════════════════════════\n');
  console.log(`  Длительность:        ${stats.duration.toFixed(0)}s`);
  console.log(`  Итераций:            ${stats.iterations}`);
  console.log(`  Запросов:            ${stats.requests}`);
  console.log(`  Success Rate:        ${stats.successRate.toFixed(2)}%`);
  console.log(`  Avg Scenario:        ${stats.avgScenario.toFixed(0)}ms`);
  console.log(`  P95 Scenario:        ${stats.p95Scenario.toFixed(0)}ms`);
  console.log('\n═══════════════════════════════════════════════════════════\n');
  
  return {
    'summary_quick_test.json': JSON.stringify(data, null, 2),
  };
}
