import { apiClient } from "@/lib/api/client";
import { apiRoutes } from "@/lib/api/routes";
import type { AuthToken, LoginRequest, RegisterRequest, User } from "@/types/auth";

export const authApi = {
  login(credentials: LoginRequest) {
    return apiClient.post<AuthToken, LoginRequest>(apiRoutes.auth.login, credentials);
  },
  register(payload: RegisterRequest) {
    return apiClient.post<User, RegisterRequest>(apiRoutes.auth.register, payload);
  },
  me(token: string) {
    return apiClient.get<User>(apiRoutes.auth.me, { token });
  },
  updateProfile(token: string, payload: Partial<Pick<User, "email" | "username">>) {
    return apiClient.put<User>(apiRoutes.auth.profile, undefined, {
      query: payload,
      token,
    });
  },
  changePassword(token: string, oldPassword: string, newPassword: string) {
    return apiClient.put<null>(apiRoutes.auth.changePassword, undefined, {
      query: {
        old_password: oldPassword,
        new_password: newPassword,
      },
      token,
    });
  },
};
