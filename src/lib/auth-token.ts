import type { JwtClaims } from "@/types/auth";

function decodeBase64Url(value: string) {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");

  if (typeof window === "undefined") {
    return Buffer.from(padded, "base64").toString("utf8");
  }

  return window.atob(padded);
}

export function decodeJwt(token: string): JwtClaims | null {
  const [, payload] = token.split(".");
  if (!payload) {
    return null;
  }

  try {
    return JSON.parse(decodeBase64Url(payload)) as JwtClaims;
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string) {
  const claims = decodeJwt(token);
  if (!claims?.exp) {
    return false;
  }

  return claims.exp * 1000 <= Date.now();
}
