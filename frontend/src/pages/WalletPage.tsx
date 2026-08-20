import { useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchLedger, fetchWallet } from "../features/wallet/api";
import { useWebSocketTopic } from "../hooks/useWebSocketTopic";
import { useAuthStore } from "../features/auth/store";
import { formatMinor } from "../utils/money";

export function WalletPage() {
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((s) => s.accessToken);

  const walletQuery = useQuery({ queryKey: ["wallet"], queryFn: fetchWallet });
  const ledgerQuery = useQuery({ queryKey: ["ledger"], queryFn: fetchLedger });

  useWebSocketTopic(
    accessToken ? `/ws/user?token=${encodeURIComponent(accessToken)}` : null,
    (message) => {
      if (message.event === "BALANCE_UPDATED") {
        queryClient.invalidateQueries({ queryKey: ["wallet"] });
        queryClient.invalidateQueries({ queryKey: ["ledger"] });
      }
    },
  );

  const wallet = walletQuery.data;
  const entries = ledgerQuery.data ?? [];

  return (
    <div style={{ padding: "20px 24px 40px", maxWidth: 1100, margin: "0 auto" }}>
      <div className="section-head">
        <span className="section-title">Paper Wallet</span>
        <div className="rule" />
      </div>

      <div className="stat-row">
        <div className="stat-card">
          <div className="k">Balance</div>
          <div className="v">{wallet ? formatMinor(wallet.balance_minor) : "—"}</div>
        </div>
        <div className="stat-card">
          <div className="k">Exposure</div>
          <div className="v">{wallet ? formatMinor(wallet.reserved_minor) : "—"}</div>
        </div>
        <div className="stat-card">
          <div className="k">Available to Bet</div>
          <div className="v">{wallet ? formatMinor(wallet.available_minor) : "—"}</div>
        </div>
      </div>

      <div className="section-head">
        <span className="section-title">Transaction History</span>
        <div className="rule" />
        <span className="section-count">{entries.length} entries</span>
      </div>

      <div className="panel">
        {ledgerQuery.isLoading ? (
          <div className="center-py">Loading…</div>
        ) : entries.length === 0 ? (
          <div className="center-py">No ledger entries yet.</div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Balance Δ</th>
                  <th>Exposure Δ</th>
                  <th>Balance After</th>
                  <th>Exposure After</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id}>
                    <td className="mono text-muted">{new Date(entry.created_at).toLocaleString()}</td>
                    <td>
                      <span className="entry-type-badge">{entry.entry_type.replace(/_/g, " ")}</span>
                    </td>
                    <td className="mono">
                      {entry.balance_delta_minor === 0 ? "—" : formatMinor(entry.balance_delta_minor)}
                    </td>
                    <td className="mono">
                      {entry.reserved_delta_minor === 0 ? "—" : formatMinor(entry.reserved_delta_minor)}
                    </td>
                    <td className="mono">{formatMinor(entry.balance_after_minor)}</td>
                    <td className="mono">{formatMinor(entry.reserved_after_minor)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
