export type UserRole = "admin" | "theatre_manager" | "staff" | "customer" | string;

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest extends LoginRequest {
  email: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface JwtClaims {
  sub?: string;
  username?: string;
  role?: UserRole;
  exp?: number;
  iat?: number;
}
