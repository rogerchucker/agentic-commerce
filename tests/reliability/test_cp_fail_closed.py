from contextlib import contextmanager

from tests.conftest import auth_header


def test_write_fails_closed_without_db(monkeypatch, app_client, wallet_ids):
    from wallet_service.domain.errors import ServiceUnavailableError
    from wallet_service.ledger import service as ledger_service

    @contextmanager
    def broken_conn():
        raise ServiceUnavailableError("database unavailable")
        yield

    monkeypatch.setattr(ledger_service, "get_connection", broken_conn)

    w1, _ = wallet_ids
    headers = auth_header("wallet:write")
    response = app_client.post("/v1/wallets", headers=headers, json={"wallet_id": w1, "asset": "USD"})
    assert response.status_code == 503
