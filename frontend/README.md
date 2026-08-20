# Frontend — Chalkline Paper Exchange

React + TypeScript + Vite frontend for the paper-trading sports exchange. See
[../docs/architecture.md](../docs/architecture.md) for the full system design
and [../backend/README.md](../backend/README.md) for the API it talks to.

## Local setup

```bash
cd frontend
npm install
cp .env.example .env   # points at the backend; defaults to http://127.0.0.1:8000/api/v1
npm run dev
```

Requires the backend running (`cd ../backend && uvicorn app.main:app`) — every
screen is wired to real endpoints, there is no mock data.

## Scripts

```bash
npm run dev        # Vite dev server (http://localhost:5173)
npm run build      # tsc --noEmit, then production build
npm run typecheck  # tsc --noEmit only
```

## What's implemented (Step 7 — React frontend)

- **Auth**: register/login against `/auth/*`, JWT access+refresh persisted in
  `localStorage` (Zustand `persist`), automatic refresh-and-retry on a 401
  from any request (`services/httpClient.ts`).
- **Home**: sports sidebar (`GET /sports`, data-driven — no sport is
  hard-coded), live/upcoming event lists (`GET /events`), each event card
  previewing real best back/lay prices for its primary market.
- **Event page**: breadcrumb, event header, every market rendered as a
  collapsible back/lay depth grid backed by `GET /markets/{id}/order-book`,
  live-updated over `/ws/markets/{id}` (event arrives → invalidate → refetch;
  no polling). Suspended/closed markets disable their price cells.
- **Bet Slip**: click any price to draft a selection; stake input with
  client-side potential-return/profit/liability preview (display only — the
  backend independently recalculates and is authoritative); submits to
  `POST /orders` with a fresh idempotency key per attempt.
- **My Bets**: `GET /bets`, cross-referenced with `GET /markets/{id}` to show
  human-readable selection/market names (BetRead only carries ids).
- **Wallet**: balance/exposure/available stat cards plus the full ledger
  history table (`GET /wallet`, `GET /wallet/ledger`), all live-updated via
  `/ws/user` `BALANCE_UPDATED` pushes.
- **WebSocket manager** (`services/websocket.ts`): shared sockets per topic
  path, exponential-backoff reconnect, heartbeat ping/pong — matches the
  reconnect/backoff/heartbeat requirements in the architecture doc.
- **Design system**: CSS custom properties for a light and a dark theme
  (toggle in the header, persisted, defaults to OS preference), with the top
  bar deliberately black in both. Back = blue, lay = pink throughout;
  monospace tabular figures for every price/money value.

Admin UI (Step 8), the match simulator's live-score display (depends on
Step 9 existing on the backend), and end-to-end Playwright tests (Step 10)
are not part of this step.

### A deliberate backend fix made alongside this step

While wiring up "click a price to bet," `MatchingService.get_order_book` was
changed from a literal dump of `Order.side` to the standard exchange display
convention: the **displayed "back" price is sourced from resting LAY
orders**, and the **displayed "lay" price from resting BACK orders**. This
is what makes clicking a displayed price actually cross and match — a
literal display doesn't let a same-side click cross same-side liquidity.
Backend tests were updated to match (`tests/test_trading.py`).
