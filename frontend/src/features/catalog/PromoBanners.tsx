import { Link } from "react-router-dom";

interface Props {
  onBrowseLive: () => void;
  onBrowseAll: () => void;
}

// Purely cosmetic — every CTA routes into real, working parts of the app
// (no "casino"/jackpot-style banners, since this is a paper-money sports
// exchange only, not a gambling product).
export function PromoBanners({ onBrowseLive, onBrowseAll }: Props) {
  return (
    <div className="promo-banners">
      <div
        className="promo-card promo-image-card"
        style={{ backgroundImage: "url(/promo-cricket.png)" }}
      >
        <button type="button" className="btn btn-block" onClick={onBrowseLive}>
          Bet Live
        </button>
      </div>

      <div
        className="promo-card promo-image-card"
        style={{ backgroundImage: "url(/promo-football.png)" }}
      >
        <button type="button" className="btn btn-block" onClick={onBrowseAll}>
          Browse Markets
        </button>
      </div>

      <div className="promo-card accent-neutral">
        <div className="promo-eyebrow">Paper Wallet</div>
        <div className="promo-title">Simulated Funds Only</div>
        <div className="promo-sub">Trade with a risk-free paper bankroll — no real money, ever.</div>
        <Link to="/wallet" className="btn btn-secondary btn-block">
          View Wallet
        </Link>
      </div>
    </div>
  );
}
