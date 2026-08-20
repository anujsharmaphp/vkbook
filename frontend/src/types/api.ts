export type UUID = string;

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    request_id: string | null;
    details?: unknown;
  };
}

// ---- auth ----
export interface UserRead {
  id: UUID;
  email: string;
  display_name: string;
  status: string;
  roles: string[];
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ---- catalog ----
export interface Sport {
  id: UUID;
  code: string;
  name: string;
}

export interface Competition {
  id: UUID;
  sport_id: UUID;
  name: string;
}

export interface EventRead {
  id: UUID;
  competition_id: UUID;
  name: string;
  status: string;
  start_time: string;
}

export interface MarketTypeRead {
  id: UUID;
  code: string;
  name: string;
  settlement_rule: Record<string, unknown>;
}

export interface Selection {
  id: UUID;
  market_id: UUID;
  name: string;
  display_order: number;
}

export type MarketStatus = "OPEN" | "SUSPENDED" | "CLOSED" | "SETTLED";

export interface Market {
  id: UUID;
  event_id: UUID;
  market_type_id: UUID;
  name: string;
  status: MarketStatus;
  version: number;
  selections: Selection[];
}

export interface EventDetail extends EventRead {
  markets: Market[];
}

// ---- trading ----
export type OrderSide = "BACK" | "LAY";

export interface OrderCreate {
  market_id: UUID;
  selection_id: UUID;
  side: OrderSide;
  price: string;
  stake_minor: number;
  idempotency_key: string;
}

export type OrderStatus = "OPEN" | "PARTIALLY_MATCHED" | "MATCHED" | "CANCELLED";

export interface OrderRead {
  id: UUID;
  market_id: UUID;
  selection_id: UUID;
  side: OrderSide;
  price: string;
  stake_minor: number;
  matched_minor: number;
  remaining_minor: number;
  status: OrderStatus;
}

export type BetStatus = "MATCHED" | "SETTLED" | "VOID";

export interface BetRead {
  id: UUID;
  order_id: UUID;
  market_id: UUID;
  selection_id: UUID;
  side: OrderSide;
  price: string;
  stake_minor: number;
  liability_minor: number;
  status: BetStatus;
}

export interface OrderBookLevel {
  price: string;
  available_size_minor: number;
}

export interface OrderBookSelection {
  selection_id: UUID;
  back: OrderBookLevel[];
  lay: OrderBookLevel[];
}

export interface OrderBook {
  market_id: UUID;
  selections: OrderBookSelection[];
}

// ---- wallet ----
export interface WalletRead {
  balance_minor: number;
  reserved_minor: number;
  available_minor: number;
}

export interface LedgerEntryRead {
  id: UUID;
  entry_type: string;
  balance_delta_minor: number;
  reserved_delta_minor: number;
  balance_after_minor: number;
  reserved_after_minor: number;
  ref_order_id: UUID | null;
  ref_bet_id: UUID | null;
  created_at: string;
}

// ---- simulator ----
export interface MatchState {
  event_id: UUID;
  status: "SCHEDULED" | "LIVE" | "PAUSED" | "COMPLETED";
  batting_team: string;
  bowling_team: string;
  runs: number;
  wickets: number;
  overs: string;
  max_overs: number;
  target_runs: number;
  markets_suspended: boolean;
  winner_team: string | null;
}

// ---- websocket ----
export interface WsMessage {
  event: string;
  sequence: number;
  [key: string]: unknown;
}
