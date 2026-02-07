import argparse
import hashlib
import hmac
import json
import time
from uuid import UUID

import requests


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--count", type=int, default=2500)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--jwt-secret", default="dev-secret-change-me")
    parser.add_argument("--jwt-audience", default="agentic-commerce")
    args = parser.parse_args()

    token = make_jwt(args.jwt_secret, args.jwt_audience, "wallet:read wallet:write wallet:admin")
    headers = {"Authorization": f"Bearer {token}"}

    for i in range(args.start, args.start + args.count):
        wallet_id = f"00000000-0000-0000-0000-{str(i).zfill(12)}"
        UUID(wallet_id)
        requests.post(
            f"{args.base_url}/v1/wallets",
            json={"wallet_id": wallet_id, "asset": "USD"},
            headers=headers,
            timeout=5,
        )

    print(f"seeded wallet range [{args.start}, {args.start + args.count - 1}]")


if __name__ == "__main__":
    main()
