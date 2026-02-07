from decimal import Decimal
from uuid import uuid4

import pytest

from wallet_service.domain.errors import ValidationError
from wallet_service.ledger.service import _ensure_balanced


def test_rejects_less_than_two_entries():
    wallet = uuid4()
    with pytest.raises(ValidationError):
        _ensure_balanced([(wallet, Decimal("1"), "USD")])


def test_rejects_unbalanced_entries():
    w1 = uuid4()
    w2 = uuid4()
    with pytest.raises(ValidationError):
        _ensure_balanced([(w1, Decimal("5"), "USD"), (w2, Decimal("-4"), "USD")])


def test_accepts_balanced_entries():
    w1 = uuid4()
    w2 = uuid4()
    _ensure_balanced([(w1, Decimal("5"), "USD"), (w2, Decimal("-5"), "USD")])
