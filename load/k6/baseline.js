import http from 'k6/http';
import { check } from 'k6';
import { authHeaders, walletId } from './common.js';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const VUS = Number(__ENV.VUS || 200);

export const options = {
  scenarios: {
    steady: {
      executor: 'constant-arrival-rate',
      rate: 1000,
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: VUS,
      maxVUs: 1200,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<150'],
  },
};

export default function () {
  const from = walletId(1 + (__ITER % 500));
  const to = walletId(1000 + (__ITER % 500));

  const idem = `base-${__VU}-${__ITER}`;
  const res = http.post(
    `${BASE_URL}/v1/transfers`,
    JSON.stringify({ from_wallet_id: from, to_wallet_id: to, amount: '0.50', asset: 'USD' }),
    { headers: authHeaders('wallet:write wallet:read', idem) }
  );

  check(res, {
    'status 200': (r) => r.status === 200,
  });
}
