import http from 'k6/http';
import { check } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8101';
const requestDuration = new Trend('request_duration_ms', true);
const requestErrors = new Rate('request_errors');
const whatifDuration = new Trend('whatif_duration_ms', true);

export const options = {
  scenarios: {
    read_and_decision_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '5s', target: 10 },
        { duration: '15s', target: 10 },
        { duration: '5s', target: 50 },
        { duration: '15s', target: 50 },
        { duration: '5s', target: 100 },
        { duration: '15s', target: 100 },
        { duration: '5s', target: 0 },
      ],
      exec: 'combinedWorkload',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<300'],
    request_errors: ['rate<0.01'],
  },
};

export function combinedWorkload() {
  // 1. Read state & risks
  for (const path of ['/api/risks', '/api/state', '/api/recommendations']) {
    const res = http.get(`${BASE_URL}${path}`, { tags: { endpoint: path } });
    const valid = check(res, { [`${path} returns 2xx`]: (r) => r.status >= 200 && r.status < 300 });
    requestDuration.add(res.timings.duration, { endpoint: path });
    requestErrors.add(!valid, { endpoint: path });
  }

  // 2. What-If Candidate Simulation (Decision path)
  const candidatePayload = JSON.stringify({
    source_depot_id: 'depot-gazipur',
    destination_station_id: 'station-mirpur',
    route_id: 'route-gazipur-mirpur',
    fuel_type: 'DIESEL',
    quantity: 5000,
  });

  const whatifRes = http.post(`${BASE_URL}/api/whatif`, candidatePayload, {
    headers: { 'Content-Type': 'application/json' },
    tags: { endpoint: '/api/whatif' },
  });

  const whatifValid = check(whatifRes, {
    'whatif returns 200': (r) => r.status === 200,
    'whatif result feasible': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.feasible === true;
      } catch (e) {
        return false;
      }
    },
  });

  whatifDuration.add(whatifRes.timings.duration, { endpoint: '/api/whatif' });
  requestErrors.add(!whatifValid, { endpoint: '/api/whatif' });
}

export function handleSummary(data) {
  const metric = (name) => data.metrics[name]?.values || {};
  return {
    'loadtest/summary.json': JSON.stringify(
      {
        workload: 'GET /api/risks, /api/state, /api/recommendations + POST /api/whatif',
        vus: [10, 50, 100],
        http_req_duration: metric('http_req_duration'),
        whatif_duration: metric('whatif_duration_ms'),
        http_reqs: metric('http_reqs'),
        request_errors: metric('request_errors'),
        checks: metric('checks'),
      },
      null,
      2
    ),
  };
}
