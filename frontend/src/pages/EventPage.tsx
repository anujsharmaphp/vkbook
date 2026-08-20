import { Link, useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchEventDetail, fetchMatchState } from "../features/catalog/api";
import { useCatalogLookup } from "../features/catalog/useCatalogLookup";
import { useWebSocketTopic } from "../hooks/useWebSocketTopic";
import { MarketSection } from "../features/trading/MarketSection";
import { BetSlip } from "../features/trading/BetSlip";
import { MyBetsPanel } from "../features/trading/MyBetsPanel";

export function EventPage() {
  const { eventId } = useParams<{ eventId: string }>();
  const { competitionInfoById } = useCatalogLookup();
  const queryClient = useQueryClient();

  const eventQuery = useQuery({
    queryKey: ["event-detail", eventId],
    queryFn: () => fetchEventDetail(eventId!),
    enabled: !!eventId,
  });

  const matchStateQuery = useQuery({
    queryKey: ["match-state", eventId],
    queryFn: () => fetchMatchState(eventId!),
    enabled: !!eventId,
    refetchInterval: (query) => (query.state.data?.status === "LIVE" ? 5000 : false),
  });

  useWebSocketTopic(eventId ? `/ws/events/${eventId}` : null, (message) => {
    if (message.event === "MATCH_STATE_UPDATED") {
      queryClient.invalidateQueries({ queryKey: ["match-state", eventId] });
    }
    if (message.event === "EVENT_STATUS_CHANGED") {
      queryClient.invalidateQueries({ queryKey: ["event-detail", eventId] });
    }
  });

  if (eventQuery.isLoading) {
    return <div className="center-py">Loading event…</div>;
  }

  if (eventQuery.isError || !eventQuery.data) {
    return <div className="center-py">Event not found.</div>;
  }

  const event = eventQuery.data;
  const info = competitionInfoById.get(event.competition_id);
  const isLive = event.status === "LIVE";
  const matchState = matchStateQuery.data;
  const showScore = !!matchState && matchState.status !== "SCHEDULED";

  return (
    <div style={{ padding: "20px 24px 40px", maxWidth: 1560, margin: "0 auto" }}>
      <div className="breadcrumb">
        <Link to="/">{info?.sport.name ?? "Sport"}</Link>
        <span className="sep">/</span>
        <Link to="/">{info?.competition.name ?? "Competition"}</Link>
        <span className="sep">/</span>
        <span className="current">{event.name}</span>
      </div>

      <div className="event-header">
        <div className="eh-top">
          <div className="eh-title">{event.name}</div>
          {isLive ? (
            <div className="live-badge">
              <span className="dot" />
              <span className="txt">LIVE</span>
            </div>
          ) : (
            <span className="status-badge">{event.status}</span>
          )}
        </div>
        <div className="eh-sub">
          {isLive ? "In progress" : new Date(event.start_time).toLocaleString()}
        </div>

        {showScore && matchState && (
          <div className="score-bar">
            <div className="score-stat">
              <span className="k">{matchState.batting_team}</span>
              <span className="v mono">
                {matchState.runs}/{matchState.wickets}
              </span>
            </div>
            <div className="score-stat">
              <span className="k">Overs</span>
              <span className="v mono">
                {matchState.overs} / {matchState.max_overs}
              </span>
            </div>
            <div className="score-stat">
              <span className="k">Target</span>
              <span className="v mono">{matchState.target_runs}</span>
            </div>
            {matchState.status === "COMPLETED" && matchState.winner_team && (
              <div className="score-stat">
                <span className="k">Result</span>
                <span className="v mono">{matchState.winner_team} won</span>
              </div>
            )}
          </div>
        )}

        {matchState?.markets_suspended && (
          <div className="suspended-banner">Markets suspended — wicket just fell</div>
        )}
      </div>

      <div className="layout-2col">
        <div className="col" style={{ paddingRight: 16 }}>
          {event.markets.length === 0 ? (
            <div className="center-py">No markets have been created for this event yet.</div>
          ) : (
            event.markets.map((market) => <MarketSection key={market.id} market={market} />)
          )}
        </div>

        <div className="col" style={{ paddingLeft: 16 }}>
          <div className="panel-sticky">
            <BetSlip />
            <MyBetsPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
