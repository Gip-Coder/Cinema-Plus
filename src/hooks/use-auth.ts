"use client";

import { useShallow } from "zustand/react/shallow";
import { useAuthStore } from "@/stores/auth-store";

export function useAuth() {
  return useAuthStore(
    useShallow((state) => ({
      accessToken: state.accessToken,
      isAuthenticated: state.isAuthenticated,
      isHydrated: state.isHydrated,
      role: state.role,
      user: state.user,
      login: state.login,
      logout: state.logout,
      setUser: state.setUser,
    }))
  );
}
