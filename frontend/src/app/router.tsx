import { Navigate, type RouteObject } from "react-router-dom";

import { AuthLayout } from "../layouts/AuthLayout";
import { ProtectedLayout } from "../layouts/ProtectedLayout";
import { LoginPage } from "../pages/LoginPage";
import { RegisterPage } from "../pages/RegisterPage";
import { HomePage } from "../pages/HomePage";
import { EventPage } from "../pages/EventPage";
import { WalletPage } from "../pages/WalletPage";

export const router: RouteObject[] = [
  {
    element: <AuthLayout />,
    children: [
      { path: "/login", element: <LoginPage /> },
      { path: "/register", element: <RegisterPage /> },
    ],
  },
  {
    element: <ProtectedLayout />,
    children: [
      { path: "/", element: <HomePage /> },
      { path: "/events/:eventId", element: <EventPage /> },
      { path: "/wallet", element: <WalletPage /> },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
];
