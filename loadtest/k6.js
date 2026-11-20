import http from 'k6/http';
import { check } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8101';
const requestDuration = new Trend('request_duration_ms', true);
const requestErrors = new Rate('request_errors');

export const options = {
  scenarios: {
    ramp_10_50_100: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 10 },
        { duration: '60s', target: 10 },
        { duration: '10s', target: 50 },
        { duration: '60s', target: 50 },
        { duration: '10s', target: 100 },
        { duration: '60s', target: 100 },
        { duration: '5s', target: 0 },
      ],
      exec: 'readWorkload',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<300'],
    request_errors: ['rate<0.01'],
  },
};

export function readWorkload() {
  for (const path of ['/api/risks', '/api/state', '/api/recommendations']) {
    const response = http.get(`${BASE_URL}${path}`, { tags: { endpoint: path } });
    const valid = check(response, { [`${path} returns 2xx`]: (r) => r.status >= 200 && r.status < 300 });
    requestDuration.add(response.timings.duration, { endpoint: path });
    requestErrors.add(!valid, { endpoint: path });
  }
}

export function handleSummary(data) {
  const metric = (name) => data.metrics[name]?.values || {};
  return {
    'loadtest/summary.json': JSON.stringify({
      workload: 'GET /api/risks, /api/state, /api/recommendations',
      vus: [10, 50, 100],
      stages: '10s ramp + 60s hold per level; 5s ramp down',
      http_req_duration: metric('http_req_duration'),
      http_reqs: metric('http_reqs'),
      request_errors: metric('request_errors'),
      checks: metric('checks'),
    }, null, 2),
  };
}
