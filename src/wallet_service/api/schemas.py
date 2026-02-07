from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CreateWalletRequest(BaseModel):
    wallet_id: UUID
    asset: str = Field(default="USD", min_length=3, max_length=12)


class WalletResponse(BaseModel):
    wallet_id: UUID
    asset: str
    version: int
    created_at: datetime


class BalanceResponse(BaseModel):
    wallet_id: UUID
    asset: str
    balance: Decimal
    version: int
    as_of: datetime


class TransferRequest(BaseModel):
    from_wallet_id: UUID
    to_wallet_id: UUID
    amount: Decimal = Field(gt=0)
    asset: str = Field(default="USD", min_length=3, max_length=12)
    external_reference: str | None = None
    expected_from_version: int | None = None
    expected_to_version: int | None = None


class AdjustmentRequest(BaseModel):
    wallet_id: UUID
    amount: Decimal = Field(gt=0)
    direction: Literal["credit", "debit"]
    asset: str = Field(default="USD", min_length=3, max_length=12)
    reason: str
    expected_wallet_version: int | None = None


class JournalEntryDTO(BaseModel):
    account_id: UUID
    amount: Decimal
    asset: str


class TransactionResponse(BaseModel):
    transaction_id: UUID
    operation_scope: str
    idempotency_key: str
    payload_hash: str
    status: str
    created_at: datetime
    external_reference: str | None = None
    entries: list[JournalEntryDTO]
