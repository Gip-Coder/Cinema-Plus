import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

interface JwtClaims {
  sub?: string;
  role?: string;
  exp?: number;
}

// Role hierarchy: higher index = higher privilege
const ADMIN_ROLES = ["staff", "theatre_manager", "admin", "super_admin"] as const;
type AdminRole = (typeof ADMIN_ROLES)[number];

function decodeJwt(token: string): JwtClaims | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = parts[1];
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
    const decoded = atob(padded);
    return JSON.parse(decoded) as JwtClaims;
  } catch {
    return null;
  }
}

function isTokenExpired(claims: JwtClaims): boolean {
  if (!claims.exp) return false;
  return claims.exp * 1000 <= Date.now();
}

function hasAdminAccess(role: string | undefined): boolean {
  return ADMIN_ROLES.includes(role as AdminRole);
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("access_token")?.value;

  let isAuthenticated = false;
  let userRole: string | undefined;

  if (token) {
    const claims = decodeJwt(token);
    if (claims && !isTokenExpired(claims)) {
      isAuthenticated = true;
      userRole = claims.role;
    }
  }

  // Define route protection match rules
  const isAdminRoute = pathname.startsWith("/admin");
  const isProtectedRoute = pathname.startsWith("/bookings") || pathname.startsWith("/profile") || pathname.startsWith("/checkout");
  const isAuthRoute = pathname.startsWith("/login") || pathname.startsWith("/register");

  // 1. Unauthenticated users trying to access protected routes -> redirect to login
  if ((isAdminRoute || isProtectedRoute) && !isAuthenticated) {
    const loginUrl = new URL("/login", request.url);
    // Remember redirection target
    loginUrl.searchParams.set("from", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // 2. Non-admin users trying to access admin routes -> redirect to homepage
  if (isAdminRoute && isAuthenticated && !hasAdminAccess(userRole)) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  // 3. Authenticated users trying to access auth pages (login/register) -> redirect appropriately
  if (isAuthRoute && isAuthenticated) {
    const destination = hasAdminAccess(userRole) ? "/admin" : "/";
    return NextResponse.redirect(new URL(destination, request.url));
  }

  return NextResponse.next();
}

// Config to specify which paths the middleware should apply to
export const config = {
  matcher: [
    "/admin/:path*",
    "/bookings/:path*",
    "/profile/:path*",
    "/checkout/:path*",
    "/login",
    "/register",
  ],
};
