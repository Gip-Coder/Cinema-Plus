export const queryKeys = {
  auth: {
    me: ["auth", "me"] as const,
  },
  movies: {
    all: ["movies"] as const,
    detail: (movieId: number) => ["movies", movieId] as const,
    search: (filters: Record<string, unknown>) => ["movies", "search", filters] as const,
  },
  bookings: {
    user: ["bookings", "user"] as const,
    seats: (showId: number) => ["bookings", "seats", showId] as const,
  },
  reservations: {
    detail: (groupId: number) => ["reservations", groupId] as const,
    seatStatus: (showId: number) => ["reservations", "seat-status", showId] as const,
  },
  schedule: {
    showsByMovie: (movieId: number) => ["schedule", "shows", movieId] as const,
    theatres: ["schedule", "theatres"] as const,
  },
} as const;
