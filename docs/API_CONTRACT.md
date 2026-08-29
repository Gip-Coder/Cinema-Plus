# Cinema Plus API Contract

Generated from the existing FastAPI routers for the Phase 3.5 Next.js foundation.

## Base URL

- Local default: `http://localhost:8001`
- Next.js env: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8001`

## Response Envelope

Most JSON endpoints return:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

Notes:

- `DELETE /api/movies/{movie_id}` returns `204 No Content`.
- `GET /api/tickets/ticket/{booking_id}/pdf` returns a PDF file response.
- Validation errors return FastAPI error payloads with `detail` and may include `errors`.
- Authenticated endpoints require `Authorization: Bearer <access_token>`.

## Root and Health

| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| `GET` | `/` | No | None | `{ message: string }` |
| `GET` | `/health` | No | None | Health status object |

## Authentication

| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| `POST` | `/api/auth/register` | No | `UserCreate` JSON | `UserResponse` |
| `POST` | `/api/auth/login` | No | `LoginRequest` JSON | `Token` |
| `GET` | `/api/auth/me` | User | None | `UserResponse` |
| `PUT` | `/api/auth/profile` | User | Query: `username?`, `email?` | `UserResponse` |
| `PUT` | `/api/auth/change-password` | User | Query: `old_password`, `new_password` | Empty envelope |

```ts
interface LoginRequest {
  username: string;
  password: string;
}

interface UserCreate extends LoginRequest {
  email: string;
}

interface Token {
  access_token: string;
  token_type: string;
}

interface UserResponse {
  id: number;
  username: string;
  email: string;
  role: string;
}
```

## Movies

| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| `GET` | `/api/movies/` | No | Query: `skip=0`, `limit=100` | `MovieResponse[]` |
| `GET` | `/api/movies/search` | No | Query: `q?`, `genre?`, `language?`, `skip=0`, `limit=100` | `MovieResponse[]` |
| `GET` | `/api/movies/{movie_id}` | No | Path: `movie_id` | `MovieResponse` |
| `POST` | `/api/movies/upload-poster` | Admin | Multipart `file` or JSON/Form `image_url`/`poster_url` | `{ poster_url: string }` |
| `POST` | `/api/movies/` | Admin | `MovieCreate` JSON | `MovieResponse` |
| `PUT` | `/api/movies/{movie_id}` | Admin | `MovieUpdate` JSON | `MovieResponse` |
| `DELETE` | `/api/movies/{movie_id}` | Admin | Path: `movie_id` | `204 No Content` |

```ts
interface MovieBase {
  title: string;
  genre: string;
  language: string;
  format: string;
  release_date: string;
  running_days: number;
  poster_url?: string | null;
  poster_source_type?: string | null;
  description?: string | null;
  duration: number;
  rating?: number | null;
}

interface MovieResponse extends MovieBase {
  id: number;
  poster_uploaded_at?: string | null;
  is_deleted: boolean;
  deleted_at?: string | null;
}
```

## Bookings and Tickets

| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| `GET` | `/api/bookings/seats/{show_id}` | No | Path: `show_id` | Seat status map |
| `POST` | `/api/bookings/book` | User | `BookingCreate` JSON | `BookingResponse` |
| `GET` | `/api/bookings/user/bookings` | User | None | `BookingResponse[]` |
| `GET` | `/api/bookings/price-calculation` | No | Query: `show_id`, `category` | Price calculation object |
| `GET` | `/api/tickets/ticket/{booking_id}/pdf` | User | Path: `booking_id` | PDF blob |

```ts
interface BookedSeatCreate {
  seat_name: string;
  category: string;
  show_id?: number | null;
}

interface BookingCreate {
  movie_id: number;
  show_id?: number | null;
  total_amount: number;
  seats: BookedSeatCreate[];
}
```

## Schedule

| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| `POST` | `/api/schedule/theatres` | Admin | `TheatreBase` JSON | `TheatreResponse` |
| `GET` | `/api/schedule/theatres` | No | None | `TheatreResponse[]` |
| `POST` | `/api/schedule/screens` | Admin | Query: `theatre_id`; body: `ScreenBase` | `ScreenResponse` |
| `GET` | `/api/schedule/screens` | No | None | `ScreenResponse[]` |
| `POST` | `/api/schedule/shows` | Admin | `ShowCreate` JSON | `ShowResponse` |
| `GET` | `/api/schedule/shows/{movie_id}` | No | Path: `movie_id` | `ShowResponse[]` |
| `GET` | `/api/schedule/shows/all/` | No | None | `ShowResponse[]` |
| `GET` | `/api/schedule/shows/show/{show_id}` | No | Path: `show_id` | `ShowResponse` |
| `DELETE` | `/api/schedule/shows/{show_id}` | Admin | Path: `show_id` | Empty envelope |

## Reservations

| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| `POST` | `/api/reservations` | User | `ReservationCreate` JSON | `ReservationGroupResponse` |
| `GET` | `/api/reservations/{group_id}` | User/Admin owner check | Path: `group_id` | `ReservationGroupResponse` |
| `DELETE` | `/api/reservations/{group_id}` | User | Path: `group_id` | Empty envelope |
| `POST` | `/api/reservations/{group_id}/confirm` | User | Path: `group_id` | `BookingResponse` |
| `GET` | `/api/shows/{show_id}/seat-status` | No | Path: `show_id` | Seat status map |
| `GET` | `/api/admin/shows/{show_id}/stats` | Admin | Path: `show_id` | Show statistics object |

```ts
interface ReservationCreate {
  show_id: number;
  seats: string[];
}
```

## Reviews

| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| `POST` | `/api/reviews/` | User | `ReviewCreate` JSON | `ReviewResponse` |
| `GET` | `/api/reviews/movie/{movie_id}` | No | Path: `movie_id` | `ReviewResponse[]` |
| `GET` | `/api/reviews/all` | Admin | None | `ReviewResponse[]` |
| `DELETE` | `/api/reviews/{review_id}` | Admin | Path: `review_id` | Empty envelope |

```ts
interface ReviewCreate {
  movie_id: number;
  rating: number;
  comment: string;
}
```

## Admin

Role dependencies in the backend allow broader staff/theatre manager access for selected theatre, screen, pricing, and media operations.

| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| `GET` | `/api/admin/theatres` | Admin/Theatre Manager/Staff | None | `TheatreResponse[]` |
| `POST` | `/api/admin/theatres` | Admin/Theatre Manager | `TheatreCreate` JSON | `TheatreResponse` |
| `PUT` | `/api/admin/theatres/{theatre_id}` | Admin/Theatre Manager | `TheatreUpdate` JSON | `TheatreResponse` |
| `DELETE` | `/api/admin/theatres/{theatre_id}` | Admin | Path: `theatre_id` | Empty envelope |
| `GET` | `/api/admin/screens` | Admin/Theatre Manager/Staff | None | `ScreenResponse[]` |
| `POST` | `/api/admin/screens` | Admin/Theatre Manager | `ScreenCreate` JSON | `ScreenResponse` |
| `PUT` | `/api/admin/screens/{screen_id}` | Admin/Theatre Manager | `ScreenUpdate` JSON | `ScreenResponse` |
| `GET` | `/api/admin/pricing` | Admin/Theatre Manager/Staff | None | `SeatPricingResponse[]` |
| `PUT` | `/api/admin/pricing/{pricing_id}` | Admin/Theatre Manager | `SeatPricingUpdate` JSON; header `X-Admin-Override?` | `SeatPricingResponse` |
| `POST` | `/api/admin/pricing/rules` | Admin/Theatre Manager | `PricingRuleCreate` JSON | `PricingRuleResponse` |
| `PUT` | `/api/admin/pricing/rules/{rule_id}` | Admin/Theatre Manager | `PricingRuleUpdate` JSON | `PricingRuleResponse` |
| `GET` | `/api/admin/stats` | Admin | None | Stats object |
| `GET` | `/api/admin/revenue-chart` | Admin | None | Revenue chart object |
| `GET` | `/api/admin/booking-trends` | Admin | None | Booking trends object |
| `GET` | `/api/admin/bookings` | Admin | Query: `skip=0`, `limit=100` | `BookingResponse[]` |
| `PUT` | `/api/admin/bookings/{booking_id}/cancel` | Admin | Path: `booking_id` | Empty envelope |
| `DELETE` | `/api/admin/bookings/{booking_id}` | Admin | Path: `booking_id` | Empty envelope |

## Layouts

| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| `POST` | `/api/layouts/generate` | Admin | `LayoutGenerateRequest` JSON | Layout preview object |
| `POST` | `/api/layouts/save` | Admin | `LayoutSaveRequest` JSON | `TheatreLayoutResponse` |
| `GET` | `/api/layouts/screen/{screen_id}` | No | Path: `screen_id` | `TheatreLayoutResponse \| null` |
| `GET` | `/api/layouts/screen/{screen_id}/all` | Admin | Path: `screen_id` | `TheatreLayoutResponse[]` |
| `GET` | `/api/layouts/{layout_id}` | Admin | Path: `layout_id` | `TheatreLayoutResponse` |
| `PUT` | `/api/layouts/{layout_id}/publish` | Admin | Path: `layout_id` | `TheatreLayoutResponse` |
| `PUT` | `/api/layouts/{layout_id}/seats` | Admin | `LayoutBulkSeatUpdate` JSON | `TheatreLayoutResponse` |
| `GET` | `/api/layouts/{layout_id}/stats` | Admin | Path: `layout_id` | Layout stats object |
| `DELETE` | `/api/layouts/{layout_id}` | Admin | Path: `layout_id` | Empty envelope |
| `GET` | `/api/layouts/templates/list` | Admin | None | Layout template list |

```ts
interface LayoutGenerateRequest {
  total_seats: number;
  template: "STANDARD" | "IMAX" | "VIP" | "RECLINER" | "CUSTOM" | string;
  custom_cols?: number | null;
}

interface SeatDefinitionInput {
  seat_code: string;
  row_label: string;
  seat_number: number;
  seat_type: string;
  category: string;
  position_x: number;
  position_y: number;
  is_active: boolean;
}
```

## Migration Notes

- The new Next.js API client unwraps the standard response envelope by default.
- Keep route strings centralized in `src/lib/api/routes.ts`.
- Keep domain-facing request helpers in `src/lib/api/*`.
- Do not migrate NiceGUI pages until a later phase.
