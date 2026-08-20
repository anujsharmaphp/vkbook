import type { OrderSide } from "../types/api";

/** Display-only estimates for the bet slip. The backend independently
 * recalculates and is authoritative — see MatchingService/WalletService. */

export function potentialReturnMinor(side: OrderSide, price: number, stakeMinor: number): number {
  if (side === "BACK") return Math.round(stakeMinor * price);
  return stakeMinor;
}

export function potentialProfitMinor(side: OrderSide, price: number, stakeMinor: number): number {
  if (side === "BACK") return Math.round(stakeMinor * (price - 1));
  return stakeMinor;
}

export function liabilityMinor(side: OrderSide, price: number, stakeMinor: number): number {
  if (side === "BACK") return stakeMinor;
  return Math.round(stakeMinor * (price - 1));
}
