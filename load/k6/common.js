import crypto from 'k6/crypto';
import encoding from 'k6/encoding';

const secret = __ENV.JWT_SECRET || 'dev-secret-change-me';
const aud = __ENV.JWT_AUDIENCE || 'agentic-commerce';

function b64url(data) {
  return encoding.b64encode(data, 'rawurl');
}

export function makeJwt(scopes) {
  const header = { alg: 'HS256', typ: 'JWT' };
  const now = Math.floor(Date.now() / 1000);
  const payload = { sub: 'k6-load', aud: aud, scope: scopes, iat: now, exp: now + 3600 };
  const h = b64url(JSON.stringify(header));
  const p = b64url(JSON.stringify(payload));
  const signature = crypto.hmac('sha256', secret, `${h}.${p}`, 'base64rawurl');
  return `${h}.${p}.${signature}`;
}

export function authHeaders(scopes, idempotencyKey = null) {
  const headers = {
    Authorization: `Bearer ${makeJwt(scopes)}`,
    'Content-Type': 'application/json',
  };
  if (idempotencyKey) {
    headers['Idempotency-Key'] = idempotencyKey;
  }
  return headers;
}

export function walletId(idx) {
  return `00000000-0000-0000-0000-${String(idx).padStart(12, '0')}`;
}
