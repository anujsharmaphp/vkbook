import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { fetchEvents } from "../features/catalog/api";
import { useCatalogLookup } from "../features/catalog/useCatalogLookup";
import { SportSidebar } from "../features/catalog/SportSidebar";
import { EventCard } from "../features/catalog/EventCard";
import { BetSlip } from "../features/trading/BetSlip";
import { MyBetsPanel } from "../features/trading/MyBetsPanel";

export function HomePage() {
  const [selectedSportId, setSelectedSportId] = useState<string | null>(null);
  const { sports, competitionInfoById } = useCatalogLookup();

  const eventsQuery = useQuery({
    queryKey: ["events"],
    queryFn: () => fetchEvents(),
    staleTime: 15_000,
  });

  const events = eventsQuery.data ?? [];

  const eventsWithInfo = useMemo(
    () =>
      events.map((event) => ({
        event,
        info: competitionInfoById.get(event.competition_id),
      })),
    [events, competitionInfoById],
  );

  const filtered = selectedSportId
    ? eventsWithInfo.filter((e) => e.info?.sport.id === selectedSportId)
    : eventsWithInfo;

  const liveEvents = filtered.filter((e) => e.event.status === "LIVE");
  const upcomingEvents = filtered
    .filter((e) => e.event.status === "SCHEDULED")
    .sort((a, b) => a.event.start_time.localeCompare(b.event.start_time));

  const liveCountBySport = new Map<string, number>();
  for (const { event, info } of eventsWithInfo) {
    if (event.status === "LIVE" && info) {
      liveCountBySport.set(info.sport.id, (liveCountBySport.get(info.sport.id) ?? 0) + 1);
    }
  }

  return (
    <div className="layout-3col">
      <div className="col">
        <div className="col-scroll">
          <SportSidebar
            sports={sports}
            selectedSportId={selectedSportId}
            onSelect={setSelectedSportId}
            liveCountBySport={liveCountBySport}
          />
        </div>
      </div>

      <div className="col">
        <div className="col-scroll">
          <div className="section-head">
            <span className="section-title">In-Play</span>
            <div className="rule" />
            <span className="section-count">{liveEvents.length} live</span>
          </div>

          {eventsQuery.isLoading ? (
            <div className="center-py">Loading events…</div>
          ) : liveEvents.length === 0 ? (
            <div className="empty-state" style={{ marginBottom: 22 }}>
              <div className="txt">No live events right now.</div>
            </div>
          ) : (
            liveEvents.map(({ event, info }) => (
              <EventCard
                key={event.id}
                event={event}
                competitionName={info?.competition.name}
                sportName={info?.sport.name}
              />
            ))
          )}

          <div className="section-head" style={{ marginTop: 26 }}>
            <span className="section-title">Upcoming</span>
            <div className="rule" />
            <span className="section-count">{upcomingEvents.length}</span>
          </div>

          {upcomingEvents.length === 0 ? (
            <div className="center-py">Nothing scheduled.</div>
          ) : (
            <div className="panel">
              <div className="panel-body" style={{ padding: "6px 16px" }}>
                {upcomingEvents.map(({ event, info }) => (
                  <Link className="upcoming-row" to={`/events/${event.id}`} key={event.id}>
                    <div className="upcoming-time mono">
                      {new Date(event.start_time).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>
                    <div>
                      <div className="upcoming-teams">{event.name}</div>
                      <div className="upcoming-comp">
                        {info?.sport.name ?? "Sport"} · {info?.competition.name ?? "Competition"}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="col">
        <div className="col-scroll">
          <BetSlip />
          <MyBetsPanel />
        </div>
      </div>
    </div>
  );
}
