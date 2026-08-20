import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../features/auth/store";

export function AuthLayout() {
  const accessToken = useAuthStore((s) => s.accessToken);
  if (accessToken) return <Navigate to="/" replace />;

  return (
    <div className="auth-shell">
      <Outlet />
    </div>
  );
}
