import http from 'k6/http';
import { check, sleep } from 'k6';
import { authHeaders, walletId } from './common.js';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export const options = {
  stages: [
    { duration: '1m', target: 100 },
    { duration: '2m', target: 1200 },
    { duration: '2m', target: 1200 },
    { duration: '1m', target: 100 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['p(95)<180'],
  },
};

export default function () {
  const from = walletId(1 + (__VU % 300));
  const to = walletId(2000 + (__VU % 300));
  const idem = `spike-${__VU}-${__ITER}`;
  const res = http.post(
    `${BASE_URL}/v1/transfers`,
    JSON.stringify({ from_wallet_id: from, to_wallet_id: to, amount: '0.25', asset: 'USD' }),
    { headers: authHeaders('wallet:write', idem) }
  );
  check(res, { 'spike status': (r) => r.status === 200 });
  sleep(0.01);
}
