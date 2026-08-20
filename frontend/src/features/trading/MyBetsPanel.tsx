import { useMemo } from "react";
import { useQueries, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchBets } from "./api";
import { fetchMarket } from "../catalog/api";
import { useWebSocketTopic } from "../../hooks/useWebSocketTopic";
import { useAuthStore } from "../auth/store";
import { formatMinor } from "../../utils/money";

export function MyBetsPanel() {
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((s) => s.accessToken);

  const betsQuery = useQuery({ queryKey: ["bets"], queryFn: () => fetchBets() });
  const bets = betsQuery.data ?? [];

  const uniqueMarketIds = useMemo(() => Array.from(new Set(bets.map((b) => b.market_id))), [bets]);

  const marketQueries = useQueries({
    queries: uniqueMarketIds.map((marketId) => ({
      queryKey: ["market", marketId],
      queryFn: () => fetchMarket(marketId),
      staleTime: 5 * 60_000,
    })),
  });

  const selectionNameById = new Map<string, string>();
  const marketNameById = new Map<string, string>();
  for (const q of marketQueries) {
    if (q.data) {
      marketNameById.set(q.data.id, q.data.name);
      for (const sel of q.data.selections) selectionNameById.set(sel.id, sel.name);
    }
  }

  useWebSocketTopic(
    accessToken ? `/ws/user?token=${encodeURIComponent(accessToken)}` : null,
    (message) => {
      if (message.event === "BET_SETTLED" || message.event === "BALANCE_UPDATED") {
        queryClient.invalidateQueries({ queryKey: ["bets"] });
      }
    },
  );

  return (
    <div className="panel">
      <div className="panel-head">
        <span className="panel-title">My Bets</span>
        <span className="panel-badge">{bets.length}</span>
      </div>
      <div className="panel-body">
        {betsQuery.isLoading ? (
          <div className="center-py">Loading…</div>
        ) : bets.length === 0 ? (
          <div className="center-py">No bets yet.</div>
        ) : (
          bets.map((bet) => (
            <div className="bet-row" key={bet.id}>
              <div className="bet-row-top">
                <span className="bet-sel">{selectionNameById.get(bet.selection_id) ?? "Selection"}</span>
                <span className={`side-chip ${bet.side.toLowerCase()}`}>{bet.side}</span>
              </div>
              <div className="bet-market-name">{marketNameById.get(bet.market_id) ?? ""}</div>
              <div className="bet-row-stats">
                <div className="bet-stat">
                  <span className="k">Price</span>
                  <span className="v mono">{bet.price}</span>
                </div>
                <div className="bet-stat">
                  <span className="k">Stake</span>
                  <span className="v mono">{formatMinor(bet.stake_minor)}</span>
                </div>
                <div className="bet-stat">
                  <span className="k">{bet.side === "BACK" ? "Risk" : "Liability"}</span>
                  <span className="v mono">{formatMinor(bet.liability_minor)}</span>
                </div>
                <span className="status-pill">{bet.status}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
