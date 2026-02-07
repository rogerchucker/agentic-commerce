import http from 'k6/http';
import { check, sleep } from 'k6';
import { authHeaders, walletId } from './common.js';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export const options = {
  scenarios: {
    soak: {
      executor: 'constant-arrival-rate',
      rate: 300,
      timeUnit: '1s',
      duration: '2h',
      preAllocatedVUs: 200,
      maxVUs: 500,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['p(95)<170'],
  },
};

export default function () {
  const from = walletId(1 + (__ITER % 500));
  const to = walletId(1000 + (__ITER % 500));

  const doTransfer = Math.random() < 0.2;
  if (doTransfer) {
    const idem = `soak-${__VU}-${__ITER}`;
    const res = http.post(
      `${BASE_URL}/v1/transfers`,
      JSON.stringify({ from_wallet_id: from, to_wallet_id: to, amount: '0.05', asset: 'USD' }),
      { headers: authHeaders('wallet:write wallet:read', idem) }
    );
    check(res, { 'transfer ok': (r) => r.status === 200 });
  } else {
    const res = http.get(`${BASE_URL}/v1/wallets/${from}/balance`, {
      headers: authHeaders('wallet:read'),
    });
    check(res, { 'read ok': (r) => r.status === 200 || r.status === 404 });
  }

  sleep(0.01);
}
