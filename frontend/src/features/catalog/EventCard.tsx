import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchEventDetail } from "./api";
import { fetchOrderBook } from "../trading/api";
import { bestLevel } from "../trading/orderBookUtils";
import { formatMinorCompact } from "../../utils/money";
import type { EventRead } from "../../types/api";

interface Props {
  event: EventRead;
  competitionName?: string;
  sportName?: string;
}

export function EventCard({ event, competitionName, sportName }: Props) {
  const detailQuery = useQuery({
    queryKey: ["event-detail", event.id],
    queryFn: () => fetchEventDetail(event.id),
    staleTime: 30_000,
  });

  const primaryMarket = detailQuery.data?.markets[0];

  const orderBookQuery = useQuery({
    queryKey: ["order-book", primaryMarket?.id],
    queryFn: () => fetchOrderBook(primaryMarket!.id),
    enabled: !!primaryMarket,
    staleTime: 5_000,
  });

  const isLive = event.status === "LIVE";

  return (
    <Link to={`/events/${event.id}`} className="event-card">
      <div className="event-card-top">
        <div className="event-meta">
          <div className="competition">
            {sportName ?? "Sport"}
            {competitionName ? ` · ${competitionName}` : ""}
          </div>
          <div className="matchup">{event.name}</div>
          <div className="score-line">
            {isLive ? "In progress" : new Date(event.start_time).toLocaleString()}
          </div>
        </div>
        {isLive ? (
          <div className="live-badge">
            <span className="dot" />
            <span className="txt">LIVE</span>
          </div>
        ) : (
          <span className="status-badge">{event.status}</span>
        )}
      </div>

      {primaryMarket && primaryMarket.selections.length > 0 && (
        <div className="odds-preview">
          {primaryMarket.selections.slice(0, 2).map((selection) => {
            const book = orderBookQuery.data?.selections.find((s) => s.selection_id === selection.id);
            const back = bestLevel(book?.back);
            const lay = bestLevel(book?.lay);
            return (
              <div className="op-row" key={selection.id}>
                <div className="op-name">{selection.name}</div>
                <div className="price-cell back">
                  <span className="p mono">{back ? back.price : "—"}</span>
                  <span className="s mono">{back ? formatMinorCompact(back.available_size_minor) : ""}</span>
                </div>
                <div className="price-cell lay">
                  <span className="p mono">{lay ? lay.price : "—"}</span>
                  <span className="s mono">{lay ? formatMinorCompact(lay.available_size_minor) : ""}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Link>
  );
}
