import { sportIconFor, RugbyIcon, GolfIcon, HorseIcon, GenericSportIcon } from "../../design-system/icons";
import type { Sport } from "../../types/api";

interface Props {
  sports: Sport[];
  selectedSportId: string | null;
  onSelect: (sportId: string | null) => void;
  liveCountBySport: Map<string, number>;
}

// Not yet backed by real markets — shown so the nav reads like a full
// exchange rather than just the handful of sports currently seeded, with an
// honest "Soon" badge instead of a dead link into an empty catalog.
const COMING_SOON_SPORTS = [
  { label: "Rugby", Icon: RugbyIcon },
  { label: "Golf", Icon: GolfIcon },
  { label: "Horse Racing", Icon: HorseIcon },
  { label: "Kabaddi", Icon: GenericSportIcon },
];

export function SportSidebar({ sports, selectedSportId, onSelect, liveCountBySport }: Props) {
  return (
    <div>
      <div className="nav-heading">Sports</div>
      <button
        type="button"
        className={`sport-row ${selectedSportId === null ? "active" : ""}`}
        onClick={() => onSelect(null)}
      >
        <span className="label">All Sports</span>
      </button>
      {sports.map((sport) => {
        const SportIcon = sportIconFor(sport.code);
        const liveCount = liveCountBySport.get(sport.id) ?? 0;
        return (
          <button
            key={sport.id}
            type="button"
            className={`sport-row ${selectedSportId === sport.id ? "active" : ""}`}
            onClick={() => onSelect(sport.id)}
          >
            <SportIcon className="ico" />
            <span className="label">{sport.name}</span>
            {liveCount > 0 && <span className="live-dot" title={`${liveCount} live`} />}
          </button>
        );
      })}
      {sports.length === 0 && <div className="center-py">No sports yet.</div>}

      <div className="nav-heading" style={{ marginTop: 14 }}>
        More Sports
      </div>
      {COMING_SOON_SPORTS.map(({ label, Icon }) => (
        <div key={label} className="sport-row soon" aria-disabled="true">
          <Icon className="ico" />
          <span className="label">{label}</span>
          <span className="soon-badge">Soon</span>
        </div>
      ))}
    </div>
  );
}
