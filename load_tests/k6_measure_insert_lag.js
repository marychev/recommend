import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Counter, Rate } from 'k6/metrics';
import { BASE_URL } from './k6-helpers.js';

// ════════════════════════════════════════════════════════
// Конфигурация
// ════════════════════════════════════════════════════════

const CLICKHOUSE_URL = __ENV.CLICKHOUSE_URL || 'http://localhost:8123';
const DATABASE = __ENV.CLICKHOUSE_DATABASE || 'music_recommend';
const API_URL = `${BASE_URL}/api/v1/users`;

// Параметры измерения
const CHECK_INTERVAL = parseFloat(__ENV.CHECK_INTERVAL || '0.5'); // секунды между проверками
const MAX_WAIT_TIME = parseFloat(__ENV.MAX_WAIT_TIME || '60'); // максимальное время ожидания в секундах
const NUM_REQUESTS = parseInt(__ENV.NUM_REQUESTS || '50'); // количество запросов для измерения

// ════════════════════════════════════════════════════════
// Кастомные метрики
// ════════════════════════════════════════════════════════

const insertLag = new Trend('insert_lag_ms', true); // лаг вставки в миллисекундах
const apiResponseTime = new Trend('api_response_time_ms', true); // время ответа API
const foundRecords = new Counter('found_records'); // количество найденных записей
const notFoundRecords = new Counter('not_found_records'); // количество не найденных записей
const successRate = new Rate('insert_success_rate'); // процент успешных вставок

// ════════════════════════════════════════════════════════
// Опции k6
// ════════════════════════════════════════════════════════

export const options = {
  vus: 1, // Один виртуальный пользователь для последовательных измерений
  iterations: NUM_REQUESTS,
  thresholds: {
    'insert_lag_ms': ['p(95)<10000', 'p(99)<20000'], // 95% запросов < 10s, 99% < 20s
    'insert_success_rate': ['rate>0.8'], // минимум 80% успешных вставок
  },
};

// ════════════════════════════════════════════════════════
// Функции
// ════════════════════════════════════════════════════════

/**
 * Генерирует уникальные данные для пользователя
 */
function generateUserData() {
  const timestamp = Date.now();
  const random = Math.floor(Math.random() * 10000);
  const username = `lag_test_user_${timestamp}_${random}`;
  
  return {
    username: username,
    email: `${username.replace(/[^a-z0-9]/g, '')}@example.com`,
    age: Math.floor(Math.random() * 60) + 18,
    country: 'Russia',
  };
}

/**
 * Проверяет наличие пользователя в ClickHouse по username
 */
function checkUserInClickHouse(username) {
  // Экранируем username для SQL запроса
  const usernameEscaped = username.replace(/'/g, "''");
  
  const query = `SELECT created_at FROM ${DATABASE}.users WHERE username = '${usernameEscaped}' LIMIT 1 FORMAT JSONEachRow`;
  const url = `${CLICKHOUSE_URL}/?query=${encodeURIComponent(query)}`;
  
  const response = http.get(url, {
    timeout: '10s',
    headers: {
      'Accept': 'application/json',
    },
  });
  
  if (response.status === 200 && response.body && response.body.trim()) {
    try {
      const lines = response.body.trim().split('\n');
      for (const line of lines) {
        if (line.trim()) {
          const data = JSON.parse(line);
          if (data.created_at) {
            // Парсим формат ClickHouse DateTime: "2026-01-08 15:48:39"
            const created_at_str = data.created_at;
            const created_at = new Date(created_at_str.replace(' ', 'T') + 'Z');
            return created_at.getTime(); // возвращаем timestamp в миллисекундах
          }
        }
      }
    } catch (e) {
      // Ошибка парсинга JSON
      return null;
    }
  }
  
  return null;
}

/**
 * Измеряет лаг вставки для одного пользователя
 */
function measureInsertLag() {
  // Генерируем данные пользователя
  const userData = generateUserData();
  const payload = JSON.stringify(userData);
  
  // Отправляем POST запрос
  const apiStartTime = Date.now();
  const apiResponse = http.post(API_URL, payload, {
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: '30s',
  });
  const apiResponseTime_ms = Date.now() - apiStartTime;
  
  // Проверяем успешность запроса
  const apiSuccess = check(apiResponse, {
    'API status is 201': (r) => r.status === 201,
    'API response has user_id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.user_id !== undefined;
      } catch (e) {
        return false;
      }
    },
  });
  
  if (!apiSuccess) {
    console.log(`❌ Ошибка создания пользователя: ${apiResponse.status} - ${apiResponse.body}`);
    notFoundRecords.add(1);
    successRate.add(false);
    return;
  }
  
  // Парсим ответ API
  let user_id, username;
  try {
    const body = JSON.parse(apiResponse.body);
    user_id = body.user_id;
    username = body.username || userData.username;
  } catch (e) {
    console.log(`❌ Ошибка парсинга ответа API: ${e}`);
    notFoundRecords.add(1);
    successRate.add(false);
    return;
  }
  
  // Сохраняем время ответа API
  apiResponseTime.add(apiResponseTime_ms);
  
  // Ждем появления записи в ClickHouse
  const requestTime = apiStartTime; // время создания запроса
  const startCheckTime = Date.now();
  let found = false;
  let insertTime = null;
  let checkCount = 0;
  
  while ((Date.now() - startCheckTime) < MAX_WAIT_TIME * 1000) {
    checkCount++;
    insertTime = checkUserInClickHouse(username);
    
    if (insertTime !== null) {
      found = true;
      break;
    }
    
    // Показываем прогресс каждые 5 секунд
    const elapsed = (Date.now() - startCheckTime) / 1000;
    if (checkCount % 10 === 0) { // каждые 5 секунд (10 проверок * 0.5 сек)
      console.log(`⏳ Проверка ${checkCount}, прошло ${elapsed.toFixed(1)}с из ${MAX_WAIT_TIME}с... (user_id=${user_id})`);
    }
    
    sleep(CHECK_INTERVAL);
  }
  
  if (found && insertTime !== null) {
    // Вычисляем лаг вставки
    const lag_ms = insertTime - requestTime;
    insertLag.add(lag_ms);
    foundRecords.add(1);
    successRate.add(true);
    
    const elapsed = (Date.now() - startCheckTime) / 1000;
    console.log(`✅ Запись найдена: user_id=${user_id}, username=${username.substring(0, 30)}..., лаг=${lag_ms.toFixed(2)}ms, проверок=${checkCount}, время проверки=${elapsed.toFixed(1)}с`);
  } else {
    const elapsed = (Date.now() - startCheckTime) / 1000;
    console.log(`⚠️  Запись не найдена после ${elapsed.toFixed(1)}с (${checkCount} проверок): user_id=${user_id}, username=${username.substring(0, 30)}...`);
    notFoundRecords.add(1);
    successRate.add(false);
  }
}

// ════════════════════════════════════════════════════════
// Основная функция
// ════════════════════════════════════════════════════════

export default function () {
  console.log('📊 ИЗМЕРЕНИЕ ЛАГА ВСТАВКИ В CLICKHOUSE');
  console.log(`   API URL: ${API_URL}`);
  console.log(`   ClickHouse URL: ${CLICKHOUSE_URL}`);
  console.log(`   Интервал проверки: ${CHECK_INTERVAL} сек`);
  console.log(`   Максимальное время ожидания: ${MAX_WAIT_TIME} сек`);
  console.log(`   ℹ️  Система использует батчинг INSERT (интервал flush: 5 сек)`);
  console.log(`   ℹ️  Ожидаемый лаг: 5-10 секунд (из-за батчинга)`);
  console.log('');
  
  measureInsertLag();
  
  // Небольшая задержка между запросами
  sleep(0.2);
}

// ════════════════════════════════════════════════════════
// Обработка результатов
// ════════════════════════════════════════════════════════

export function handleSummary(data) {
  const found = data.metrics.found_records?.values?.count || 0;
  const notFound = data.metrics.not_found_records?.values?.count || 0;
  const total = found + notFound;
  const successRateValue = data.metrics.insert_success_rate?.values?.rate || 0;
  
  const insertLagValues = data.metrics.insert_lag_ms?.values || {};
  const apiResponseValues = data.metrics.api_response_time_ms?.values || {};
  
  let summary = '\n';
  summary += '═'.repeat(80) + '\n';
  summary += '📈 СТАТИСТИКА ИЗМЕРЕНИЙ ЛАГА ВСТАВКИ\n';
  summary += '═'.repeat(80) + '\n\n';
  
  summary += `Всего запросов:        ${total}\n`;
  summary += `Успешно вставлено:     ${found} (${(found / total * 100).toFixed(1)}%)\n`;
  summary += `Не найдено в БД:       ${notFound} (${(notFound / total * 100).toFixed(1)}%)\n`;
  summary += `Процент успеха:        ${(successRateValue * 100).toFixed(1)}%\n\n`;
  
  if (found > 0) {
    summary += '⏱️  ЛАГ ВСТАВКИ (время от запроса до вставки в БД):\n';
    summary += `   Минимум:             ${insertLagValues.min?.toFixed(2) || 'N/A'} ms\n`;
    summary += `   Максимум:            ${insertLagValues.max?.toFixed(2) || 'N/A'} ms\n`;
    summary += `   Среднее:             ${insertLagValues.avg?.toFixed(2) || 'N/A'} ms\n`;
    summary += `   Медиана:             ${insertLagValues.med?.toFixed(2) || 'N/A'} ms\n`;
    if (insertLagValues['p(95)']) {
      summary += `   95 перцентиль:       ${insertLagValues['p(95)'].toFixed(2)} ms\n`;
    }
    if (insertLagValues['p(99)']) {
      summary += `   99 перцентиль:       ${insertLagValues['p(99)'].toFixed(2)} ms\n`;
    }
    summary += '\n';
    
    summary += '⚡ ВРЕМЯ ОТВЕТА API (время от запроса до ответа API):\n';
    summary += `   Минимум:             ${apiResponseValues.min?.toFixed(2) || 'N/A'} ms\n`;
    summary += `   Максимум:            ${apiResponseValues.max?.toFixed(2) || 'N/A'} ms\n`;
    summary += `   Среднее:             ${apiResponseValues.avg?.toFixed(2) || 'N/A'} ms\n`;
    summary += `   Медиана:             ${apiResponseValues.med?.toFixed(2) || 'N/A'} ms\n`;
    
    if (insertLagValues.avg && apiResponseValues.avg) {
      const queueTime = insertLagValues.avg - apiResponseValues.avg;
      summary += '\n';
      summary += '📊 РАЗНИЦА (лаг вставки - время ответа API):\n';
      summary += `   Это время, которое запись провела в очереди/буфере\n`;
      summary += `   Среднее:             ${queueTime.toFixed(2)} ms\n`;
    }
  } else {
    summary += '⚠️  Нет успешных измерений для анализа\n';
    summary += '\n';
    summary += '💡 ВОЗМОЖНЫЕ ПРИЧИНЫ:\n';
    summary += '   • Записи еще обрабатываются Kafka Consumer (батчинг до 5 сек)\n';
    summary += '   • Kafka Consumer не запущен или не работает\n';
    summary += '   • Проблемы с Zookeeper/Kafka координатором\n';
    summary += '   • Fallback механизм работает, но батчинг задерживает вставку (до 5 сек)\n';
    summary += '   • Проблемы с подключением к ClickHouse\n';
  }
  
  summary += '\n';
  summary += '═'.repeat(80) + '\n';
  
  return {
    stdout: summary,
  };
}
