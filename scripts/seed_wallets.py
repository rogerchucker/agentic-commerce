import argparse
import hashlib
import hmac
import json
import os
import time
from uuid import UUID

import requests
from requests import Response


def make_jwt(secret: str, aud: str, scope: str) -> str:
    import base64

    def b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode().rstrip("=")

    header = b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    now = int(time.time())
    payload = b64url(
        json.dumps({"sub": "seed-script", "aud": aud, "scope": scope, "iat": now, "exp": now + 3600}, separators=(",", ":")).encode()
    )
    sig = hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    return f"{header}.{payload}.{b64url(sig)}"

def _sleep_backoff(attempt: int, base_seconds: float, max_seconds: float) -> None:
    # Exponential backoff with a cap; keep it simple and deterministic.
    delay = min(max_seconds, base_seconds * (2**attempt))
    time.sleep(delay)


def _request_with_retries(
    session: requests.Session,
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict | None = None,
    timeout_seconds: float = 5.0,
    retries: int = 10,
    backoff_seconds: float = 0.2,
    max_backoff_seconds: float = 2.0,
) -> Response:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return session.request(
                method,
                url,
                headers=headers,
                json=json_body,
                timeout=timeout_seconds,
            )
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            last_exc = exc
            if attempt >= retries:
                raise
            _sleep_backoff(attempt, backoff_seconds, max_backoff_seconds)
    # Unreachable, but keeps type checkers happy.
    raise RuntimeError(f"request failed: {last_exc}")


def _wait_ready(
    session: requests.Session,
    base_url: str,
    *,
    timeout_seconds: float,
    request_timeout_seconds: float,
    retries_per_request: int,
    backoff_seconds: float,
    max_backoff_seconds: float,
) -> None:
    deadline = time.time() + timeout_seconds
    last_err: str | None = None

    while time.time() < deadline:
        try:
            res = _request_with_retries(
                session,
                "GET",
                f"{base_url}/v1/ready",
                timeout_seconds=request_timeout_seconds,
                retries=retries_per_request,
                backoff_seconds=backoff_seconds,
                max_backoff_seconds=max_backoff_seconds,
            )
            if res.status_code == 200:
                return
            last_err = f"ready returned {res.status_code}: {res.text[:200]}"
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            last_err = f"ready request failed: {exc!r}"

        time.sleep(0.25)

    raise RuntimeError(f"service not ready at {base_url!r}: {last_err}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("BASE_URL", "http://localhost:8080"))
    parser.add_argument("--count", type=int, default=2500)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--jwt-secret", default="dev-secret-change-me")
    parser.add_argument("--jwt-audience", default="agentic-commerce")
    parser.add_argument("--timeout-seconds", type=float, default=5.0, help="HTTP request timeout")
    parser.add_argument("--retries", type=int, default=10, help="Retries for transient connection errors")
    parser.add_argument("--backoff-seconds", type=float, default=0.2, help="Backoff base seconds between retries")
    parser.add_argument("--max-backoff-seconds", type=float, default=2.0, help="Max backoff seconds between retries")
    parser.add_argument(
        "--wait-ready-seconds",
        type=float,
        default=30.0,
        help="Wait up to N seconds for /v1/ready before seeding",
    )
    args = parser.parse_args()

    token = make_jwt(args.jwt_secret, args.jwt_audience, "wallet:read wallet:write wallet:admin")
    headers = {"Authorization": f"Bearer {token}"}

    base_url = args.base_url.rstrip("/")
    session = requests.Session()

    if args.wait_ready_seconds > 0:
        _wait_ready(
            session,
            base_url,
            timeout_seconds=args.wait_ready_seconds,
            request_timeout_seconds=args.timeout_seconds,
            retries_per_request=max(1, min(args.retries, 3)),
            backoff_seconds=args.backoff_seconds,
            max_backoff_seconds=args.max_backoff_seconds,
        )

    created = 0
    already_exists = 0
    failed = 0

    for i in range(args.start, args.start + args.count):
        wallet_id = f"00000000-0000-0000-0000-{str(i).zfill(12)}"
        UUID(wallet_id)
        res = _request_with_retries(
            session,
            "POST",
            f"{base_url}/v1/wallets",
            headers=headers,
            json_body={"wallet_id": wallet_id, "asset": "USD"},
            timeout_seconds=args.timeout_seconds,
            retries=args.retries,
            backoff_seconds=args.backoff_seconds,
            max_backoff_seconds=args.max_backoff_seconds,
        )

        if res.status_code == 200:
            created += 1
            continue
        if res.status_code == 409:
            # Safe to re-run seeding against an existing dataset.
            already_exists += 1
            continue

        failed += 1
        # Keep the loop going to surface the full scope (and any transient issues),
        # but print a hint for the first few failures.
        if failed <= 5:
            print(f"seed failed wallet_id={wallet_id} status={res.status_code} body={res.text[:200]!r}")

    print(
        f"seeded wallet range [{args.start}, {args.start + args.count - 1}] "
        f"(created={created}, already_exists={already_exists}, failed={failed})"
    )
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
