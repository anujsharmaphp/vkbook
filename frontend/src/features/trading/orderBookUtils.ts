import type { OrderBookLevel } from "../../types/api";

/** The backend already returns each side's levels sorted best-first
 * (MatchingService.get_order_book) — level 0 is what a new order would
 * match against first. */
export function bestLevel(levels: OrderBookLevel[] | undefined): OrderBookLevel | null {
  return levels && levels.length > 0 ? levels[0] : null;
}

/** Pads (or truncates) a level list to a fixed depth with nulls, so the
 * odds grid always renders the same number of columns regardless of how
 * much real liquidity is currently resting. */
export function padLevels(levels: OrderBookLevel[] | undefined, depth: number): (OrderBookLevel | null)[] {
  const list = (levels ?? []).slice(0, depth);
  const padded: (OrderBookLevel | null)[] = [...list];
  while (padded.length < depth) padded.push(null);
  return padded;
}
