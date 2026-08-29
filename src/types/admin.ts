// ─── Theatre ────────────────────────────────────────────────────────────────
export interface Theatre {
  id: number;
  name: string;
  address: string | null;
  city: string | null;
  state: string | null;
  timezone: string;
  contact_info: string | null;
  description: string | null;
  banner_image_url: string | null;
  is_active: boolean;
  screens: Screen[];
  created_at: string;
  updated_at: string;
}

export interface TheatreCreate {
  name: string;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  timezone?: string;
  contact_info?: string | null;
  description?: string | null;
  banner_image_url?: string | null;
  is_active?: boolean;
}

export type TheatreUpdate = Partial<TheatreCreate>;

// ─── Screen ─────────────────────────────────────────────────────────────────
export interface Screen {
  id: number;
  theatre_id: number;
  name: string;
  screen_type: string;
  total_seats: number;
  seat_layout_json: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ScreenCreate {
  theatre_id: number;
  name: string;
  screen_type?: string;
  total_seats?: number;
  seat_layout_json?: string | null;
  is_active?: boolean;
}

export type ScreenUpdate = Partial<Omit<ScreenCreate, "theatre_id">>;

// ─── Shows ──────────────────────────────────────────────────────────────────
export interface Movie {
  id: number;
  title: string;
  description: string | null;
  duration: number;
  duration_minutes?: number;
  genre: string | null;
  language: string;
  rating: number | null;
  format: string;
  poster_url: string | null;
  status: string;
  release_date: string | null;
  created_at: string;
}

export interface Show {
  id: number;
  movie_id: number;
  screen_id: number;
  start_time: string;
  end_time: string;
  date: string;
  price_multiplier: number;
  movie: Movie | null;
  screen: Screen | null;
}

export interface ShowCreate {
  movie_id: number;
  screen_id: number;
  start_time: string;
  end_time: string;
  date: string;
  price_multiplier?: number;
}

// ─── Seat Pricing ───────────────────────────────────────────────────────────
export interface SeatPricing {
  id: number;
  theatre_id: number;
  screen_id: number | null;
  seat_category: string;
  base_price: number;
  currency: string;
  created_at: string;
  updated_at: string;
}

export interface SeatPricingUpdate {
  base_price: number;
}

// ─── Pricing Rules ──────────────────────────────────────────────────────────
export interface PricingRule {
  id: number;
  name: string;
  rule_type: string;
  multiplier: number;
  priority: number;
  stackable: boolean;
  valid_from: string | null;
  valid_to: string | null;
  is_active: boolean;
  theatre_id: number | null;
  screen_id: number | null;
  created_at: string;
}

export interface PricingRuleCreate {
  name: string;
  rule_type: string;
  multiplier: number;
  priority?: number;
  stackable?: boolean;
  valid_from?: string | null;
  valid_to?: string | null;
  is_active?: boolean;
  theatre_id?: number | null;
  screen_id?: number | null;
}

export type PricingRuleUpdate = Partial<PricingRuleCreate>;

// ─── Media Assets ───────────────────────────────────────────────────────────
export interface MediaAsset {
  id: number;
  filename: string;
  storage_provider: string;
  storage_key: string | null;
  public_url: string | null;
  mime_type: string;
  size_bytes: number;
  asset_type: string;
  thumbnail_url: string | null;
  medium_url: string | null;
  source_type: string;
  original_source_url: string | null;
  created_at: string;
}

// ─── Admin Stats ────────────────────────────────────────────────────────────
export interface AdminStats {
  total_movies: number;
  total_theatres: number;
  total_screens: number;
  total_shows: number;
  total_bookings: number;
  total_revenue: number;
  total_users: number;
  today_revenue?: number;
  active_reservations?: number;
  most_booked_movie?: string;
  occupancy_percentage?: number;
  [key: string]: number | string | undefined;
}

export interface RevenueChartPoint {
  date: string;
  revenue: number;
}

export interface BookingTrendPoint {
  date: string;
  bookings: number;
}

// ─── Bookings (Admin view) ──────────────────────────────────────────────────
export interface AdminBooking {
  id: number;
  user_id: number;
  show_id: number;
  total_amount: number;
  status: string;
  booking_date: string;
  payment_method: string | null;
  transaction_id: string | null;
  created_at: string;
}

// ─── Audit Log ──────────────────────────────────────────────────────────────
export interface AuditLog {
  id: number;
  user_id: number;
  entity_type: string;
  entity_id: number;
  action: string;
  old_value: string | null;
  new_value: string | null;
  ip_address: string | null;
  timestamp: string;
}

// ─── System Health ──────────────────────────────────────────────────────────
export interface SchedulerTaskStatus {
  status: string;
  detail: string;
}

export interface SystemHealth {
  status: string;
  database: {
    status: string;
    latency_ms: number;
    engine: string;
  };
  cache: {
    status: string;
    scope: string;
  };
  storage: {
    status: string;
    path: string;
    note: string;
  };
  reservation: {
    mechanism: string;
    hold_minutes: number;
  };
  scheduler_tasks: {
    reservation_expiry_cleanup: SchedulerTaskStatus;
    daily_revenue_compiler: SchedulerTaskStatus;
    media_thumbnail_optimizer: SchedulerTaskStatus;
  };
  system: {
    cpu_usage_percent: number;
    memory_usage_percent: number;
    memory_used_gb: number;
    memory_total_gb: number;
    disk_usage_percent: number;
    disk_free_gb: number;
  };
  uptime_seconds: number;
}

// ─── Seating Layout Designer ────────────────────────────────────────────────
export interface SeatDefinition {
  id?: number;
  seat_code: string;
  row_label: string;
  seat_number: number;
  seat_type: string; // standard, wheelchair, couple, blocked, maintenance, emergency
  category: string;  // Normal, Executive, Premium
  position_x: number;
  position_y: number;
  is_active: boolean;
}

export interface TheatreLayout {
  id: number;
  theatre_id: number;
  screen_id: number;
  layout_name: string;
  layout_type: string; // STANDARD, IMAX, VIP, RECLINER, CUSTOM
  total_seats: number;
  rows: number;
  cols: number;
  status: string; // draft, published
  version: number;
  is_published: boolean;
  seats: SeatDefinition[];
  created_at: string;
  updated_at: string;
}

export interface LayoutTemplate {
  name: string;
  description: string;
  default_cols: number;
  max_cols: number;
  min_cols: number;
  has_center_aisle: boolean;
  has_side_aisles: boolean;
}

export interface LayoutStats {
  total_seats: number;
  total_active: number;
  normal: number;
  executive: number;
  premium: number;
  wheelchair: number;
  couple: number;
  blocked: number;
  available_capacity: number;
}

export interface LayoutSavePayload {
  screen_id: number;
  layout_name: string;
  layout_type: string;
  seats: SeatDefinition[];
  rows: number;
  cols: number;
}
