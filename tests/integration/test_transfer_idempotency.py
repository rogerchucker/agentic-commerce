from decimal import Decimal

from tests.conftest import auth_header


def test_transfer_idempotency_and_balance(app_client, wallet_ids):
    w1, w2 = wallet_ids
    headers = auth_header("wallet:read wallet:write")

    for wallet in [w1, w2]:
        res = app_client.post("/v1/wallets", headers=headers, json={"wallet_id": wallet, "asset": "USD"})
        assert res.status_code == 200

    payload = {
        "from_wallet_id": w1,
        "to_wallet_id": w2,
        "amount": "10.25",
        "asset": "USD",
        "external_reference": "order-123",
    }
    transfer_headers = dict(headers)
    transfer_headers["Idempotency-Key"] = "idem-transfer-1"

    first = app_client.post("/v1/transfers", headers=transfer_headers, json=payload)
    second = app_client.post("/v1/transfers", headers=transfer_headers, json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["transaction_id"] == second.json()["transaction_id"]

    b1 = app_client.get(f"/v1/wallets/{w1}/balance", headers=headers).json()
    b2 = app_client.get(f"/v1/wallets/{w2}/balance", headers=headers).json()

    assert Decimal(b1["balance"]) == Decimal("-10.25")
    assert Decimal(b2["balance"]) == Decimal("10.25")
