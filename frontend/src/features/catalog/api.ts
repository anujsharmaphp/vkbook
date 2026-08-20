import { apiRequest } from "../../services/httpClient";
import type { Competition, EventDetail, EventRead, Market, MatchState, Sport } from "../../types/api";

export function fetchSports() {
  return apiRequest<Sport[]>("/sports");
}

export function fetchCompetitions(sportId?: string) {
  return apiRequest<Competition[]>("/competitions", { query: { sport_id: sportId } });
}

export function fetchEvents(params: { competitionId?: string; status?: string } = {}) {
  return apiRequest<EventRead[]>("/events", {
    query: { competition_id: params.competitionId, status: params.status },
  });
}

export function fetchEventDetail(eventId: string) {
  return apiRequest<EventDetail>(`/events/${eventId}`);
}

export function fetchMarket(marketId: string) {
  return apiRequest<Market>(`/markets/${marketId}`);
}

export function fetchMatchState(eventId: string) {
  return apiRequest<MatchState | null>(`/events/${eventId}/match-state`);
}
