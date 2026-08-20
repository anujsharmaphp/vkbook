import { apiRequest } from "../../services/httpClient";
import type { LedgerEntryRead, WalletRead } from "../../types/api";

export function fetchWallet() {
  return apiRequest<WalletRead>("/wallet");
}

export function fetchLedger() {
  return apiRequest<LedgerEntryRead[]>("/wallet/ledger");
}
