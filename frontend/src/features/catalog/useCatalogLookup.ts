import { useQuery } from "@tanstack/react-query";
import { fetchCompetitions, fetchSports } from "./api";
import type { Competition, Sport } from "../../types/api";

export interface CompetitionInfo {
  competition: Competition;
  sport: Sport;
}

/** Sports/competitions rarely change — fetched once and joined client-side
 * so event listings can show human-readable names without an N+1 fetch
 * per event (the backend only returns ids on EventRead). */
export function useCatalogLookup() {
  const sportsQuery = useQuery({ queryKey: ["sports"], queryFn: fetchSports, staleTime: 5 * 60_000 });
  const competitionsQuery = useQuery({
    queryKey: ["competitions"],
    queryFn: () => fetchCompetitions(),
    staleTime: 5 * 60_000,
  });

  const sportsById = new Map((sportsQuery.data ?? []).map((sport) => [sport.id, sport]));
  const competitionInfoById = new Map<string, CompetitionInfo>();
  for (const competition of competitionsQuery.data ?? []) {
    const sport = sportsById.get(competition.sport_id);
    if (sport) competitionInfoById.set(competition.id, { competition, sport });
  }

  return {
    sports: sportsQuery.data ?? [],
    isLoading: sportsQuery.isLoading || competitionsQuery.isLoading,
    competitionInfoById,
  };
}
