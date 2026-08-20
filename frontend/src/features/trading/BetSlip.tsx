import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { useBetSlipStore } from "./betSlipStore";
import { placeOrder } from "./api";
import { ApiError } from "../../services/httpClient";
import { formatMinor } from "../../utils/money";
import { liabilityMinor, potentialProfitMinor, potentialReturnMinor } from "../../utils/odds";
import { CloseIcon, EmptySlipIcon } from "../../design-system/icons";
import { pushSuccessToast } from "../../store/toast";

export function BetSlip() {
  const selection = useBetSlipStore((s) => s.selection);
  const stakeMinor = useBetSlipStore((s) => s.stakeMinor);
  const setStakeMinor = useBetSlipStore((s) => s.setStakeMinor);
  const clear = useBetSlipStore((s) => s.clear);
  const queryClient = useQueryClient();
  const [placeError, setPlaceError] = useState<string | null>(null);

  const placeMutation = useMutation({
    mutationFn: placeOrder,
    onSuccess: (order) => {
      setPlaceError(null);
      clear();
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
      queryClient.invalidateQueries({ queryKey: ["bets"] });
      queryClient.invalidateQueries({ queryKey: ["order-book", order.market_id] });
      pushSuccessToast(
        order.status === "MATCHED" ? "Bet matched" : "Bet placed",
        order.status === "MATCHED"
          ? "Fully matched at the best available price."
          : order.status === "PARTIALLY_MATCHED"
            ? "Partially matched — the rest is resting in the order book."
            : "Resting in the order book, waiting for a match.",
      );
    },
    onError: (err) => {
      setPlaceError(err instanceof ApiError ? err.message : "Could not place the bet. Please try again.");
    },
  });

  if (!selection) {
    return (
      <div className="panel">
        <div className="panel-head">
          <span className="panel-title">Bet Slip</span>
          <span className="panel-badge">0</span>
        </div>
        <div className="panel-body">
          <div className="empty-state">
            <EmptySlipIcon className="ico" />
            <div className="txt">
              Click any price to add
              <br />a selection to your slip
            </div>
          </div>
        </div>
      </div>
    );
  }

  const price = selection.price;
  const potentialReturn = potentialReturnMinor(selection.side, price, stakeMinor);
  const potentialProfit = potentialProfitMinor(selection.side, price, stakeMinor);
  const liability = liabilityMinor(selection.side, price, stakeMinor);

  function handleStakeChange(raw: string) {
    const digits = raw.replace(/[^0-9]/g, "");
    setStakeMinor(digits ? Number(digits) * 100 : 0);
  }

  function handlePlace() {
    if (!selection) return;
    setPlaceError(null);
    placeMutation.mutate({
      market_id: selection.marketId,
      selection_id: selection.selectionId,
      side: selection.side,
      price: selection.price.toFixed(2),
      stake_minor: stakeMinor,
      idempotency_key: crypto.randomUUID(),
    });
  }

  return (
    <div className="panel">
      <div className="panel-head">
        <span className="panel-title">Bet Slip</span>
        <span className="panel-badge">1</span>
      </div>
      <div className="panel-body">
        <div className="slip-card">
          <div className="slip-card-top">
            <span className="slip-sel-name">{selection.selectionName}</span>
            <button type="button" className="slip-remove" onClick={clear} aria-label="Remove selection">
              <CloseIcon />
            </button>
          </div>
          <div className="slip-market-name">{selection.marketName}</div>
          <div className="slip-price-row">
            <span className={`side-chip ${selection.side.toLowerCase()}`}>{selection.side}</span>
            <span className={`slip-price mono ${selection.side.toLowerCase()}`}>{price.toFixed(2)}</span>
          </div>

          <div className="stake-field">
            <div className="field-label">Stake</div>
            <div className="stake-input-wrap">
              <span className="cur mono">₹</span>
              <input
                className="mono"
                inputMode="numeric"
                value={stakeMinor ? String(stakeMinor / 100) : ""}
                onChange={(e) => handleStakeChange(e.target.value)}
              />
            </div>
          </div>

          {selection.side === "BACK" ? (
            <>
              <div className="slip-calc-row">
                <span>Potential Return</span>
                <span className="v mono">{formatMinor(potentialReturn)}</span>
              </div>
              <div className="slip-calc-row highlight back">
                <span>Potential Profit</span>
                <span className="v mono">{formatMinor(potentialProfit)}</span>
              </div>
            </>
          ) : (
            <div className="slip-calc-row highlight lay">
              <span>Liability</span>
              <span className="v mono">{formatMinor(liability)}</span>
            </div>
          )}

          <button
            type="button"
            className={`place-btn ${selection.side === "BACK" ? "btn-back" : "btn-lay"}`}
            disabled={placeMutation.isPending || stakeMinor <= 0}
            onClick={handlePlace}
          >
            {placeMutation.isPending ? "Placing…" : "Place Paper Bet"}
          </button>

          {placeError && <div className="slip-error">{placeError}</div>}

          <div className="slip-note">
            Simulated stake only — no real funds are at risk. Odds may move before confirmation.
          </div>
        </div>
      </div>
    </div>
  );
}
