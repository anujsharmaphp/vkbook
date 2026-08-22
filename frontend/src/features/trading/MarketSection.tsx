import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchOrderBook } from "./api";
import { useWebSocketTopic } from "../../hooks/useWebSocketTopic";
import { useBetSlipStore } from "./betSlipStore";
import { ChevronDownIcon } from "../../design-system/icons";
import { formatMinorCompact } from "../../utils/money";
import { padLevels } from "./orderBookUtils";
import type { Market, OrderBookLevel, OrderSide } from "../../types/api";

const DEPTH = 3;

interface Props {
  market: Market;
}

export function MarketSection({ market }: Props) {
  const [expanded, setExpanded] = useState(true);
  const queryClient = useQueryClient();
  const setSelection = useBetSlipStore((s) => s.setSelection);
  const currentSelection = useBetSlipStore((s) => s.selection);

  const orderBookQuery = useQuery({
    queryKey: ["order-book", market.id],
    queryFn: () => fetchOrderBook(market.id),
    staleTime: 5_000,
  });

  useWebSocketTopic(`/ws/markets/${market.id}`, () => {
    queryClient.invalidateQueries({ queryKey: ["order-book", market.id] });
  });

  const isOpen = market.status === "OPEN";

  function handlePick(selectionId: string, side: OrderSide, level: OrderBookLevel | null) {
    if (!isOpen || !level) return;
    setSelection({
      marketId: market.id,
      marketName: market.name,
      selectionId,
      selectionName: market.selections.find((s) => s.id === selectionId)?.name ?? "",
      side,
      price: Number(level.price),
    });
  }

  function cellClass(side: OrderSide, selectionId: string, idx: number, level: OrderBookLevel | null): string {
    const classes = ["price-cell", side.toLowerCase()];
    if (idx === 0 && level) classes.push("best");
    if (!level) classes.push("empty");
    const isSelected =
      !!level &&
      currentSelection?.selectionId === selectionId &&
      currentSelection.side === side &&
      currentSelection.price === Number(level.price);
    if (isSelected) classes.push("selected");
    return classes.join(" ");
  }

  return (
    <div className="market-section">
      <button type="button" className="market-head" onClick={() => setExpanded((e) => !e)}>
        <ChevronDownIcon className={`chevron ${expanded ? "" : "collapsed"}`} />
        <span className="market-title">{market.name}</span>
        {!isOpen && <span className="market-sub">· {market.status}</span>}
        <div className="mh-spacer" />
      </button>

      {expanded && (
        <div className="market-body">
          <div className="market-grid-scroll">
            <div className="odds-grid-header">
              <div />
              <div className="lbl back-lbl">Back</div>
              <div className="lbl lay-lbl">Lay</div>
            </div>
            {market.selections.map((selection) => {
              const book = orderBookQuery.data?.selections.find((s) => s.selection_id === selection.id);
              const backLevels = padLevels(book?.back, DEPTH);
              const layLevels = padLevels(book?.lay, DEPTH);
              return (
                <div className="odds-row" key={selection.id}>
                  <div className="sel-name">{selection.name}</div>
                  {backLevels.map((level, idx) => (
                    <button
                      key={`back-${idx}`}
                      type="button"
                      disabled={!isOpen || !level}
                      className={cellClass("BACK", selection.id, idx, level)}
                      onClick={() => handlePick(selection.id, "BACK", level)}
                    >
                      <span className="p mono">{level ? level.price : "—"}</span>
                      <span className="s mono">
                        {level ? formatMinorCompact(level.available_size_minor) : ""}
                      </span>
                    </button>
                  ))}
                  {layLevels.map((level, idx) => (
                    <button
                      key={`lay-${idx}`}
                      type="button"
                      disabled={!isOpen || !level}
                      className={cellClass("LAY", selection.id, idx, level)}
                      onClick={() => handlePick(selection.id, "LAY", level)}
                    >
                      <span className="p mono">{level ? level.price : "—"}</span>
                      <span className="s mono">
                        {level ? formatMinorCompact(level.available_size_minor) : ""}
                      </span>
                    </button>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
