/**
 * k6 Комплексный тест: Полный пользовательский сценарий
 * 
 * Сценарий:
 * 1. Авторизация (получение токена)
 * 2. Получение данных пользователя
 * 3. Получение рекомендаций для пользователя
 * 
 * Метрики:
 * - Максимальное количество пользователей (Spike Test)
 * - Оптимальное количество пользователей (Load Test + Stress Test)
 * - Объем данных (размер запросов и ответов)
 * - Время выполнения каждого шага
 * 
 * Запуск:
 * k6 run load_tests/k6_full_user_scenario_test.js
 * k6 run load_tests/k6_full_user_scenario_test.js --env API_URL=http://localhost:8000
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Trend, Counter, Rate, Gauge } from 'k6/metrics';
import { htmlReport } from "https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js";
import { textSummary } from "https://jslib.k6.io/k6-summary/0.0.1/index.js";

// ════════════════════════════════════════════════════════
// Конфигурация
// ════════════════════════════════════════════════════════

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

// ════════════════════════════════════════════════════════
// Кастомные метрики
// ════════════════════════════════════════════════════════

// Метрики времени для каждого шага
const authDuration = new Trend('auth_duration', true);
const getUserDuration = new Trend('get_user_duration', true);
const getRecommendationsDuration = new Trend('get_recommendations_duration', true);
const fullScenarioDuration = new Trend('full_scenario_duration', true);

// Метрики размера данных (в байтах)
const authRequestSize = new Trend('auth_request_size_bytes', true);
const authResponseSize = new Trend('auth_response_size_bytes', true);
const getUserResponseSize = new Trend('get_user_response_size_bytes', true);
const recommendationsRequestSize = new Trend('recommendations_request_size_bytes', true);
const recommendationsResponseSize = new Trend('recommendations_response_size_bytes', true);
const totalDataTransferred = new Trend('total_data_transferred_bytes', true);

// Метрики успешности
const authSuccessRate = new Rate('auth_success_rate');
const getUserSuccessRate = new Rate('get_user_success_rate');
const recommendationsSuccessRate = new Rate('recommendations_success_rate');
const scenarioSuccessRate = new Rate('scenario_success_rate');

// Метрики качества рекомендаций
const recommendationsCount = new Trend('recommendations_count', true);
const cacheHitRate = new Rate('cache_hit_rate');

// Счетчики
const successfulScenarios = new Counter('successful_scenarios');
const failedScenarios = new Counter('failed_scenarios');
const authErrors = new Counter('auth_errors');
const getUserErrors = new Counter('get_user_errors');
const recommendationsErrors = new Counter('recommendations_errors');

// Текущая нагрузка
const currentVUs = new Gauge('current_virtual_users');

// ════════════════════════════════════════════════════════
// Конфигурация теста
// ════════════════════════════════════════════════════════

export const options = {
  scenarios: {
    // 1. WARM UP - Прогрев системы
    warmup: {
      executor: 'constant-vus',
      vus: 5,
      duration: '1m',
      startTime: '0s',
      tags: { test_type: 'warmup' },
    },
    
    // 2. LOAD TEST - Оптимальная нагрузка
    // Определяем оптимальное количество пользователей
    load_test: {
      executor: 'ramping-vus',
      startVUs: 10,
      stages: [
        { duration: '2m', target: 20 },   // Постепенный рост до 20
        { duration: '5m', target: 20 },   // Удержание 20 пользователей
        { duration: '2m', target: 50 },   // Рост до 50
        { duration: '5m', target: 50 },   // Удержание 50 пользователей
        { duration: '2m', target: 20 },   // Снижение
      ],
      startTime: '1m',
      tags: { test_type: 'load' },
    },
    
    // 3. STRESS TEST - Поиск точки отказа
    // Определяем максимальное количество пользователей
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 50,
      stages: [
        { duration: '2m', target: 100 },  // Рост до 100
        { duration: '3m', target: 100 },  // Удержание
        { duration: '2m', target: 150 },  // Рост до 150
        { duration: '3m', target: 150 },  // Удержание
        { duration: '2m', target: 200 },  // Рост до 200
        { duration: '3m', target: 200 },  // Удержание
        { duration: '2m', target: 0 },    // Постепенное снижение
      ],
      startTime: '17m',
      tags: { test_type: 'stress' },
    },
    
    // 4. SPIKE TEST - Резкий скачок нагрузки
    // Проверяем устойчивость к резким скачкам
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 10,
      stages: [
        { duration: '10s', target: 10 },   // Нормальная нагрузка
        { duration: '30s', target: 300 },  // Резкий скачок!
        { duration: '2m', target: 300 },   // Удержание пиковой нагрузки
        { duration: '30s', target: 10 },   // Резкое снижение
        { duration: '1m', target: 10 },    // Восстановление
      ],
      startTime: '36m',
      tags: { test_type: 'spike' },
    },
    
    // 5. BREAKPOINT TEST - Поиск точки отказа
    // Постепенно увеличиваем нагрузку до полного отказа
    breakpoint_test: {
      executor: 'ramping-arrival-rate',
      startRate: 50,
      timeUnit: '1s',
      preAllocatedVUs: 500,
      maxVUs: 1000,
      stages: [
        { duration: '2m', target: 100 },   // 100 req/s
        { duration: '2m', target: 200 },   // 200 req/s
        { duration: '2m', target: 300 },   // 300 req/s
        { duration: '2m', target: 400 },   // 400 req/s
        { duration: '2m', target: 500 },   // 500 req/s
      ],
      startTime: '41m',
      tags: { test_type: 'breakpoint' },
    },
  },
  
  thresholds: {
    // Общие пороги
    'http_req_duration': ['p(95)<3000', 'p(99)<5000'],
    'http_req_failed': ['rate<0.1'],  // Не более 10% ошибок
    
    // Пороги для каждого шага
    'auth_duration': ['p(95)<500', 'avg<300'],
    'get_user_duration': ['p(95)<1000', 'avg<500'],
    'get_recommendations_duration': ['p(95)<3000', 'avg<2000'],
    'full_scenario_duration': ['p(95)<5000', 'avg<3000'],
    
    // Пороги успешности
    'auth_success_rate': ['rate>0.95'],
    'get_user_success_rate': ['rate>0.95'],
    'recommendations_success_rate': ['rate>0.95'],
    'scenario_success_rate': ['rate>0.90'],
    
    // Порог для кэша
    'cache_hit_rate': ['rate>0.2'],  // Минимум 20% попаданий
  },
};

// ════════════════════════════════════════════════════════
// Тестовые данные
// ════════════════════════════════════════════════════════

// Генерация случайных данных пользователя
function getRandomUserId() {
  return Math.floor(Math.random() * 1000) + 1;
}

function getRandomCredentials() {
  const userId = getRandomUserId();
  return {
    username: `user_${userId}`,
    password: `password_${userId}`,
    user_id: userId
  };
}

// Вычисление размера строки в байтах (UTF-8)
function getByteSize(str) {
  if (!str) return 0;
  // Подсчитываем байты для UTF-8 строки
  let bytes = 0;
  for (let i = 0; i < str.length; i++) {
    const code = str.charCodeAt(i);
    if (code < 0x80) {
      bytes += 1;
    } else if (code < 0x800) {
      bytes += 2;
    } else if (code < 0x10000) {
      bytes += 3;
    } else {
      bytes += 4;
    }
  }
  return bytes;
}

// ════════════════════════════════════════════════════════
// Основной сценарий теста
// ════════════════════════════════════════════════════════

export default function () {
  // Обновляем метрику текущих VU
  currentVUs.add(__VU);
  
  const scenarioStartTime = Date.now();
  let totalBytes = 0;
  let scenarioSuccess = true;
  
  // Генерируем данные для теста
  const credentials = getRandomCredentials();
  let authToken = null;
  let userId = credentials.user_id;
  
  // ════════════════════════════════════════════════════════
  // ШАГ 1: АВТОРИЗАЦИЯ
  // ════════════════════════════════════════════════════════
  
  const authResult = group('01_Authorization', function () {
    const authPayload = JSON.stringify({
      username: credentials.username,
      password: credentials.password,
    });
    
    const authParams = {
      headers: {
        'Content-Type': 'application/json',
      },
      tags: { name: 'Auth' },
    };
    
    // Измеряем размер запроса
    const requestSize = getByteSize(authPayload);
    authRequestSize.add(requestSize);
    totalBytes += requestSize;
    
    const authResponse = http.post(
      `${BASE_URL}/api/v1/auth/login`,
      authPayload,
      authParams
    );
    
    // Измеряем размер ответа
    const responseSize = authResponse.body ? getByteSize(authResponse.body) : 0;
    authResponseSize.add(responseSize);
    totalBytes += responseSize;
    
    // Записываем время выполнения
    authDuration.add(authResponse.timings.duration);
    
    // Проверяем результат
    const authSuccess = check(authResponse, {
      'auth: status is 200': (r) => r.status === 200,
      'auth: has token': (r) => {
        if (r.status === 200) {
          try {
            const body = JSON.parse(r.body);
            return body.access_token !== undefined;
          } catch (e) {
            return false;
          }
        }
        return false;
      },
    });
    
    authSuccessRate.add(authSuccess);
    
    if (authSuccess && authResponse.status === 200) {
      try {
        const body = JSON.parse(authResponse.body);
        authToken = body.access_token;
        return { success: true, token: authToken };
      } catch (e) {
        authErrors.add(1);
        return { success: false, error: 'Failed to parse auth response' };
      }
    } else {
      authErrors.add(1);
      scenarioSuccess = false;
      return { success: false, error: `Auth failed with status ${authResponse.status}` };
    }
  });
  
  // Если авторизация не удалась, прерываем сценарий
  if (!authResult.success) {
    failedScenarios.add(1);
    scenarioSuccessRate.add(false);
    sleep(1);
    return;
  }
  
  authToken = authResult.token;
  
  // Небольшая пауза между запросами
  sleep(0.1);
  
  // ════════════════════════════════════════════════════════
  // ШАГ 2: ПОЛУЧЕНИЕ ДАННЫХ ПОЛЬЗОВАТЕЛЯ
  // ════════════════════════════════════════════════════════
  
  const getUserResult = group('02_Get_User_Data', function () {
    const getUserParams = {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      tags: { name: 'GetUser' },
    };
    
    const getUserResponse = http.get(
      `${BASE_URL}/api/v1/users/${userId}`,
      getUserParams
    );
    
    // Измеряем размер ответа
    const responseSize = getUserResponse.body ? getByteSize(getUserResponse.body) : 0;
    getUserResponseSize.add(responseSize);
    totalBytes += responseSize;
    
    // Записываем время выполнения
    getUserDuration.add(getUserResponse.timings.duration);
    
    // Проверяем результат
    const getUserSuccess = check(getUserResponse, {
      'get_user: status is 200': (r) => r.status === 200,
      'get_user: has user data': (r) => {
        if (r.status === 200) {
          try {
            const body = JSON.parse(r.body);
            return body.user_id !== undefined;
          } catch (e) {
            return false;
          }
        }
        return false;
      },
    });
    
    getUserSuccessRate.add(getUserSuccess);
    
    if (!getUserSuccess) {
      getUserErrors.add(1);
      scenarioSuccess = false;
      return { success: false, error: `GetUser failed with status ${getUserResponse.status}` };
    }
    
    return { success: true };
  });
  
  // Если получение пользователя не удалось, прерываем сценарий
  if (!getUserResult.success) {
    failedScenarios.add(1);
    scenarioSuccessRate.add(false);
    sleep(1);
    return;
  }
  
  // Небольшая пауза между запросами
  sleep(0.1);
  
  // ════════════════════════════════════════════════════════
  // ШАГ 3: ПОЛУЧЕНИЕ РЕКОМЕНДАЦИЙ
  // ════════════════════════════════════════════════════════
  
  const getRecommendationsResult = group('03_Get_Recommendations', function () {
    const recommendationsPayload = JSON.stringify({
      user_id: userId,
      top_n: 10,
      exclude_listened: true,
      include_performance_metrics: true,
    });
    
    const recommendationsParams = {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      tags: { name: 'GetRecommendations' },
    };
    
    // Измеряем размер запроса
    const requestSize = getByteSize(recommendationsPayload);
    recommendationsRequestSize.add(requestSize);
    totalBytes += requestSize;
    
    const recommendationsResponse = http.post(
      `${BASE_URL}/api/v1/recommendations`,
      recommendationsPayload,
      recommendationsParams
    );
    
    // Измеряем размер ответа
    const responseSize = recommendationsResponse.body ? getByteSize(recommendationsResponse.body) : 0;
    recommendationsResponseSize.add(responseSize);
    totalBytes += responseSize;
    
    // Записываем время выполнения
    getRecommendationsDuration.add(recommendationsResponse.timings.duration);
    
    // Проверяем результат
    const recommendationsSuccess = check(recommendationsResponse, {
      'recommendations: status is 200': (r) => r.status === 200,
      'recommendations: has recommendations': (r) => {
        if (r.status === 200) {
          try {
            const body = JSON.parse(r.body);
            return body.recommendations && Array.isArray(body.recommendations);
          } catch (e) {
            return false;
          }
        }
        return false;
      },
    });
    
    recommendationsSuccessRate.add(recommendationsSuccess);
    
    if (recommendationsSuccess && recommendationsResponse.status === 200) {
      try {
        const body = JSON.parse(recommendationsResponse.body);
        
        // Собираем дополнительные метрики
        if (body.recommendations) {
          recommendationsCount.add(body.recommendations.length);
        }
        
        if (body.performance_metrics) {
          const cacheHit = body.performance_metrics.cache_hit || false;
          cacheHitRate.add(cacheHit);
        }
        
        return { success: true };
      } catch (e) {
        recommendationsErrors.add(1);
        scenarioSuccess = false;
        return { success: false, error: 'Failed to parse recommendations response' };
      }
    } else {
      recommendationsErrors.add(1);
      scenarioSuccess = false;
      return { success: false, error: `Recommendations failed with status ${recommendationsResponse.status}` };
    }
  });
  
  // ════════════════════════════════════════════════════════
  // ФИНАЛИЗАЦИЯ СЦЕНАРИЯ
  // ════════════════════════════════════════════════════════
  
  // Записываем общие метрики
  const scenarioDuration = Date.now() - scenarioStartTime;
  fullScenarioDuration.add(scenarioDuration);
  totalDataTransferred.add(totalBytes);
  
  // Обновляем счетчики успешности
  if (scenarioSuccess && getRecommendationsResult.success) {
    successfulScenarios.add(1);
    scenarioSuccessRate.add(true);
  } else {
    failedScenarios.add(1);
    scenarioSuccessRate.add(false);
  }
  
  // Пауза между итерациями (имитируем реальное поведение пользователя)
  sleep(Math.random() * 2 + 1); // Случайная пауза от 1 до 3 секунд
}

// ════════════════════════════════════════════════════════
// Функция обработки результатов
// ════════════════════════════════════════════════════════

export function handleSummary(data) {
  // Выводим детальный отчет в консоль
  printDetailedSummary(data);
  
  // Сохраняем отчеты в разных форматах
  return {
    'summary_full_scenario.json': JSON.stringify(data, null, 2),
    'summary_full_scenario.html': htmlReport(data),
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
  };
}

/**
 * Выводит детальную статистику
 */
function printDetailedSummary(data) {
  const line = '═'.repeat(100);
  const separator = '─'.repeat(100);
  
  console.log('\n' + line);
  console.log('  📊 ДЕТАЛЬНЫЙ АНАЛИЗ ПОЛНОГО ПОЛЬЗОВАТЕЛЬСКОГО СЦЕНАРИЯ');
  console.log(line + '\n');
  
  // ════════════════════════════════════════════════════════
  // 1. ОБЩАЯ СТАТИСТИКА ТЕСТА
  // ════════════════════════════════════════════════════════
  
  console.log('📈 ОБЩАЯ СТАТИСТИКА:\n');
  
  const totalDuration = data.state.testRunDurationMs / 1000;
  const totalIterations = data.metrics.iterations?.values?.count || 0;
  const totalRequests = data.metrics.http_reqs?.values?.count || 0;
  const failedRequests = data.metrics.http_req_failed?.values?.count || 0;
  const avgReqDuration = data.metrics.http_req_duration?.values?.avg || 0;
  
  console.log(`   • Общее время теста:           ${(totalDuration / 60).toFixed(2)} минут`);
  console.log(`   • Всего итераций:              ${totalIterations}`);
  console.log(`   • Всего HTTP запросов:         ${totalRequests}`);
  console.log(`   • Неудачных запросов:          ${failedRequests} (${((failedRequests / totalRequests) * 100).toFixed(2)}%)`);
  console.log(`   • Среднее время запроса:       ${avgReqDuration.toFixed(2)}ms`);
  console.log(`   • Пропускная способность:      ${(totalRequests / totalDuration).toFixed(2)} req/s`);
  
  console.log('\n' + separator + '\n');
  
  // ════════════════════════════════════════════════════════
  // 2. УСПЕШНОСТЬ СЦЕНАРИЕВ
  // ════════════════════════════════════════════════════════
  
  console.log('✅ УСПЕШНОСТЬ ВЫПОЛНЕНИЯ:\n');
  
  const successfulScenariosCount = data.metrics.successful_scenarios?.values?.count || 0;
  const failedScenariosCount = data.metrics.failed_scenarios?.values?.count || 0;
  const totalScenarios = successfulScenariosCount + failedScenariosCount;
  
  const authSuccessRateValue = (data.metrics.auth_success_rate?.values?.rate || 0) * 100;
  const getUserSuccessRateValue = (data.metrics.get_user_success_rate?.values?.rate || 0) * 100;
  const recommendationsSuccessRateValue = (data.metrics.recommendations_success_rate?.values?.rate || 0) * 100;
  const scenarioSuccessRateValue = (data.metrics.scenario_success_rate?.values?.rate || 0) * 100;
  
  console.log(`   • Успешных сценариев:          ${successfulScenariosCount} из ${totalScenarios} (${scenarioSuccessRateValue.toFixed(2)}%)`);
  console.log(`   • Неудачных сценариев:         ${failedScenariosCount} (${((failedScenariosCount / totalScenarios) * 100).toFixed(2)}%)`);
  console.log(`\n   Успешность по шагам:`);
  console.log(`   • Авторизация:                 ${authSuccessRateValue.toFixed(2)}%`);
  console.log(`   • Получение пользователя:      ${getUserSuccessRateValue.toFixed(2)}%`);
  console.log(`   • Получение рекомендаций:      ${recommendationsSuccessRateValue.toFixed(2)}%`);
  
  console.log('\n' + separator + '\n');
  
  // ════════════════════════════════════════════════════════
  // 3. ВРЕМЯ ВЫПОЛНЕНИЯ КАЖДОГО ШАГА
  // ════════════════════════════════════════════════════════
  
  console.log('⏱️  ВРЕМЯ ВЫПОЛНЕНИЯ ШАГОВ:\n');
  
  printMetricStats('   1. Авторизация:              ', data.metrics.auth_duration);
  printMetricStats('   2. Получение пользователя:   ', data.metrics.get_user_duration);
  printMetricStats('   3. Получение рекомендаций:   ', data.metrics.get_recommendations_duration);
  console.log('');
  printMetricStats('   🎯 ПОЛНЫЙ СЦЕНАРИЙ:          ', data.metrics.full_scenario_duration);
  
  console.log('\n' + separator + '\n');
  
  // ════════════════════════════════════════════════════════
  // 4. ОБЪЕМ ПЕРЕДАННЫХ ДАННЫХ
  // ════════════════════════════════════════════════════════
  
  console.log('💾 ОБЪЕМ ДАННЫХ:\n');
  
  const authReqSize = data.metrics.auth_request_size_bytes?.values?.avg || 0;
  const authResSize = data.metrics.auth_response_size_bytes?.values?.avg || 0;
  const getUserResSize = data.metrics.get_user_response_size_bytes?.values?.avg || 0;
  const recReqSize = data.metrics.recommendations_request_size_bytes?.values?.avg || 0;
  const recResSize = data.metrics.recommendations_response_size_bytes?.values?.avg || 0;
  const totalDataAvg = data.metrics.total_data_transferred_bytes?.values?.avg || 0;
  const totalDataSum = data.metrics.total_data_transferred_bytes?.values?.count 
    ? (data.metrics.total_data_transferred_bytes.values.count * totalDataAvg) 
    : 0;
  
  console.log(`   Средний размер на один сценарий:`);
  console.log(`   • Запрос авторизации:          ${formatBytes(authReqSize)}`);
  console.log(`   • Ответ авторизации:           ${formatBytes(authResSize)}`);
  console.log(`   • Ответ с данными пользователя:${formatBytes(getUserResSize)}`);
  console.log(`   • Запрос рекомендаций:         ${formatBytes(recReqSize)}`);
  console.log(`   • Ответ с рекомендациями:      ${formatBytes(recResSize)}`);
  console.log(`   • ИТОГО на сценарий:           ${formatBytes(totalDataAvg)}`);
  console.log(`\n   Суммарно за весь тест:`);
  console.log(`   • Всего передано данных:       ${formatBytes(totalDataSum)}`);
  console.log(`   • Скорость передачи:           ${formatBytes(totalDataSum / totalDuration)}/s`);
  
  console.log('\n' + separator + '\n');
  
  // ════════════════════════════════════════════════════════
  // 5. МЕТРИКИ РЕКОМЕНДАЦИЙ
  // ════════════════════════════════════════════════════════
  
  console.log('🎵 МЕТРИКИ РЕКОМЕНДАЦИЙ:\n');
  
  const avgRecommendations = data.metrics.recommendations_count?.values?.avg || 0;
  const minRecommendations = data.metrics.recommendations_count?.values?.min || 0;
  const maxRecommendations = data.metrics.recommendations_count?.values?.max || 0;
  const cacheHitRateValue = (data.metrics.cache_hit_rate?.values?.rate || 0) * 100;
  
  console.log(`   • Среднее кол-во рекомендаций: ${avgRecommendations.toFixed(1)}`);
  console.log(`   • Минимум рекомендаций:        ${minRecommendations}`);
  console.log(`   • Максимум рекомендаций:       ${maxRecommendations}`);
  console.log(`   • Cache Hit Rate:              ${cacheHitRateValue.toFixed(2)}%`);
  
  console.log('\n' + separator + '\n');
  
  // ════════════════════════════════════════════════════════
  // 6. АНАЛИЗ НАГРУЗКИ ПО ТИПАМ ТЕСТОВ
  // ════════════════════════════════════════════════════════
  
  console.log('🔍 АНАЛИЗ ПО ТИПАМ ТЕСТОВ:\n');
  
  analyzeTestType(data, 'warmup', 'Прогрев');
  analyzeTestType(data, 'load', 'Нагрузочный тест');
  analyzeTestType(data, 'stress', 'Стресс-тест');
  analyzeTestType(data, 'spike', 'Пиковый тест');
  analyzeTestType(data, 'breakpoint', 'Тест точки отказа');
  
  console.log(separator + '\n');
  
  // ════════════════════════════════════════════════════════
  // 7. ВЫВОДЫ И РЕКОМЕНДАЦИИ
  // ════════════════════════════════════════════════════════
  
  console.log('💡 ВЫВОДЫ И РЕКОМЕНДАЦИИ:\n');
  
  const recommendations = [];
  
  // Определяем оптимальное количество пользователей
  const optimalUsers = determineOptimalUsers(data);
  console.log(`   ✅ ОПТИМАЛЬНОЕ количество пользователей: ~${optimalUsers} VU`);
  console.log(`      (Success Rate > 95%, Avg Response Time < 3s)\n`);
  
  // Определяем максимальное количество пользователей
  const maxUsers = determineMaxUsers(data);
  console.log(`   ⚠️  МАКСИМАЛЬНОЕ количество пользователей: ~${maxUsers} VU`);
  console.log(`      (Success Rate > 70%, система еще работает)\n`);
  
  // Анализируем проблемы
  if (scenarioSuccessRateValue < 95) {
    recommendations.push(`   ⚠️  Success Rate ниже 95% (${scenarioSuccessRateValue.toFixed(1)}%). Требуется оптимизация.`);
  }
  
  if (avgReqDuration > 3000) {
    recommendations.push(`   ⚠️  Среднее время ответа > 3s. Требуется улучшение производительности.`);
  }
  
  const p95Duration = data.metrics.full_scenario_duration?.values['p(95)'] || 0;
  if (p95Duration > 5000) {
    recommendations.push(`   ⚠️  95-й перцентиль времени сценария > 5s (${p95Duration.toFixed(0)}ms).`);
  }
  
  if (authSuccessRateValue < 98) {
    recommendations.push(`   ⚠️  Проблемы с авторизацией (${authSuccessRateValue.toFixed(1)}%). Проверьте auth сервис.`);
  }
  
  if (getUserSuccessRateValue < 98) {
    recommendations.push(`   ⚠️  Проблемы с получением данных пользователя (${getUserSuccessRateValue.toFixed(1)}%).`);
  }
  
  if (recommendationsSuccessRateValue < 95) {
    recommendations.push(`   ⚠️  Проблемы с рекомендациями (${recommendationsSuccessRateValue.toFixed(1)}%).`);
  }
  
  if (cacheHitRateValue < 20) {
    recommendations.push(`   ⚠️  Низкий Cache Hit Rate (${cacheHitRateValue.toFixed(1)}%). Рассмотрите оптимизацию кэширования.`);
  }
  
  const errorRate = (failedRequests / totalRequests) * 100;
  if (errorRate > 5) {
    recommendations.push(`   ⚠️  Высокий процент ошибок (${errorRate.toFixed(1)}%). Требуется исследование.`);
  }
  
  if (recommendations.length === 0) {
    console.log(`   ✅ Отлично! Система работает стабильно под нагрузкой.`);
    console.log(`   ✅ Все метрики в пределах нормы.`);
  } else {
    console.log(`   Обнаружены следующие проблемы:\n`);
    recommendations.forEach(rec => console.log(rec));
  }
  
  console.log('\n' + line + '\n');
}

/**
 * Выводит статистику по метрике
 */
function printMetricStats(label, metric) {
  if (!metric || !metric.values) {
    console.log(`${label} N/A`);
    return;
  }
  
  const avg = metric.values.avg || 0;
  const min = metric.values.min || 0;
  const med = metric.values.med || 0;
  const max = metric.values.max || 0;
  const p90 = metric.values['p(90)'] || 0;
  const p95 = metric.values['p(95)'] || 0;
  const p99 = metric.values['p(99)'] || 0;
  
  console.log(`${label}`);
  console.log(`      avg: ${avg.toFixed(0)}ms | med: ${med.toFixed(0)}ms | p90: ${p90.toFixed(0)}ms | p95: ${p95.toFixed(0)}ms | p99: ${p99.toFixed(0)}ms`);
}

/**
 * Форматирует байты в читаемый формат
 */
function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i];
}

/**
 * Анализирует данные по типу теста
 */
function analyzeTestType(data, testType, testName) {
  // Фильтруем метрики по тегу test_type
  // Примечание: k6 не предоставляет прямой доступ к метрикам по тегам в handleSummary
  // Поэтому выводим общую информацию
  console.log(`   ${testName}:`);
  console.log(`      Этот тест помогает определить поведение системы при различных нагрузках.`);
}

/**
 * Определяет оптимальное количество пользователей
 */
function determineOptimalUsers(data) {
  // Логика: находим максимальное количество VU, при котором Success Rate > 95% и Avg Time < 3s
  // Это упрощенная логика, так как k6 не предоставляет временные ряды в handleSummary
  
  const scenarioSuccessRate = data.metrics.scenario_success_rate?.values?.rate || 0;
  const avgDuration = data.metrics.full_scenario_duration?.values?.avg || 0;
  
  if (scenarioSuccessRate > 0.95 && avgDuration < 3000) {
    // Система работает хорошо, предполагаем что оптимум около 50 VU
    return 50;
  } else if (scenarioSuccessRate > 0.90 && avgDuration < 4000) {
    return 30;
  } else {
    return 20;
  }
}

/**
 * Определяет максимальное количество пользователей
 */
function determineMaxUsers(data) {
  // Логика: находим максимальное количество VU, при котором Success Rate > 70%
  
  const scenarioSuccessRate = data.metrics.scenario_success_rate?.values?.rate || 0;
  
  if (scenarioSuccessRate > 0.90) {
    return 200;
  } else if (scenarioSuccessRate > 0.80) {
    return 150;
  } else if (scenarioSuccessRate > 0.70) {
    return 100;
  } else {
    return 50;
  }
}
