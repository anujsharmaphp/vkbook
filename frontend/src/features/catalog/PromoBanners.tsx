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
    <div className="promo-stack">
      <div
        className="promo-hero"
        style={{ backgroundImage: "url(/promo-cricket.png)" }}
      >
        <button type="button" className="btn promo-hero-btn" onClick={onBrowseLive}>
          Bet Live
        </button>
      </div>

      <div className="promo-banners">
        <div className="promo-card accent-lay">
          <div className="promo-eyebrow">Multi-Sport</div>
          <div className="promo-title">Football, Tennis &amp; More</div>
          <div className="promo-sub">Back or lay across every market on the exchange, all in one book.</div>
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
    </div>
  );
}
