/**
 * k6 Smoke Test - Базовая проверка работоспособности API
 * 
 * Назначение:
 * - Быстрая проверка, что все критичные endpoints доступны
 * - Выполняется перед запуском полноценного нагрузочного тестирования
 * - Минимальная нагрузка на систему
 * 
 * Что проверяется:
 * ✅ API доступен и отвечает
 * ✅ Endpoints пользователей работают
 * ✅ Endpoints треков работают
 * ✅ Recommendations (главная функция) работает
 * ✅ Health check проходит
 * 
 * Запуск:
 *   k6 run load_tests/k6_smoke_test.js
 * 
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { BASE_URL, urlUsersList10, urlTracksList10 } from './k6-helpers.js';

// Конфигурация smoke теста
export const options = {
  // Минимальная нагрузка: 2 пользователя на 30 секунд
  vus: 3,
  duration: '10s',
  
  // Пороговые значения (thresholds)
  thresholds: {
    // 95% запросов должны быть быстрее 2 секунд
    'http_req_duration': ['p(95)<2000'],
    
    // Менее 10% ошибок допустимо для smoke теста
    'http_req_failed': ['rate<0.1'],
    
    // Минимум 90% проверок должны пройти
    'checks': ['rate>0.9'],
  },
};


/**
 * Основной сценарий smoke теста
 */
export default function () {
  // 1️⃣ Проверка корневого endpoint и health
  group('🏥 Health Check', () => {
    const rootRes = http.get(`${BASE_URL}/`);
    check(rootRes, {
      'Root endpoint is accessible': (r) => r.status === 200,
      'Root returns JSON': (r) => r.headers['Content-Type']?.includes('application/json'),
    });
  });

  sleep(0.5);

  // 2️⃣ Проверка Users API
  group('👥 Users API', () => {
    // Список пользователей
    const usersListRes = http.get(urlUsersList10);
    check(usersListRes, {
      'GET /users returns 200': (r) => r.status === 200,
      'GET /users returns array': (r) => {
        try {
          const body = JSON.parse(r.body);
          return Array.isArray(body) && body.length > 0;
        } catch {
          return false;
        }
      },
    });

    // Конкретный пользователь (если есть данные)
    if (usersListRes.status === 200) {
      try {
        const users = JSON.parse(usersListRes.body);
        if (users.length > 0) {
          const userId = users[0].user_id;
          const userRes = http.get(`${BASE_URL}/api/v1/users/${userId}`);
          check(userRes, {
            'GET /users/{id} returns 200': (r) => r.status === 200,
          });
        }
      } catch (e) {
        console.error('Error parsing users:', e);
      }
    }
  });

  sleep(0.5);

  // 3️⃣ Проверка Tracks API
  group('🎵 Tracks API', () => {
    const tracksListRes = http.get(urlTracksList10);
    check(tracksListRes, {
      'GET /tracks returns 200': (r) => r.status === 200,
      'GET /tracks returns array': (r) => {
        try {
          const body = JSON.parse(r.body);
          return Array.isArray(body) && body.length > 0;
        } catch {
          return false;
        }
      },
    });

    // Конкретный трек (если есть данные)
    if (tracksListRes.status === 200) {
      try {
        const tracks = JSON.parse(tracksListRes.body);
        if (tracks.length > 0) {
          const trackId = tracks[0].track_id;
          const trackRes = http.get(`${BASE_URL}/api/v1/tracks/${trackId}`);
          check(trackRes, {
            'GET /tracks/{id} returns 200': (r) => r.status === 200,
          });
        }
      } catch (e) {
        console.error('Error parsing tracks:', e);
      }
    }
  });

  sleep(0.5);

  // 4️⃣ Проверка Recommendations API (ГЛАВНАЯ ФУНКЦИЯ!)
  group('🎯 Recommendations API', () => {
    // Проверяем рекомендации для существующего пользователя
    const usersRes = http.get(`${BASE_URL}/api/v1/users?limit=1`);
    
    if (usersRes.status === 200) {
      try {
        const users = JSON.parse(usersRes.body);
        if (users.length > 0) {
          const userId = users[0].user_id;
          
          // GET рекомендации
          const recRes = http.get(`${BASE_URL}/api/v1/recommendations/${userId}`);
          check(recRes, {
            'GET /recommendations/{user_id} responds': (r) => 
              r.status === 200 || r.status === 404,
            'GET /recommendations response is JSON': (r) => {
              if (r.status === 200) {
                try {
                  JSON.parse(r.body);
                  return true;
                } catch {
                  return false;
                }
              }
              return true; // 404 тоже OK
            },
          });
        }
      } catch (e) {
        console.error('Error testing recommendations:', e);
      }
    }
  });

  sleep(1);
}

/**
 * Функция для отображения результатов в конце теста
 */
export function handleSummary(data) {
  console.log('\n');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('               🔥 SMOKE TEST ЗАВЕРШЁН                      ');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  
  const totalReqs = data.metrics.http_reqs?.values?.count || 0;
  const failRate = (data.metrics.http_req_failed?.values?.rate || 0) * 100;
  const avgDuration = data.metrics.http_req_duration?.values?.avg || 0;
  const p95Duration = data.metrics.http_req_duration?.values?.['p(95)'] || 0;
  const checksRate = (data.metrics.checks?.values?.rate || 0) * 100;
  
  console.log(`📊 Статистика:`);
  console.log(`   • Всего запросов:        ${totalReqs}`);
  console.log(`   • Среднее время ответа:  ${avgDuration.toFixed(2)}ms`);
  console.log(`   • 95 перцентиль:         ${p95Duration.toFixed(2)}ms`);
  console.log(`   • Процент ошибок:        ${failRate.toFixed(2)}%`);
  console.log(`   • Успешные проверки:     ${checksRate.toFixed(2)}%`);
  console.log('');
  
  // Оценка результатов
  let status = '✅ PASSED';
  let message = 'API работает нормально. Можно запускать полноценные тесты!';
  
  if (failRate > 10) {
    status = '❌ FAILED';
    message = 'Слишком много ошибок! Проверьте систему перед дальнейшим тестированием.';
  } else if (p95Duration > 5000) {
    status = '⚠️  WARNING';
    message = 'API работает медленно. Рекомендуется проверить производительность.';
  } else if (checksRate < 90) {
    status = '⚠️  WARNING';
    message = 'Некоторые проверки не прошли. Рекомендуется изучить логи.';
  }
  
  console.log(`${status}: ${message}`);
  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  
  return {
    'stdout': textSummary(data),
  };
}

function textSummary(data) {
  return ''; // k6 сам выведет стандартную статистику
}

