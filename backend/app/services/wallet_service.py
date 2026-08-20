import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ConflictError, NotFoundError
from app.models.ledger_entry import LedgerEntry, LedgerEntryType
from app.models.wallet import Wallet
from app.repositories.ledger_entry_repository import LedgerEntryRepository
from app.repositories.wallet_repository import WalletRepository


class WalletService:
    """The wallet engine: a simulated-money wallet backed by an append-only
    ledger (docs/architecture.md Section G). Every mutation is
    reserve-or-release against `reserved_minor`, or a balance-affecting
    credit/debit — always posted as one LedgerEntry, deduplicated by
    idempotency_key so a retried call never double-applies (Section 21).

    `reserve`/`release`/`create_wallet` deliberately do not commit — they
    run inside the caller's transaction (e.g. MatchingService.place_order),
    so an order and its exposure hold are created or rejected atomically.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.wallets = WalletRepository(session)
        self.ledger = LedgerEntryRepository(session)

    async def create_wallet(
        self, user_id: uuid.UUID, initial_balance_minor: int | None = None
    ) -> Wallet:
        grant = initial_balance_minor
        if grant is None:
            grant = get_settings().initial_demo_balance_minor
        wallet = Wallet(user_id=user_id, balance_minor=0, reserved_minor=0)
        await self.wallets.add(wallet)
        await self._post_entry(
            wallet,
            LedgerEntryType.INITIAL_GRANT,
            balance_delta=grant,
            reserved_delta=0,
            idempotency_key=f"initial-grant:{user_id}",
        )
        return wallet

    async def get_wallet(self, user_id: uuid.UUID) -> Wallet:
        wallet = await self.wallets.get_by_user_id(user_id)
        if wallet is None:
            raise NotFoundError(f"Wallet for user {user_id} not found.", code="WALLET_NOT_FOUND")
        return wallet

    async def list_ledger(self, user_id: uuid.UUID) -> list[LedgerEntry]:
        wallet = await self.get_wallet(user_id)
        return await self.ledger.list_by_wallet(wallet.id)

    async def reserve(
        self,
        user_id: uuid.UUID,
        amount_minor: int,
        *,
        ref_order_id: uuid.UUID,
        idempotency_key: str,
    ) -> Wallet:
        wallet = await self.wallets.get_for_update(user_id)
        if wallet is None:
            raise NotFoundError(f"Wallet for user {user_id} not found.", code="WALLET_NOT_FOUND")

        if amount_minor > wallet.available_minor:
            raise ConflictError(
                f"Insufficient available balance: need {amount_minor}, "
                f"have {wallet.available_minor}.",
                code="INSUFFICIENT_BALANCE",
            )

        await self._post_entry(
            wallet,
            LedgerEntryType.EXPOSURE_HOLD,
            balance_delta=0,
            reserved_delta=amount_minor,
            ref_order_id=ref_order_id,
            idempotency_key=idempotency_key,
        )
        return wallet

    async def release(
        self,
        user_id: uuid.UUID,
        amount_minor: int,
        *,
        ref_order_id: uuid.UUID,
        idempotency_key: str,
    ) -> Wallet:
        wallet = await self.wallets.get_for_update(user_id)
        if wallet is None:
            raise NotFoundError(f"Wallet for user {user_id} not found.", code="WALLET_NOT_FOUND")

        await self._post_entry(
            wallet,
            LedgerEntryType.EXPOSURE_RELEASE,
            balance_delta=0,
            reserved_delta=-amount_minor,
            ref_order_id=ref_order_id,
            idempotency_key=idempotency_key,
        )
        return wallet

    async def post_settlement(
        self,
        user_id: uuid.UUID,
        *,
        balance_delta: int,
        reserved_delta: int,
        entry_type: LedgerEntryType,
        ref_bet_id: uuid.UUID,
        idempotency_key: str,
    ) -> Wallet:
        """Settlement realizes profit/loss (balance) and releases the
        exposure hold that bet's order placed (reserved) in one entry —
        see docs/architecture.md Section H."""
        wallet = await self.wallets.get_for_update(user_id)
        if wallet is None:
            raise NotFoundError(f"Wallet for user {user_id} not found.", code="WALLET_NOT_FOUND")

        await self._post_entry(
            wallet,
            entry_type,
            balance_delta=balance_delta,
            reserved_delta=reserved_delta,
            ref_bet_id=ref_bet_id,
            idempotency_key=idempotency_key,
        )
        return wallet

    async def _post_entry(
        self,
        wallet: Wallet,
        entry_type: LedgerEntryType,
        *,
        balance_delta: int,
        reserved_delta: int,
        idempotency_key: str,
        ref_order_id: uuid.UUID | None = None,
        ref_bet_id: uuid.UUID | None = None,
    ) -> LedgerEntry:
        existing = await self.ledger.get_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing

        wallet.balance_minor += balance_delta
        wallet.reserved_minor += reserved_delta
        entry = LedgerEntry(
            wallet_id=wallet.id,
            ref_order_id=ref_order_id,
            ref_bet_id=ref_bet_id,
            entry_type=entry_type,
            balance_delta_minor=balance_delta,
            reserved_delta_minor=reserved_delta,
            balance_after_minor=wallet.balance_minor,
            reserved_after_minor=wallet.reserved_minor,
            idempotency_key=idempotency_key,
        )
        await self.ledger.add(entry)
        return entry
