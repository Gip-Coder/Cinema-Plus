"use client";

import { useAuthStore } from "@/stores/auth-store";

export function useAuth() {
  return useAuthStore((state) => ({
    accessToken: state.accessToken,
    isAuthenticated: state.isAuthenticated,
    isHydrated: state.isHydrated,
    role: state.role,
    user: state.user,
    login: state.login,
    logout: state.logout,
    setUser: state.setUser,
  }));
}
