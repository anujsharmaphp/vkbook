import { useEffect, useState, type ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuthStore } from "../features/auth/store";
import { useThemeStore } from "../store/theme";
import { fetchWallet } from "../features/wallet/api";
import { useWebSocketTopic } from "../hooks/useWebSocketTopic";
import { formatMinor } from "../utils/money";
import { SunMoonIcon, LogoutIcon } from "../design-system/icons";
import { ToastStack } from "../design-system/ToastStack";

export function AppShell({ children }: { children: ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const theme = useThemeStore((s) => s.theme);
  const toggleTheme = useThemeStore((s) => s.toggleTheme);

  const user = useAuthStore((s) => s.user);
  const accessToken = useAuthStore((s) => s.accessToken);
  const logout = useAuthStore((s) => s.logout);

  const walletQuery = useQuery({
    queryKey: ["wallet"],
    queryFn: fetchWallet,
    enabled: !!accessToken,
  });

  useWebSocketTopic(
    accessToken ? `/ws/user?token=${encodeURIComponent(accessToken)}` : null,
    (message) => {
      if (message.event === "BALANCE_UPDATED") {
        queryClient.invalidateQueries({ queryKey: ["wallet"] });
      }
    },
  );

  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const initials = user?.display_name
    ? user.display_name
        .split(/\s+/)
        .map((part) => part[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "?";

  return (
    <>
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">VK</span>
          <span className="brand-tag">Paper Exchange</span>
        </div>
        <nav className="topnav">
          <Link className={`topnav-item ${location.pathname === "/" ? "active" : ""}`} to="/">
            Home
          </Link>
          <Link className={`topnav-item ${location.pathname === "/wallet" ? "active" : ""}`} to="/wallet">
            Wallet
          </Link>
        </nav>
        <div className="topbar-spacer" />
        <div className="clock mono">{now.toLocaleTimeString()}</div>
        <button
          type="button"
          className="icon-btn"
          title={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
          onClick={toggleTheme}
        >
          <SunMoonIcon width={17} height={17} />
        </button>
        <div className="balance-chip">
          <div>
            <div className="label">Available</div>
            <div className="value mono">
              {walletQuery.data ? formatMinor(walletQuery.data.available_minor) : "—"}
            </div>
          </div>
        </div>
        <button type="button" className="icon-btn" title="Log out" onClick={handleLogout}>
          <LogoutIcon width={17} height={17} />
        </button>
        <div className="avatar-btn" title={user?.email}>
          {initials}
        </div>
      </header>
      <div className="page-body">{children}</div>
      <ToastStack />
    </>
  );
}
