import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserRead } from "../../types/api";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserRead | null;
  setSession: (tokens: { access_token: string; refresh_token: string }) => void;
  setAccessToken: (accessToken: string) => void;
  setUser: (user: UserRead | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setSession: (tokens) =>
        set({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token }),
      setAccessToken: (accessToken) => set({ accessToken }),
      setUser: (user) => set({ user }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: "chalkline-auth" },
  ),
);
