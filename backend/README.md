# Backend — Sports Exchange Simulator

FastAPI backend for the paper-trading sports exchange. See
[../docs/architecture.md](../docs/architecture.md) for the full system design.

## Local setup

```bash
cd backend
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt   # Windows
# source .venv/bin/activate && pip install -r requirements-dev.txt  # macOS/Linux

cp .env.example .env    # defaults to a local SQLite file, no external services needed
./.venv/Scripts/python.exe -m alembic upgrade head
./.venv/Scripts/python.exe -m app.db.seed               # seeds the "user"/"admin" roles
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for the interactive OpenAPI docs.

To point at PostgreSQL instead (e.g. once `docker compose up` is available,
added in Step 12), set `DATABASE_URL` in `.env` to a `postgresql+asyncpg://...`
DSN and re-run `alembic upgrade head`.

## Tests

```bash
./.venv/Scripts/python.exe -m pytest
./.venv/Scripts/python.exe -m ruff check app tests
```

Tests run against an isolated in-memory SQLite database per test — no setup
required. This is a deliberate dev-speed tradeoff (see architecture doc,
Section on testing); CI/production correctness against PostgreSQL-specific
behavior (row locking, JSONB) will be exercised once Docker Compose + a real
Postgres service lands in Step 12.

## What's implemented

**Step 2 — backend foundation**
- FastAPI app with structured JSON logging, request-ID middleware, and a
  consistent `{"error": {"code", "message", "request_id"}}` error shape.
- Async SQLAlchemy + Alembic, `User`/`Role`/`Permission` models with an RBAC
  many-to-many schema.
- JWT access/refresh auth (`/api/v1/auth/register|login|refresh|me`) with
  bcrypt password hashing and a `require_role(...)` dependency for admin-only
  routes.
- Repository + service layering: routes stay thin, all logic lives in
  `app/services/*`.

**Step 3 — market engine**
- Data-driven catalog: `Sport -> Competition -> Event -> Market -> Selection`,
  plus `MarketType.settlement_rule` so new market types are a data operation.
- `MarketService` owns the market status state machine
  (`OPEN -> SUSPENDED/CLOSED -> SETTLED`) with real optimistic locking via
  SQLAlchemy's `version_id_col` — a concurrent stale-version transition raises
  `MARKET_VERSION_CONFLICT` instead of silently clobbering the other writer.
- `EventPublisher` port (`app/events/publisher.py`) with a logging no-op
  implementation for now; Step 6 swaps in a Redis Streams publisher without
  touching any service code.
- Public read API (`/sports`, `/competitions`, `/events`, `/markets/{id}`)
  and admin write API (`/admin/*`, RBAC-gated) for the full catalog.

**Step 4 — matching engine**
- `Order` / `OrderMatch` / `Bet` models. A BACK order's price is the odds
  floor its owner accepts; a LAY order's price is the odds ceiling
  (liability cap) its owner accepts. Two orders cross whenever
  `lay.price >= back.price`, always executing at the resting maker's price.
- `MatchingService.place_order` walks resting opposite-side orders
  best-price-first (highest eligible LAY price for a BACK taker, lowest
  eligible BACK price for a LAY taker), partially or fully filling the
  taker and creating one BACK + one LAY `Bet` per fill.
- Row-level `SELECT ... FOR UPDATE` (real locking on PostgreSQL, a no-op on
  the SQLite dev DB) plus per-order optimistic `version_id_col` ensure two
  takers can never collectively over-consume one resting order's liquidity —
  covered by `test_shared_liquidity_never_over_consumed_across_two_takers`.
- Idempotency-key replay, cancellation, and market-suspended rejection are
  all covered by `tests/test_trading.py`.
- `GET /markets/{id}/order-book` exposes the literal aggregated book (each
  side's own resting orders, best price first) — no wallet checks yet.

**Step 5 — wallet/ledger**
- `Wallet` (balance/reserved, optimistic-locked) + append-only `LedgerEntry`
  rows; `wallet.balance/reserved` are a materialized cache, the ledger is
  the source of truth. Registration auto-provisions a wallet with the demo
  balance (`INITIAL_GRANT` entry).
- `MatchingService.place_order` now reserves the order's full worst-case
  exposure (stake for BACK, `stake*(price-1)` liability for LAY) before
  matching — insufficient balance rejects the order atomically with the
  attempted DB insert rolled back. `cancel_order` releases only the
  unmatched remainder's share; the matched portion stays held until
  settlement (Step 9).
- Every reserve/release is idempotency-keyed off the order id, so a retried
  call can never double-apply (`tests/test_wallet.py`).
- `GET /wallet`, `GET /wallet/ledger`.

**Step 6 — WebSocket layer**
- `ConnectionManager` (`app/websocket/manager.py`) tracks topic
  subscriptions (`market:{id}`, `event:{id}`, `user:{id}`) in-process.
  `WebSocketEventPublisher` is the live `EventPublisher` implementation now
  (replacing the logging no-op) — every domain event MarketService /
  MatchingService / WalletService already published now reaches connected
  clients immediately, no polling.
- `/ws/markets/{id}`, `/ws/events/{id}`, `/ws/user` (auth via `?token=`
  query param, since browsers can't set WS handshake headers). Client
  heartbeat (`"ping"` -> `"pong"`) and per-topic monotonic `sequence`
  numbers are in place for the frontend's gap-detection/resync logic
  (Step 7).
- This is the single-instance, in-process fanout — swapping in a Redis
  Streams publisher/consumer for horizontal scaling (the production path
  described in docs/architecture.md) doesn't require touching any service
  code, only `app/events/publisher.py`.
- Verified with a live smoke test (`scripts/` not checked in — run against
  a booted `uvicorn` instance): placing an order over REST pushes
  `ORDER_PLACED` to `/ws/markets/{id}` and `BALANCE_UPDATED` to the
  trader's own `/ws/user` in real time.

Simulator, admin UI, and the React frontend land in the following steps.
