"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Film, 
  Calendar, 
  Clock, 
  User, 
  Ticket, 
  Bell, 
  Heart, 
  Compass, 
  ChevronRight, 
  Sparkles, 
  AlertTriangle,
  Award,
  Zap,
  MapPin
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { bookingsApi } from "@/lib/api/bookings";
import { moviesApi } from "@/lib/api/movies";
import { resolveMediaUrl } from "@/lib/api/client";
import type { Booking, Movie } from "@/types/domain";

interface NotificationItem {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

export default function DashboardPage() {
  const { user, accessToken, isAuthenticated, isHydrated } = useAuth();
  const router = useRouter();

  const [bookings, setBookings] = useState<Booking[]>([]);
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Local storage lists
  const [watchlist, setWatchlist] = useState<number[]>([]);
  const [favorites, setFavorites] = useState<number[]>([]);
  const [activeHold, setActiveHold] = useState<{
    showId: number;
    groupId: number;
    expiresAt: string;
    movieTitle: string;
    showTime: string;
  } | null>(null);

  // Notifications state
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  
  // Preferences
  const [prefs, setPrefs] = useState({
    preferredTheatre: "Downtown Luxe Screen 1",
    preferredSeatCategory: "Executive",
    preferredLanguage: "English",
    preferredGenres: ["Action", "Sci-Fi"]
  });

  // Hold Timer remaining
  const [holdTimeLeft, setHoldTimeLeft] = useState<string>("");

  useEffect(() => {
    if (isHydrated && !isAuthenticated) {
      router.push("/login?redirect=/dashboard");
    }
  }, [isAuthenticated, isHydrated, router]);

  // Load Data
  useEffect(() => {
    if (!isAuthenticated || !accessToken) return;

    async function loadData() {
      try {
        const [bookingsData, moviesData] = await Promise.all([
          bookingsApi.userBookings(accessToken as string),
          moviesApi.list(),
        ]);

        setBookings(bookingsData ?? []);
        setMovies(moviesData ?? []);

        // Load preferences & watchlist from local storage
        const savedPrefs = localStorage.getItem("cinema_plus_profile_prefs");
        if (savedPrefs) {
          try {
            setPrefs(JSON.parse(savedPrefs));
          } catch (e) {
            console.error("Failed to parse prefs", e);
          }
        }

        const savedWatchlist = localStorage.getItem("cinema_plus_watchlist");
        if (savedWatchlist) {
          try {
            setWatchlist(JSON.parse(savedWatchlist));
          } catch {}
        }

        const savedFavs = localStorage.getItem("cinema_plus_favorites");
        if (savedFavs) {
          try {
            setFavorites(JSON.parse(savedFavs));
          } catch {}
        }

        // Check active reservations in localStorage
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key && key.startsWith("cinema_plus_active_reservation_")) {
            const val = localStorage.getItem(key);
            if (val) {
              try {
                const parsed = JSON.parse(val);
                const expiry = new Date(parsed.expires_at);
                if (expiry > new Date()) {
                  // Valid active hold!
                  // Find show and movie details
                  const showId = parsed.show_id;
                  const groupId = parsed.id;
                  
                  // Try to find movie title from moviesData
                  const relatedMovie = moviesData?.find(m => m.id === parsed.movie_id) || null;
                  
                  setActiveHold({
                    showId,
                    groupId,
                    expiresAt: parsed.expires_at,
                    movieTitle: relatedMovie?.title || "Reserved Movie",
                    showTime: parsed.reserved_seats?.[0]?.created_at 
                      ? new Date(parsed.reserved_seats[0].created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
                      : "Upcoming Showtime"
                  });
                  break;
                }
              } catch (e) {
                console.error("Error reading cached reservation", e);
              }
            }
          }
        }

        // Generate dynamic mock notifications for booking status or system events
        const customNotifications: NotificationItem[] = [
          {
            id: "notif-1",
            type: "success",
            title: "Welcome to Cinema Plus!",
            message: "Your premium cinema dashboard is now ready. Browse showtimes, view dynamic seat layouts, and enjoy your movies.",
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            read: false,
          }
        ];

        // Add bookings confirmations if user has bookings
        if (bookingsData && bookingsData.length > 0) {
          const latestBooking = bookingsData[0];
          customNotifications.push({
            id: `notif-booking-${latestBooking.id}`,
            type: "success",
            title: "Booking Confirmed",
            message: `Your tickets for "${latestBooking.movie?.title || "Movie"}" are ready. Show this dashboard at entry.`,
            timestamp: latestBooking.booking_date,
            read: false,
          });
        }

        setNotifications(customNotifications);

      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [accessToken, isAuthenticated]);

  // Hold Timer updates
  useEffect(() => {
    if (!activeHold) return;

    const timer = setInterval(() => {
      const remaining = new Date(activeHold.expiresAt).getTime() - Date.now();
      if (remaining <= 0) {
        setActiveHold(null);
        setHoldTimeLeft("");
        clearInterval(timer);
      } else {
        const mins = Math.floor(remaining / 60000);
        const secs = Math.floor((remaining % 60000) / 1000);
        setHoldTimeLeft(`${mins}:${secs < 10 ? "0" : ""}${secs}`);
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [activeHold]);

  const markNotificationRead = (id: string) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
  };

  const clearNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  if (!isHydrated || loading) {
    return (
      <div className="min-h-screen bg-[hsl(222,84%,2.5%)] flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  // Filter bookings
  const upcomingBookings = bookings.filter(b => {
    if (b.status === "cancelled") return false;
    const showDate = b.show?.date ? new Date(b.show.date) : new Date(b.booking_date);
    return showDate >= new Date(new Date().setHours(0,0,0,0));
  });

  // Watchlist Movie info mapping
  const watchlistMovies = movies.filter(m => watchlist.includes(m.id));
  const favoriteMovies = movies.filter(m => favorites.includes(m.id));

  // Personalization recommendations logic:
  // Match genres or rating
  const recommendedMovies = movies
    .filter(m => {
      const matchGenre = prefs.preferredGenres.some(g => m.genre.toLowerCase().includes(g.toLowerCase()));
      const isNotBooked = !bookings.some(b => b.movie_id === m.id);
      return matchGenre && isNotBooked;
    })
    .slice(0, 4);

  return (
    <main className="min-h-screen bg-[hsl(222,84%,2.5%)] text-zinc-100 pb-20">
      {/* Header spotlight */}
      <section className="relative w-full py-12 border-b border-white/[0.04] bg-gradient-to-b from-red-950/10 to-transparent">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              Welcome back, <span className="text-red-500">{user?.username}</span>
            </h1>
            <p className="text-zinc-400 text-xs sm:text-sm font-medium">
              Manage reservations, download digital tickets, and review your movie spotlight recommendations.
            </p>
          </div>

          {/* Loyalty status widget */}
          <div className="flex items-center gap-4 bg-white/[0.02] border border-white/[0.06] rounded-2xl p-4 shadow-xl backdrop-blur-md">
            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center text-white shadow-md">
              <Award className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-extrabold uppercase tracking-widest text-amber-400">Gold Club VIP</span>
                <Sparkles className="h-3.5 w-3.5 text-amber-400 fill-amber-400" />
              </div>
              <p className="text-xl font-black text-white">450 <span className="text-xs font-medium text-zinc-400">Points</span></p>
              <div className="w-32 bg-white/[0.08] h-1.5 rounded-full mt-1.5 overflow-hidden">
                <div className="bg-amber-500 h-full rounded-full" style={{ width: "45%" }} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Grid */}
      <section className="max-w-7xl mx-auto px-6 mt-10 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column (2/3 width) - Bookings & Recommendations */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Active Reservation recovery alert */}
          {activeHold && (
            <div className="rounded-2xl border border-red-500/30 bg-gradient-to-r from-red-950/20 to-zinc-950 p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 shadow-2xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 h-32 w-32 bg-red-600/5 rounded-full filter blur-xl" />
              <div className="flex items-start gap-4">
                <div className="h-10 w-10 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-500 shrink-0 mt-1">
                  <AlertTriangle className="h-5 w-5 animate-pulse" />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-extrabold uppercase tracking-wider text-red-400">Unfinished Hold Detected</span>
                    <span className="h-2 w-2 rounded-full bg-red-500 animate-ping" />
                  </div>
                  <h3 className="font-extrabold text-sm text-white">You have seats held for {activeHold.movieTitle}</h3>
                  <p className="text-xs text-zinc-400 font-medium">
                    Your seats are locked until {new Date(activeHold.expiresAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 w-full sm:w-auto shrink-0">
                <div className="bg-white/[0.03] border border-white/[0.08] px-3.5 py-2 rounded-xl text-center shrink-0">
                  <span className="block text-[9px] uppercase tracking-wider text-zinc-500 font-bold">Expires in</span>
                  <span className="text-sm font-black text-red-500 font-mono">{holdTimeLeft}</span>
                </div>
                <Link
                  href={`/checkout/${activeHold.groupId}`}
                  className="flex-grow sm:flex-grow-0 px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs text-center shadow-lg hover:shadow-red-600/10 transition-all"
                >
                  Resume booking
                </Link>
              </div>
            </div>
          )}

          {/* Upcoming Bookings */}
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-white/[0.04] pb-3">
              <h2 className="font-extrabold text-lg text-white flex items-center gap-2">
                <Ticket className="h-5 w-5 text-red-500" />
                Upcoming Screenings
              </h2>
              <Link href="/bookings" className="text-xs font-bold text-red-400 hover:text-red-300 flex items-center gap-0.5">
                All Bookings
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>

            {upcomingBookings.length === 0 ? (
              <div className="rounded-2xl border border-white/[0.04] bg-white/[0.01] p-12 text-center space-y-4">
                <Film className="mx-auto h-10 w-10 text-zinc-700" />
                <div className="space-y-1">
                  <p className="text-sm font-bold text-zinc-300">No upcoming ticket reservations</p>
                  <p className="text-xs text-zinc-500">Pick a spotlight movie and choose your premium seat layout today!</p>
                </div>
                <Link
                  href="/"
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white/[0.03] border border-white/[0.06] text-xs font-bold text-zinc-300 hover:bg-white/[0.06] hover:text-white transition-colors"
                >
                  Browse Now Showing
                </Link>
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {upcomingBookings.map((booking) => (
                  <div 
                    key={booking.id}
                    className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5 flex gap-4 hover:border-red-500/20 transition-all group"
                  >
                    {/* Poster */}
                    <div className="aspect-[2/3] w-20 rounded-xl bg-zinc-900 border border-white/[0.06] overflow-hidden shrink-0">
                      {booking.movie?.poster_url ? (
                        /* eslint-disable-next-line @next/next/no-img-element */
                        <img src={resolveMediaUrl(booking.movie.poster_url)} alt={booking.movie.title} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-zinc-700">
                          <Film className="h-6 w-6" />
                        </div>
                      )}
                    </div>

                    {/* Meta */}
                    <div className="flex flex-col justify-between flex-grow">
                      <div className="space-y-1">
                        <span className="inline-flex rounded bg-red-500/10 border border-red-500/20 px-1.5 py-0.5 text-[8px] font-bold text-red-400 uppercase">
                          {booking.show?.screen?.name || "Premium Screen"}
                        </span>
                        <h4 className="font-bold text-sm text-zinc-100 group-hover:text-red-400 transition-colors line-clamp-1">
                          {booking.movie?.title}
                        </h4>
                        <div className="space-y-0.5 text-[10px] text-zinc-400 font-semibold">
                          <p className="flex items-center gap-1">
                            <Calendar className="h-3.5 w-3.5 text-zinc-600" />
                            {booking.show?.date ? new Date(booking.show.date).toLocaleDateString("en-US", { weekday: "short", day: "numeric", month: "short" }) : "N/A"}
                          </p>
                          <p className="flex items-center gap-1">
                            <Clock className="h-3.5 w-3.5 text-zinc-600" />
                            {booking.show?.start_time ? booking.show.start_time.slice(0, 5) : "N/A"}
                          </p>
                          <p className="flex items-center gap-1">
                            <MapPin className="h-3.5 w-3.5 text-zinc-600" />
                            {booking.booked_seats?.map(s => s.seat_name).join(", ")}
                          </p>
                        </div>
                      </div>

                      <Link
                        href={`/bookings/${booking.id}`}
                        className="self-start text-[10px] font-bold text-red-400 hover:text-red-300 flex items-center gap-0.5 mt-2"
                      >
                        View Ticket QR & details
                        <ChevronRight className="h-3.5 w-3.5" />
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recommended Movies */}
          <div className="space-y-4">
            <h2 className="font-extrabold text-lg text-white flex items-center gap-2 border-b border-white/[0.04] pb-3">
              <Sparkles className="h-5 w-5 text-red-500" />
              Recommended For You
            </h2>

            {recommendedMovies.length === 0 ? (
              <div className="rounded-2xl border border-white/[0.04] bg-white/[0.01] p-8 text-center text-zinc-500 text-xs">
                Provide preferences in your profile to customize recommendations.
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {recommendedMovies.map((movie) => (
                  <Link 
                    href={`/movies/${movie.id}`} 
                    key={movie.id}
                    className="group space-y-2.5"
                  >
                    <div className="aspect-[2/3] w-full rounded-xl bg-zinc-950 border border-white/[0.06] overflow-hidden relative group-hover:border-red-500/20 transition-all duration-300">
                      {movie.poster_url ? (
                        /* eslint-disable-next-line @next/next/no-img-element */
                        <img src={resolveMediaUrl(movie.poster_url)} alt={movie.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-zinc-700">
                          <Film className="h-8 w-8" />
                        </div>
                      )}
                    </div>
                    <div className="space-y-0.5">
                      <h4 className="font-bold text-xs text-zinc-200 group-hover:text-red-400 transition-colors line-clamp-1">{movie.title}</h4>
                      <p className="text-[9px] text-zinc-500 uppercase font-bold tracking-wider">{movie.genre}</p>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Watchlist & Favorites split */}
          <div className="grid gap-6 md:grid-cols-2">
            
            {/* Watchlist */}
            <div className="space-y-3 bg-white/[0.01] border border-white/[0.04] p-5 rounded-2xl">
              <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                <Compass className="h-4 w-4 text-red-500" />
                My Watchlist ({watchlistMovies.length})
              </h3>
              
              {watchlistMovies.length === 0 ? (
                <p className="text-xs text-zinc-500 py-2">Add movies on detail pages to view them here.</p>
              ) : (
                <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
                  {watchlistMovies.map(movie => (
                    <Link key={movie.id} href={`/movies/${movie.id}`} className="flex items-center gap-3 p-1.5 rounded-lg hover:bg-white/[0.02] transition-colors group">
                      <div className="h-10 w-7 rounded bg-zinc-950 overflow-hidden shrink-0 border border-white/[0.04]">
                        {movie.poster_url && (
                          /* eslint-disable-next-line @next/next/no-img-element */
                          <img src={resolveMediaUrl(movie.poster_url)} alt={movie.title} className="w-full h-full object-cover" />
                        )}
                      </div>
                      <div className="flex-grow min-w-0">
                        <p className="text-xs font-bold text-zinc-200 group-hover:text-red-400 transition-colors truncate">{movie.title}</p>
                        <p className="text-[9px] text-zinc-500 truncate">{movie.genre}</p>
                      </div>
                      <ChevronRight className="h-3.5 w-3.5 text-zinc-600 shrink-0" />
                    </Link>
                  ))}
                </div>
              )}
            </div>

            {/* Favorites */}
            <div className="space-y-3 bg-white/[0.01] border border-white/[0.04] p-5 rounded-2xl">
              <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                <Heart className="h-4 w-4 text-red-500 fill-red-500/20" />
                Favorite Movies ({favoriteMovies.length})
              </h3>

              {favoriteMovies.length === 0 ? (
                <p className="text-xs text-zinc-500 py-2">Heart your absolute favorites to keep them saved.</p>
              ) : (
                <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
                  {favoriteMovies.map(movie => (
                    <Link key={movie.id} href={`/movies/${movie.id}`} className="flex items-center gap-3 p-1.5 rounded-lg hover:bg-white/[0.02] transition-colors group">
                      <div className="h-10 w-7 rounded bg-zinc-950 overflow-hidden shrink-0 border border-white/[0.04]">
                        {movie.poster_url && (
                          /* eslint-disable-next-line @next/next/no-img-element */
                          <img src={resolveMediaUrl(movie.poster_url)} alt={movie.title} className="w-full h-full object-cover" />
                        )}
                      </div>
                      <div className="flex-grow min-w-0">
                        <p className="text-xs font-bold text-zinc-200 group-hover:text-red-400 transition-colors truncate">{movie.title}</p>
                        <p className="text-[9px] text-zinc-500 truncate">{movie.genre}</p>
                      </div>
                      <ChevronRight className="h-3.5 w-3.5 text-zinc-600 shrink-0" />
                    </Link>
                  ))}
                </div>
              )}
            </div>

          </div>

        </div>

        {/* Right Sidebar (1/3 width) - Actions, Notifications, Prefs */}
        <div className="space-y-8">
          
          {/* Quick Actions */}
          <div className="bg-white/[0.02] border border-white/[0.06] p-5 rounded-2xl space-y-4">
            <h3 className="font-extrabold text-sm text-white uppercase tracking-wider">Quick Vault</h3>
            
            <div className="grid grid-cols-1 gap-2.5">
              <Link
                href="/"
                className="flex items-center gap-3 p-3 rounded-xl border border-white/[0.04] bg-white/[0.01] hover:bg-white/[0.04] hover:border-red-500/20 transition-all text-xs font-bold text-zinc-200"
              >
                <Compass className="h-4 w-4 text-red-500" />
                Book Showtime
              </Link>
              <Link
                href="/tickets"
                className="flex items-center gap-3 p-3 rounded-xl border border-white/[0.04] bg-white/[0.01] hover:bg-white/[0.04] hover:border-red-500/20 transition-all text-xs font-bold text-zinc-200"
              >
                <Ticket className="h-4 w-4 text-red-500" />
                Rapid Ticket QR Barcodes
              </Link>
              <Link
                href="/profile"
                className="flex items-center gap-3 p-3 rounded-xl border border-white/[0.04] bg-white/[0.01] hover:bg-white/[0.04] hover:border-red-500/20 transition-all text-xs font-bold text-zinc-200"
              >
                <User className="h-4 w-4 text-red-500" />
                Edit Profile Preferences
              </Link>
            </div>
          </div>

          {/* Notification Center */}
          <div className="bg-white/[0.02] border border-white/[0.06] p-5 rounded-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-extrabold text-sm text-white uppercase tracking-wider flex items-center gap-1.5">
                <Bell className="h-4 w-4 text-red-500" />
                Notification Hub
              </h3>
              {notifications.some(n => !n.read) && (
                <span className="h-2 w-2 rounded-full bg-red-500" />
              )}
            </div>

            {notifications.length === 0 ? (
              <p className="text-xs text-zinc-500 py-4 text-center">No active notifications.</p>
            ) : (
              <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
                {notifications.map(notif => (
                  <div 
                    key={notif.id}
                    className={`p-3 rounded-xl border text-xs space-y-1 transition-all ${
                      notif.read 
                        ? "bg-white/[0.005] border-white/[0.03] text-zinc-400" 
                        : "bg-white/[0.02] border-white/[0.08] text-zinc-200"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className={`font-bold ${notif.read ? "text-zinc-300" : "text-white"}`}>
                        {notif.title}
                      </span>
                      <button 
                        onClick={() => clearNotification(notif.id)}
                        className="text-[10px] text-zinc-600 hover:text-zinc-400"
                      >
                        ✕
                      </button>
                    </div>
                    <p className="text-[11px] text-zinc-400 font-medium">{notif.message}</p>
                    <div className="flex items-center justify-between pt-1 text-[9px] text-zinc-500">
                      <span>{new Date(notif.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      {!notif.read && (
                        <button 
                          onClick={() => markNotificationRead(notif.id)}
                          className="font-bold text-red-400 hover:text-red-300"
                        >
                          Mark read
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* User Preferences Summary */}
          <div className="bg-white/[0.02] border border-white/[0.06] p-5 rounded-2xl space-y-4">
            <h3 className="font-extrabold text-sm text-white uppercase tracking-wider">Spotlight Tastes</h3>
            
            <div className="space-y-3 text-xs">
              <div className="flex justify-between border-b border-white/[0.02] pb-2">
                <span className="text-zinc-500">Primary Theatre:</span>
                <span className="font-bold text-zinc-300">{prefs.preferredTheatre}</span>
              </div>
              <div className="flex justify-between border-b border-white/[0.02] pb-2">
                <span className="text-zinc-500">Seat Category:</span>
                <span className="font-bold text-zinc-300">{prefs.preferredSeatCategory}</span>
              </div>
              <div className="flex justify-between border-b border-white/[0.02] pb-2">
                <span className="text-zinc-500">Language:</span>
                <span className="font-bold text-zinc-300">{prefs.preferredLanguage}</span>
              </div>
              <div className="space-y-1">
                <span className="text-zinc-500 block">Favorite Genres:</span>
                <div className="flex flex-wrap gap-1">
                  {prefs.preferredGenres.map(g => (
                    <span key={g} className="px-2 py-0.5 rounded bg-zinc-800 border border-white/[0.05] text-[10px] text-zinc-400">
                      {g}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Future Ready Modules (Task 13) */}
          <div className="bg-white/[0.01] border border-white/[0.04] p-5 rounded-2xl space-y-3">
            <span className="inline-flex rounded-full bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 text-[8px] font-bold text-amber-400 uppercase tracking-widest">
              Membership perks
            </span>
            <h4 className="font-bold text-sm text-zinc-200">Cinema Plus Rewards</h4>
            <p className="text-xs text-zinc-500 leading-relaxed font-medium">
              Watch for upcoming updates like food ordering, parking reservations, and targeted AI trailers tailored to your preferences.
            </p>
            <div className="flex items-center gap-1.5 text-[10px] font-bold text-red-400">
              <Zap className="h-3.5 w-3.5 fill-red-500/10" />
              <span>Free Popcorn upgrade coming soon</span>
            </div>
          </div>

        </div>

      </section>
    </main>
  );
}
