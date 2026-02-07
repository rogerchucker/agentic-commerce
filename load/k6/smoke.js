import http from 'k6/http';
import { check, sleep } from 'k6';
import { authHeaders, walletId } from './common.js';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export const options = {
  vus: 2,
  iterations: 20,
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<150'],
  },
};

export default function () {
  const from = walletId(1001 + __VU);
  const to = walletId(2001 + __VU);

  http.post(`${BASE_URL}/v1/wallets`, JSON.stringify({ wallet_id: from, asset: 'USD' }), {
    headers: authHeaders('wallet:write wallet:read wallet:admin'),
  });
  http.post(`${BASE_URL}/v1/wallets`, JSON.stringify({ wallet_id: to, asset: 'USD' }), {
    headers: authHeaders('wallet:write wallet:read wallet:admin'),
  });

  const idem = `smoke-${__VU}-${__ITER}`;
  const res = http.post(
    `${BASE_URL}/v1/transfers`,
    JSON.stringify({ from_wallet_id: from, to_wallet_id: to, amount: '1.00', asset: 'USD' }),
    { headers: authHeaders('wallet:write wallet:read', idem) }
  );

  check(res, {
    'transfer success': (r) => r.status === 200,
  });

  sleep(0.1);
}
