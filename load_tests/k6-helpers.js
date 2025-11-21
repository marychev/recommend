/**
 * Общие helper функции для k6 тестов
 * 
 * Используется всеми тестами для избежания дублирования кода
 */

// ════════════════════════════════════════════════════════
// Конфигурация
// ════════════════════════════════════════════════════════

export const BASE_URL = __ENV.API_URL || 'http://localhost:8000';
export const urlUsersList10 = `${BASE_URL}/api/v1/users?limit=10`;
export const urlTracksList10 = `${BASE_URL}/api/v1/tracks?limit=10`;

// export const urlRandomRecommendation = `${BASE_URL}/api/v1/recommendations/${getRandomUserId()}`;
// export const urlRandomUser = `${BASE_URL}/api/v1/users/${getRandomUserId()}`;
// export const urlRandomTrack = `${BASE_URL}/api/v1/tracks/${getRandomTrackId()}`;

// Диапазоны ID для тестовых данных
export const USER_ID_MIN = 1;
export const USER_ID_MAX = 100_000_000; // 100000;
export const TRACK_ID_MIN = 1;
export const TRACK_ID_MAX = 50_000_000; // 50000;

// ════════════════════════════════════════════════════════
// Helper функции
// ════════════════════════════════════════════════════════

/**
 * Получает случайный ID пользователя в диапазоне тестовых данных
 */
export function getRandomUserId() {
  return Math.floor(Math.random() * (USER_ID_MAX - USER_ID_MIN + 1)) + USER_ID_MIN;
}

/**
 * Получает случайный ID трека в диапазоне тестовых данных
 */
export function getRandomTrackId() {
  return Math.floor(Math.random() * (TRACK_ID_MAX - TRACK_ID_MIN + 1)) + TRACK_ID_MIN;
}

/**
 * Получает случайный offset для пагинации
 */
export function getRandomOffset(max = 10000) {
  return Math.floor(Math.random() * max);
}

/**
 * Генерирует случайное число в диапазоне
 */
export function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

// ════════════════════════════════════════════════════════
// Форматирование результатов
// ════════════════════════════════════════════════════════

/**
 * Форматирует миллисекунды в читаемый формат
 */
export function formatMs(ms) {
  if (ms < 1000) {
    return `${ms.toFixed(0)}ms`;
  } else if (ms < 60000) {
    return `${(ms / 1000).toFixed(2)}s`;
  } else {
    return `${(ms / 60000).toFixed(2)}m`;
  }
}

/**
 * Форматирует процент
 */
export function formatPercent(rate) {
  return `${(rate * 100).toFixed(2)}%`;
}

/**
 * Форматирует длительность теста
 */
export function formatDuration(ms) {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}

/**
 * Получает базовую статистику из результатов k6
 */
export function getBasicStats(data) {
  return {
    duration: data.state.testRunDurationMs || 0,
    totalReqs: data.metrics.http_reqs?.values?.count || 0,
    rps: data.metrics.http_reqs?.values?.rate || 0,
    failRate: data.metrics.http_req_failed?.values?.rate || 0,
    avgDuration: data.metrics.http_req_duration?.values?.avg || 0,
    medDuration: data.metrics.http_req_duration?.values?.med || 0,
    p95Duration: data.metrics.http_req_duration?.values?.['p(95)'] || 0,
    p99Duration: data.metrics.http_req_duration?.values?.['p(99)'] || 0,
    minDuration: data.metrics.http_req_duration?.values?.min || 0,
    maxDuration: data.metrics.http_req_duration?.values?.max || 0,
    maxVUs: data.metrics.vus_max?.values?.max || data.metrics.vus?.values?.max || 0,
    checksRate: data.metrics.checks?.values?.rate || 0,
  };
}

/**
 * Печатает красивую шапку для результатов
 */
export function printHeader(title) {
  const line = '═'.repeat(63);
  console.log('\n' + line);
  console.log(`  ${title}`);
  console.log(line + '\n');
}

/**
 * Печатает базовую статистику теста
 */
export function printBasicStats(stats) {
  console.log(`📊 Общая статистика:`);
  console.log(`   • Длительность теста:    ${formatDuration(stats.duration)}`);
  console.log(`   • Виртуальных юзеров:    ${stats.maxVUs}`);
  console.log(`   • Всего запросов:        ${stats.totalReqs}`);
  console.log(`   • RPS (req/sec):         ${stats.rps.toFixed(2)}`);
  console.log(`   • Процент ошибок:        ${formatPercent(stats.failRate)}`);
  console.log('');
  
  console.log(`⏱️  Время ответа:`);
  console.log(`   • Минимум:               ${stats.minDuration.toFixed(0)}ms`);
  console.log(`   • Среднее:               ${stats.avgDuration.toFixed(0)}ms`);
  console.log(`   • Медиана:               ${stats.medDuration.toFixed(0)}ms`);
  console.log(`   • 95 перцентиль:         ${stats.p95Duration.toFixed(0)}ms`);
  console.log(`   • 99 перцентиль:         ${stats.p99Duration.toFixed(0)}ms`);
  console.log(`   • Максимум:              ${stats.maxDuration.toFixed(0)}ms`);
  console.log('');
}

/**
 * Оценивает результаты теста и выводит статус
 */
export function evaluateResults(stats, thresholds = {}) {
  const {
    maxP95 = 5000,
    maxP99 = 10000,
    maxFailRate = 0.1,
    minChecksRate = 0.9,
  } = thresholds;
  
  let status = '✅ PASSED';
  let messages = [];
  
  // Проверка времени ответа
  if (stats.p95Duration > maxP95) {
    status = '⚠️  WARNING';
    messages.push(`95 перцентиль превышает ${maxP95}ms`);
  }
  
  if (stats.p99Duration > maxP99) {
    status = '❌ FAILED';
    messages.push(`99 перцентиль превышает ${maxP99}ms`);
  }
  
  // Проверка процента ошибок
  if (stats.failRate > maxFailRate) {
    status = '❌ FAILED';
    messages.push(`Процент ошибок превышает ${formatPercent(maxFailRate)}`);
  }
  
  // Проверка успешных checks
  if (stats.checksRate < minChecksRate) {
    status = '⚠️  WARNING';
    messages.push(`Успешных проверок меньше ${formatPercent(minChecksRate)}`);
  }
  
  console.log(`${status}`);
  
  if (messages.length > 0) {
    console.log('');
    messages.forEach(msg => console.log(`   ⚠️  ${msg}`));
  } else {
    console.log(`   Все пороговые значения соблюдены!`);
  }
  
  console.log('');
}

/**
 * Создает стандартный summary для теста
 */
export function createSummary(data, outputFile = null) {
  const result = {};
  
  if (outputFile) {
    result[outputFile] = JSON.stringify(data);
  }
  
  return result;
}

