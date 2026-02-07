import http from 'k6/http';
import { check } from 'k6';
import { authHeaders, walletId } from './common.js';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export const options = {
  scenarios: {
    partition_window: {
      executor: 'constant-vus',
      vus: 100,
      duration: '6m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.15'],
  },
};

export default function () {
  const from = walletId(1 + (__ITER % 200));
  const to = walletId(1000 + (__ITER % 200));
  const idem = `res-${__VU}-${__ITER}`;

  const res = http.post(
    `${BASE_URL}/v1/transfers`,
    JSON.stringify({ from_wallet_id: from, to_wallet_id: to, amount: '0.10', asset: 'USD' }),
    { headers: authHeaders('wallet:write', idem) }
  );

  check(res, {
    'either committed or fail-closed': (r) => r.status === 200 || r.status === 503,
  });
}
