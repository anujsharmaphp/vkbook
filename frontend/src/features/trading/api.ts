import { apiRequest } from "../../services/httpClient";
import type { BetRead, OrderBook, OrderCreate, OrderRead } from "../../types/api";

export function fetchOrderBook(marketId: string) {
  return apiRequest<OrderBook>(`/markets/${marketId}/order-book`);
}

export function placeOrder(payload: OrderCreate) {
  return apiRequest<OrderRead>("/orders", { method: "POST", body: payload });
}

export function cancelOrder(orderId: string) {
  return apiRequest<OrderRead>(`/orders/${orderId}`, { method: "DELETE" });
}

export function fetchOrders(marketId?: string) {
  return apiRequest<OrderRead[]>("/orders", { query: { market_id: marketId } });
}

export function fetchBets(marketId?: string) {
  return apiRequest<BetRead[]>("/bets", { query: { market_id: marketId } });
}
