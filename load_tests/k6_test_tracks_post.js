import http from 'k6/http';
import { check } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { textSummary, BASE_URL } from './k6_test_events_post.js';

// Кастомные метрики
const TITLE = "Tracks POST Load Test Results"
const trackErrors = new Counter('track_errors');
const trackSuccessRate = new Rate('track_success_rate');
const trackResponseTime = new Trend('track_response_time');

export const options = {
  stages: [{ duration: '1m', target: 100 }],
  thresholds: {
    // Реалистичные пороги для нагрузки 100 VUs с учетом батчинга
    http_req_duration: ['p(95)<2000', 'p(99)<3000'], // 95% запросов < 1.5s, 99% < 3s
    http_req_failed: ['rate<0.05'],                  // Меньше 5% ошибок
    track_success_rate: ['rate>0.95'],               // Больше 95% успешных запросов
  },
};

const API_URL = `${BASE_URL}/api/v1/tracks`;

// Генерация случайных данных для трека
function generateTrackData() {
  const titles = [
    'Bohemian Rhapsody', 'Stairway to Heaven', 'Hotel California',
    'Imagine', 'Like a Rolling Stone', 'Hey Jude', 'Smells Like Teen Spirit',
    'Billie Jean', 'Sweet Child O Mine', 'Thunderstruck'
  ];
  const artists = [
    'Queen', 'Led Zeppelin', 'Eagles', 'John Lennon', 'Bob Dylan',
    'The Beatles', 'Nirvana', 'Michael Jackson', 'Guns N Roses', 'AC/DC'
  ];
  const albums = [
    'A Night at the Opera', 'Led Zeppelin IV', 'Hotel California',
    'Imagine', 'Highway 61 Revisited', 'The Beatles', 'Nevermind',
    'Thriller', 'Appetite for Destruction', 'The Razors Edge'
  ];
  const genres = ['Rock', 'Pop', 'Jazz', 'Blues', 'Country', 'Electronic', 'Hip-Hop'];
  
  const title = titles[Math.floor(Math.random() * titles.length)];
  const artist = artists[Math.floor(Math.random() * artists.length)];
  const album = albums[Math.floor(Math.random() * albums.length)];
  const genre = genres[Math.floor(Math.random() * genres.length)];
  const duration_seconds = Math.floor(Math.random() * 300) + 120; // 2-7 минут
  const release_year = Math.floor(Math.random() * 50) + 1970;     // 1970-2020

  return {
    title: `${title} ${Math.floor(Math.random() * 1000)}`,
    artist: artist,
    album: album,
    genre: genre,
    duration_seconds: duration_seconds,
    release_year: release_year,
  };
}

export default function () {
  const payload = JSON.stringify(generateTrackData());
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const startTime = Date.now();
  const response = http.post(API_URL, payload, params);
  const responseTime = Date.now() - startTime;

  const success = check(response, {
    'status is 201': (r) => r.status === 201,
    'response has track_id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.track_id !== undefined && body.track_id > 0;
      } catch (e) {
        return false;
      }
    },
    'response has title': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.title !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  trackSuccessRate.add(success);
  trackResponseTime.add(responseTime);
  
  if (!success) {
    trackErrors.add(1);
  }

}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }, TITLE),
  };
}
