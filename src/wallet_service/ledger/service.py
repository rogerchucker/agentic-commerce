import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import psycopg

from wallet_service.config import settings
from wallet_service.db.database import get_connection
from wallet_service.domain.errors import ConflictError, NotFoundError, ValidationError


@dataclass
class LedgerTransaction:
    transaction_id: UUID
    operation_scope: str
    idempotency_key: str
    payload_hash: str
    status: str
    created_at: datetime
    external_reference: str | None
    entries: list[dict]


def _payload_hash(payload: dict) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _ensure_balanced(entries: list[tuple[UUID, Decimal, str]]) -> None:
    if len(entries) < 2:
        raise ValidationError("at least two journal entries required")
    total = Decimal("0")
    asset = None
    for _, amount, entry_asset in entries:
        if amount == 0:
            raise ValidationError("journal entry amount cannot be zero")
        total += amount
        asset = asset or entry_asset
        if entry_asset != asset:
            raise ValidationError("all entries in a transaction must have the same asset")
    if total != 0:
        raise ValidationError("double-entry violation: sum(entries.amount) != 0")


def create_wallet(wallet_id: UUID, asset: str) -> dict:
    now = datetime.now(timezone.utc)
    with get_connection() as conn:
        try:
            row = conn.execute(
                """
                INSERT INTO accounts(wallet_id, asset, version, created_at)
                VALUES (%s, %s, 0, %s)
                RETURNING wallet_id, asset, version, created_at
                """,
                (str(wallet_id), asset, now),
            ).fetchone()
            conn.execute(
                """
                INSERT INTO balance_projections(wallet_id, asset, balance, version, as_of)
                VALUES (%s, %s, 0, 0, %s)
                """,
                (str(wallet_id), asset, now),
            )
            conn.commit()
            return {
                "wallet_id": row[0],
                "asset": row[1],
                "version": row[2],
                "created_at": row[3],
            }
        except psycopg.errors.UniqueViolation as exc:
            raise ConflictError("wallet already exists") from exc


def get_balance(wallet_id: UUID) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT wallet_id, asset, balance, version, as_of
            FROM balance_projections
            WHERE wallet_id = %s
            """,
            (str(wallet_id),),
        ).fetchone()
        if not row:
            raise NotFoundError("wallet not found")
        return {
            "wallet_id": row[0],
            "asset": row[1],
            "balance": row[2],
            "version": row[3],
            "as_of": row[4],
        }


def _fetch_existing_idempotent(conn, operation_scope: str, idempotency_key: str, payload_hash: str):
    existing = conn.execute(
        """
        SELECT transaction_id, payload_hash
        FROM journal_transactions
        WHERE operation_scope = %s AND idempotency_key = %s
        """,
        (operation_scope, idempotency_key),
    ).fetchone()
    if not existing:
        return None
    if existing[1] != payload_hash:
        raise ConflictError("idempotency key reuse with different payload")
    return existing[0]


def _load_transaction(conn, transaction_id: str) -> LedgerTransaction:
    tx = conn.execute(
        """
        SELECT transaction_id, operation_scope, idempotency_key, payload_hash, status, created_at, external_reference
        FROM journal_transactions
        WHERE transaction_id = %s
        """,
        (transaction_id,),
    ).fetchone()
    entries = conn.execute(
        """
        SELECT wallet_id, amount, asset
        FROM journal_entries
        WHERE transaction_id = %s
        ORDER BY seq ASC
        """,
        (transaction_id,),
    ).fetchall()
    return LedgerTransaction(
        transaction_id=tx[0],
        operation_scope=tx[1],
        idempotency_key=tx[2],
        payload_hash=tx[3],
        status=tx[4],
        created_at=tx[5],
        external_reference=tx[6],
        entries=[{"account_id": row[0], "amount": row[1], "asset": row[2]} for row in entries],
    )


def _bump_version(conn, wallet_id: str, expected_version: int | None) -> int:
    if expected_version is None:
        row = conn.execute("SELECT version FROM accounts WHERE wallet_id = %s FOR UPDATE", (wallet_id,)).fetchone()
        if not row:
            raise NotFoundError("wallet not found")
        expected_version = int(row[0])

    bumped = conn.execute(
        """
        UPDATE accounts
        SET version = version + 1
        WHERE wallet_id = %s AND version = %s
        RETURNING version
        """,
        (wallet_id, expected_version),
    ).fetchone()
    if not bumped:
        raise ConflictError("optimistic version conflict")
    return int(bumped[0])


def _apply_projection(conn, wallet_id: str, asset: str, delta: Decimal, version: int) -> None:
    updated = conn.execute(
        """
        UPDATE balance_projections
        SET balance = balance + %s, version = %s, as_of = NOW()
        WHERE wallet_id = %s AND asset = %s
        """,
        (delta, version, wallet_id, asset),
    )
    if updated.rowcount == 0:
        raise NotFoundError("projection row not found")


def post_transfer(
    *,
    idempotency_key: str,
    from_wallet_id: UUID,
    to_wallet_id: UUID,
    amount: Decimal,
    asset: str,
    external_reference: str | None,
    expected_from_version: int | None,
    expected_to_version: int | None,
) -> LedgerTransaction:
    if from_wallet_id == to_wallet_id:
        raise ValidationError("from_wallet_id and to_wallet_id must differ")

    operation_scope = "transfer"
    payload = {
        "from_wallet_id": str(from_wallet_id),
        "to_wallet_id": str(to_wallet_id),
        "amount": str(amount),
        "asset": asset,
        "external_reference": external_reference,
        "expected_from_version": expected_from_version,
        "expected_to_version": expected_to_version,
    }
    payload_hash = _payload_hash(payload)
    entries = [
        (from_wallet_id, -amount, asset),
        (to_wallet_id, amount, asset),
    ]
    _ensure_balanced(entries)

    with get_connection() as conn:
        conn.execute("SELECT 1")
        existing = _fetch_existing_idempotent(conn, operation_scope, idempotency_key, payload_hash)
        if existing:
            return _load_transaction(conn, existing)

        transaction_id = str(uuid4())
        conn.execute(
            """
            INSERT INTO journal_transactions(transaction_id, operation_scope, idempotency_key, payload_hash, status, external_reference)
            VALUES (%s, %s, %s, %s, 'committed', %s)
            """,
            (transaction_id, operation_scope, idempotency_key, payload_hash, external_reference),
        )

        from_ver = _bump_version(conn, str(from_wallet_id), expected_from_version)
        to_ver = _bump_version(conn, str(to_wallet_id), expected_to_version)

        for seq, (wallet_id, entry_amount, entry_asset) in enumerate(entries, start=1):
            conn.execute(
                """
                INSERT INTO journal_entries(transaction_id, seq, wallet_id, amount, asset)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (transaction_id, seq, str(wallet_id), entry_amount, entry_asset),
            )

        _apply_projection(conn, str(from_wallet_id), asset, -amount, from_ver)
        _apply_projection(conn, str(to_wallet_id), asset, amount, to_ver)

        conn.execute(
            """
            INSERT INTO outbox_events(event_id, transaction_id, event_type, payload)
            VALUES (%s, %s, %s, %s::jsonb)
            """,
            (str(uuid4()), transaction_id, "wallet.transfer.committed", json.dumps(payload)),
        )
        conn.commit()
        return _load_transaction(conn, transaction_id)


def post_adjustment(
    *,
    idempotency_key: str,
    wallet_id: UUID,
    amount: Decimal,
    direction: str,
    asset: str,
    reason: str,
    expected_wallet_version: int | None,
) -> LedgerTransaction:
    operation_scope = "adjustment"
    sign = Decimal("1") if direction == "credit" else Decimal("-1")
    system_wallet_id = UUID(settings.system_wallet_id)

    payload = {
        "wallet_id": str(wallet_id),
        "amount": str(amount),
        "direction": direction,
        "asset": asset,
        "reason": reason,
        "expected_wallet_version": expected_wallet_version,
    }
    payload_hash = _payload_hash(payload)

    wallet_delta = amount * sign
    entries = [
        (wallet_id, wallet_delta, asset),
        (system_wallet_id, -wallet_delta, asset),
    ]
    _ensure_balanced(entries)

    with get_connection() as conn:
        existing = _fetch_existing_idempotent(conn, operation_scope, idempotency_key, payload_hash)
        if existing:
            return _load_transaction(conn, existing)

        transaction_id = str(uuid4())
        conn.execute(
            """
            INSERT INTO journal_transactions(transaction_id, operation_scope, idempotency_key, payload_hash, status, external_reference)
            VALUES (%s, %s, %s, %s, 'committed', %s)
            """,
            (transaction_id, operation_scope, idempotency_key, payload_hash, reason),
        )

        wallet_ver = _bump_version(conn, str(wallet_id), expected_wallet_version)
        system_ver = _bump_version(conn, str(system_wallet_id), None)

        for seq, (entry_wallet_id, entry_amount, entry_asset) in enumerate(entries, start=1):
            conn.execute(
                """
                INSERT INTO journal_entries(transaction_id, seq, wallet_id, amount, asset)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (transaction_id, seq, str(entry_wallet_id), entry_amount, entry_asset),
            )

        _apply_projection(conn, str(wallet_id), asset, wallet_delta, wallet_ver)
        _apply_projection(conn, str(system_wallet_id), asset, -wallet_delta, system_ver)

        conn.execute(
            """
            INSERT INTO outbox_events(event_id, transaction_id, event_type, payload)
            VALUES (%s, %s, %s, %s::jsonb)
            """,
            (
                str(uuid4()),
                transaction_id,
                "wallet.adjustment.committed",
                json.dumps(payload),
            ),
        )
        conn.commit()
        return _load_transaction(conn, transaction_id)


def get_transaction(transaction_id: UUID) -> LedgerTransaction:
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM journal_transactions WHERE transaction_id = %s", (str(transaction_id),)
        ).fetchone()
        if not exists:
            raise NotFoundError("transaction not found")
        return _load_transaction(conn, str(transaction_id))


def audit_balance(wallet_id: UUID) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT a.wallet_id, a.asset, COALESCE(SUM(e.amount), 0) AS balance
            FROM accounts a
            LEFT JOIN journal_entries e ON e.wallet_id = a.wallet_id AND e.asset = a.asset
            WHERE a.wallet_id = %s
            GROUP BY a.wallet_id, a.asset
            """,
            (str(wallet_id),),
        ).fetchone()
        if not row:
            raise NotFoundError("wallet not found")
        return {"wallet_id": row[0], "asset": row[1], "balance": row[2]}
