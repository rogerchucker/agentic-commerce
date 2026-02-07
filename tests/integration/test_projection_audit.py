from decimal import Decimal

from tests.conftest import auth_header


def test_projection_matches_audit(app_client, wallet_ids):
    wallet, other = wallet_ids
    headers = auth_header("wallet:read wallet:write")

    app_client.post("/v1/wallets", headers=headers, json={"wallet_id": wallet, "asset": "USD"})
    app_client.post("/v1/wallets", headers=headers, json={"wallet_id": other, "asset": "USD"})

    transfer_headers = dict(headers)
    transfer_headers["Idempotency-Key"] = "idem-proj-1"
    app_client.post(
        "/v1/transfers",
        headers=transfer_headers,
        json={
            "from_wallet_id": wallet,
            "to_wallet_id": other,
            "amount": "2.00",
            "asset": "USD",
        },
    )

    projected = app_client.get(f"/v1/wallets/{wallet}/balance", headers=headers)
    audited = app_client.get(f"/v1/wallets/{wallet}/balance/audit", headers=headers)

    assert projected.status_code == 200
    assert audited.status_code == 200
    assert Decimal(projected.json()["balance"]) == Decimal(audited.json()["balance"])
