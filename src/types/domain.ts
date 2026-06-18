import type { User } from "@/types/auth";

export type DateString = string;
export type DateTimeString = string;

export interface Movie {
  id: number;
  title: string;
  genre: string;
  language: string;
  format: string;
  release_date: DateString;
  running_days: number;
  poster_url?: string | null;
  poster_source_type?: string | null;
  description?: string | null;
  duration: number;
  rating?: number | null;
  poster_uploaded_at?: DateTimeString | null;
  is_deleted: boolean;
  deleted_at?: DateTimeString | null;
}

export type MovieCreate = Omit<Movie, "id" | "poster_uploaded_at" | "is_deleted" | "deleted_at">;

export type MovieUpdate = Partial<MovieCreate>;

export interface Theatre {
  id: number;
  name: string;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  timezone: string;
  contact_info?: string | null;
  description?: string | null;
  banner_image_url?: string | null;
  is_active: boolean;
  screens: Screen[];
  created_at: DateTimeString;
  updated_at: DateTimeString;
}

export interface Screen {
  id: number;
  theatre_id: number;
  name: string;
  screen_type: string;
  total_seats: number;
  seat_layout_json?: string | null;
  is_active: boolean;
  created_at: DateTimeString;
  updated_at: DateTimeString;
}

export interface Show {
  id: number;
  movie_id: number;
  screen_id: number;
  start_time: string;
  end_time: string;
  date: DateString;
  price_multiplier: number;
  movie?: Movie | null;
  screen?: Screen | null;
}

export interface BookedSeat {
  id: number;
  booking_id: number;
  seat_name: string;
  category: string;
  show_id?: number | null;
}

export interface Booking {
  id: number;
  user_id: number;
  movie_id: number;
  show_id?: number | null;
  total_amount: number;
  booking_date: DateTimeString;
  status: string;
  booked_seats: BookedSeat[];
  movie: Movie;
  show?: Show | null;
}

export interface ReservationGroup {
  id: number;
  user_id: number;
  show_id: number;
  reservation_token: string;
  reserved_at: DateTimeString;
  expires_at: DateTimeString;
  status: string;
  created_at: DateTimeString;
  reserved_seats: SeatReservation[];
}

export interface SeatReservation {
  id: number;
  seat_id: string;
  show_id: number;
  status: string;
  created_at: DateTimeString;
}

export interface Review {
  id: number;
  user_id: number;
  movie_id: number;
  rating: number;
  comment: string;
  created_at: DateTimeString;
  user?: User | null;
}

export interface PriceCalculation {
  base_price: number;
  applied_rules: unknown[];
  final_price: number;
}

export interface SeatDefinition {
  id?: number;
  seat_code: string;
  row_label: string;
  seat_number: number;
  seat_type: string;
  category: string;
  position_x: number;
  position_y: number;
  is_active: boolean;
}

export interface TheatreLayout {
  id: number;
  theatre_id: number;
  screen_id: number;
  layout_name: string;
  layout_type: string;
  total_seats: number;
  rows: number;
  cols: number;
  is_published: boolean;
  seats: SeatDefinition[];
  created_at: DateTimeString;
  updated_at: DateTimeString;
}

export interface MediaAsset {
  id: number;
  filename: string;
  storage_provider: string;
  storage_key?: string | null;
  public_url?: string | null;
  mime_type: string;
  size_bytes: number;
  asset_type: string;
  thumbnail_url?: string | null;
  medium_url?: string | null;
  source_type: string;
  original_source_url?: string | null;
  created_at: DateTimeString;
}
