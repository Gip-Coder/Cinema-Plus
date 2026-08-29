import { apiClient } from "@/lib/api/client";
import { apiRoutes } from "@/lib/api/routes";
import type {
  AdminStats,
  AuditLog,
  SystemHealth,
  BookingTrendPoint,
  Movie,
  PricingRule,
  PricingRuleCreate,
  PricingRuleUpdate,
  RevenueChartPoint,
  Screen,
  ScreenCreate,
  ScreenUpdate,
  SeatPricing,
  SeatPricingUpdate,
  Show,
  ShowCreate,
  Theatre,
  TheatreCreate,
  TheatreUpdate,
  SeatDefinition,
  TheatreLayout,
  LayoutTemplate,
  LayoutStats,
  LayoutSavePayload,
} from "@/types/admin";

// ─── Stats & Charts ─────────────────────────────────────────────────────────
export function getStats(token: string) {
  return apiClient.get<AdminStats>(apiRoutes.admin.stats, { token });
}

export function getRevenueChart(token: string) {
  return apiClient.get<RevenueChartPoint[]>(apiRoutes.admin.revenueChart, { token });
}

export function getBookingTrends(token: string) {
  return apiClient.get<BookingTrendPoint[]>(apiRoutes.admin.bookingTrends, { token });
}

import { Booking } from "@/types/domain";

// ─── Bookings ───────────────────────────────────────────────────────────────
export function getBookings(token: string, skip = 0, limit = 100) {
  return apiClient.get<Booking[]>(apiRoutes.admin.bookings, {
    token,
    query: { skip, limit },
  });
}

export function cancelBooking(token: string, bookingId: number) {
  return apiClient.put<void>(apiRoutes.admin.cancelBooking(bookingId), undefined, { token });
}

export function deleteBooking(token: string, bookingId: number) {
  return apiClient.delete<void>(apiRoutes.admin.booking(bookingId), { token });
}

// ─── Theatres ───────────────────────────────────────────────────────────────
export function getTheatres(token: string) {
  return apiClient.get<Theatre[]>(apiRoutes.admin.theatres, { token });
}

export function createTheatre(token: string, payload: TheatreCreate) {
  return apiClient.post<Theatre, TheatreCreate>(apiRoutes.admin.theatres, payload, { token });
}

export function updateTheatre(token: string, id: number, payload: TheatreUpdate) {
  return apiClient.put<Theatre, TheatreUpdate>(apiRoutes.admin.theatre(id), payload, { token });
}

export function deleteTheatre(token: string, id: number) {
  return apiClient.delete<void>(apiRoutes.admin.theatre(id), { token });
}

// ─── Screens ────────────────────────────────────────────────────────────────
export function getScreens(token: string) {
  return apiClient.get<Screen[]>(apiRoutes.admin.screens, { token });
}

export function createScreen(token: string, payload: ScreenCreate) {
  return apiClient.post<Screen, ScreenCreate>(apiRoutes.admin.screens, payload, { token });
}

export function updateScreen(token: string, id: number, payload: ScreenUpdate) {
  return apiClient.put<Screen, ScreenUpdate>(apiRoutes.admin.screen(id), payload, { token });
}

// ─── Pricing ────────────────────────────────────────────────────────────────
export function getPricing(token: string) {
  return apiClient.get<SeatPricing[]>(apiRoutes.admin.pricing, { token });
}

export function updatePricing(
  token: string,
  id: number,
  payload: SeatPricingUpdate,
  adminOverride = false,
) {
  const headers: Record<string, string> = {};
  if (adminOverride) {
    headers["X-Admin-Override"] = "true";
  }
  return apiClient.put<SeatPricing, SeatPricingUpdate>(apiRoutes.admin.pricingById(id), payload, {
    token,
    headers,
  });
}

// ─── Pricing Rules ──────────────────────────────────────────────────────────
export function createPricingRule(token: string, payload: PricingRuleCreate) {
  return apiClient.post<PricingRule, PricingRuleCreate>(apiRoutes.admin.pricingRules, payload, {
    token,
  });
}

export function updatePricingRule(token: string, id: number, payload: PricingRuleUpdate) {
  return apiClient.put<PricingRule, PricingRuleUpdate>(apiRoutes.admin.pricingRule(id), payload, {
    token,
  });
}

// ─── Movies (admin listing via public API) ──────────────────────────────────
export function getMovies(token: string) {
  return apiClient.get<Movie[]>(apiRoutes.movies.list, { token });
}

// ─── Shows (via schedule API) ───────────────────────────────────────────────
export function getShows(token: string) {
  return apiClient.get<Show[]>(apiRoutes.schedule.allShows, { token });
}

export function createShow(token: string, payload: ShowCreate) {
  return apiClient.post<Show, ShowCreate>(apiRoutes.schedule.shows, payload, { token });
}

export function deleteShow(token: string, showId: number) {
  return apiClient.delete<void>(apiRoutes.schedule.deleteShow(showId), { token });
}

// ─── System Health & Audit ──────────────────────────────────────────────────
export function getAuditLogs(token: string, skip = 0, limit = 100) {
  return apiClient.get<AuditLog[]>(apiRoutes.admin.audit, {
    token,
    query: { skip, limit },
  });
}

export function getSystemHealth(token: string) {
  return apiClient.get<SystemHealth>(apiRoutes.admin.health, { token });
}

// ─── Movies CRUD ────────────────────────────────────────────────────────────
export function createMovie(token: string, payload: Omit<Movie, "id" | "created_at">) {
  return apiClient.post<Movie, Omit<Movie, "id" | "created_at">>("/api/movies/", payload, { token });
}

export function updateMovie(token: string, id: number, payload: Partial<Movie>) {
  return apiClient.put<Movie, Partial<Movie>>(`/api/movies/${id}`, payload, { token });
}

export function deleteMovie(token: string, id: number) {
  return apiClient.delete<void>(`/api/movies/${id}`, { token });
}

export function uploadMoviePoster(token: string, formData: FormData) {
  return apiClient.post<{ poster_url: string }, FormData>("/api/movies/upload-poster", formData, { token });
}

// ─── Layout Designer ────────────────────────────────────────────────────────
export function getLayoutTemplates(token: string) {
  return apiClient.get<LayoutTemplate[]>(apiRoutes.layouts.templates, { token });
}

export function previewLayout(
  token: string,
  payload: { total_seats: number; template: string; custom_cols?: number }
) {
  return apiClient.post<{ seats: SeatDefinition[]; rows: number; cols: number; total_seats: number; template: string }>(
    apiRoutes.layouts.generate,
    payload,
    { token }
  );
}

export function validateLayout(
  token: string,
  payload: { seats: SeatDefinition[]; rows: number; cols: number }
) {
  return apiClient.post<{ is_valid: boolean; errors: string[]; stats: LayoutStats }, { seats: SeatDefinition[]; rows: number; cols: number }>("/api/layouts/validate", payload, { token });
}

export function saveLayout(token: string, payload: LayoutSavePayload) {
  return apiClient.post<TheatreLayout, LayoutSavePayload>(apiRoutes.layouts.save, payload, { token });
}

export function getLayoutForScreen(token: string, screenId: number) {
  return apiClient.get<TheatreLayout | null>(apiRoutes.layouts.screen(screenId), { token });
}

export function getAllLayoutsForScreen(token: string, screenId: number) {
  return apiClient.get<TheatreLayout[]>(apiRoutes.layouts.screenAll(screenId), { token });
}

export function getLayoutById(token: string, layoutId: number) {
  return apiClient.get<TheatreLayout>(apiRoutes.layouts.detail(layoutId), { token });
}

export function publishLayout(token: string, layoutId: number) {
  return apiClient.put<TheatreLayout, undefined>(apiRoutes.layouts.publish(layoutId), undefined, { token });
}

export function createLayoutVersion(token: string, layoutId: number, payload?: { layout_name?: string }) {
  return apiClient.post<TheatreLayout, { layout_name?: string }>(apiRoutes.layouts.version(layoutId), payload ?? {}, { token });
}

export function rollbackLayoutVersion(token: string, screenId: number, payload: { version: number }) {
  return apiClient.post<TheatreLayout, { version: number }>(apiRoutes.layouts.rollback(screenId), payload, { token });
}

export function updateLayoutSeats(
  token: string,
  layoutId: number,
  payload: { seats: SeatDefinition[]; rows: number; cols: number }
) {
  return apiClient.put<TheatreLayout, { seats: SeatDefinition[]; rows: number; cols: number }>(apiRoutes.layouts.seats(layoutId), payload, { token });
}

export function getLayoutStats(token: string, layoutId: number) {
  return apiClient.get<LayoutStats>(apiRoutes.layouts.stats(layoutId), { token });
}

export function deleteLayout(token: string, layoutId: number) {
  return apiClient.delete<void>(apiRoutes.layouts.detail(layoutId), { token });
}
