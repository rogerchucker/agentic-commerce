from uuid import UUID

from fastapi import APIRouter, Depends

from wallet_service.api.deps import get_auth_context, require_idempotency_key
from wallet_service.api.schemas import (
    AdjustmentRequest,
    BalanceResponse,
    CreateWalletRequest,
    TransactionResponse,
    TransferRequest,
    WalletResponse,
)
from wallet_service.auth.jwt import AuthContext, require_scope
from wallet_service.ledger import service

router = APIRouter(prefix="/v1", tags=["wallet"])


@router.post("/wallets", response_model=WalletResponse)
def create_wallet_endpoint(
    request: CreateWalletRequest,
    auth: AuthContext = Depends(get_auth_context),
):
    require_scope(auth, "wallet:write")
    result = service.create_wallet(request.wallet_id, request.asset)
    return WalletResponse(**result)


@router.get("/wallets/{wallet_id}/balance", response_model=BalanceResponse)
def get_balance_endpoint(
    wallet_id: UUID,
    auth: AuthContext = Depends(get_auth_context),
):
    require_scope(auth, "wallet:read")
    result = service.get_balance(wallet_id)
    return BalanceResponse(**result)


@router.get("/wallets/{wallet_id}/balance/audit", response_model=BalanceResponse)
def audit_balance_endpoint(
    wallet_id: UUID,
    auth: AuthContext = Depends(get_auth_context),
):
    require_scope(auth, "wallet:read")
    projected = service.get_balance(wallet_id)
    audit = service.audit_balance(wallet_id)
    return BalanceResponse(
        wallet_id=audit["wallet_id"],
        asset=audit["asset"],
        balance=audit["balance"],
        version=projected["version"],
        as_of=projected["as_of"],
    )


@router.post("/transfers", response_model=TransactionResponse)
def transfer_endpoint(
    request: TransferRequest,
    idempotency_key: str = Depends(require_idempotency_key),
    auth: AuthContext = Depends(get_auth_context),
):
    require_scope(auth, "wallet:write")
    tx = service.post_transfer(
        idempotency_key=idempotency_key,
        from_wallet_id=request.from_wallet_id,
        to_wallet_id=request.to_wallet_id,
        amount=request.amount,
        asset=request.asset,
        external_reference=request.external_reference,
        expected_from_version=request.expected_from_version,
        expected_to_version=request.expected_to_version,
    )
    return TransactionResponse(**tx.__dict__)


@router.post("/adjustments", response_model=TransactionResponse)
def adjustment_endpoint(
    request: AdjustmentRequest,
    idempotency_key: str = Depends(require_idempotency_key),
    auth: AuthContext = Depends(get_auth_context),
):
    require_scope(auth, "wallet:admin")
    tx = service.post_adjustment(
        idempotency_key=idempotency_key,
        wallet_id=request.wallet_id,
        amount=request.amount,
        direction=request.direction,
        asset=request.asset,
        reason=request.reason,
        expected_wallet_version=request.expected_wallet_version,
    )
    return TransactionResponse(**tx.__dict__)


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction_endpoint(
    transaction_id: UUID,
    auth: AuthContext = Depends(get_auth_context),
):
    require_scope(auth, "wallet:read")
    tx = service.get_transaction(transaction_id)
    return TransactionResponse(**tx.__dict__)
