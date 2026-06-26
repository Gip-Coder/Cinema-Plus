"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import { decodeJwt, isTokenExpired } from "@/lib/auth-token";
import type { AuthToken, User, UserRole } from "@/types/auth";

interface AuthState {
  accessToken: string | null;
  isAuthenticated: boolean;
  isHydrated: boolean;
  role: UserRole | null;
  tokenType: string | null;
  user: User | null;
  login: (token: AuthToken, user?: User | null) => void;
  logout: () => void;
  setHydrated: (isHydrated: boolean) => void;
  setUser: (user: User | null) => void;
}

function getRoleFromToken(token: string): UserRole | null {
  return decodeJwt(token)?.role ?? null;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      isAuthenticated: false,
      isHydrated: false,
      role: null,
      tokenType: null,
      user: null,
      login: (token, user = null) => {
        const expired = isTokenExpired(token.access_token);

        if (!expired && typeof window !== "undefined") {
          document.cookie = `access_token=${token.access_token}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
        }

        set({
          accessToken: expired ? null : token.access_token,
          isAuthenticated: !expired,
          role: expired ? null : user?.role ?? getRoleFromToken(token.access_token),
          tokenType: expired ? null : token.token_type,
          user: expired ? null : user,
        });
      },
      logout: () => {
        if (typeof window !== "undefined") {
          document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
        }
        set({
          accessToken: null,
          isAuthenticated: false,
          role: null,
          tokenType: null,
          user: null,
        });
      },
      setHydrated: (isHydrated) => set({ isHydrated }),
      setUser: (user) =>
        set((state) => ({
          role: user?.role ?? state.role,
          user,
        })),
    }),
    {
      name: "cinema-plus-auth",
      onRehydrateStorage: () => (state) => {
        if (!state) {
          return;
        }

        if (state.accessToken && isTokenExpired(state.accessToken)) {
          state.logout();
        }

        state.setHydrated(true);
      },
      partialize: (state) => ({
        accessToken: state.accessToken,
        isAuthenticated: state.isAuthenticated,
        role: state.role,
        tokenType: state.tokenType,
        user: state.user,
      }),
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
