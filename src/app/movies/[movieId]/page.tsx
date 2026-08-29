"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Film, 
  Calendar, 
  Clock, 
  Star, 
  MapPin, 
  Monitor,
  ChevronLeft,
  Heart,
  Bookmark,
  MessageSquare,
  Trash2,
  Edit,
  Send,
  Loader2,
  AlertCircle
} from "lucide-react";
import { moviesApi } from "@/lib/api/movies";
import { scheduleApi } from "@/lib/api/schedule";
import { reviewsApi } from "@/lib/api/reviews";
import { resolveMediaUrl } from "@/lib/api/client";
import { useAuth } from "@/hooks/use-auth";
import type { Movie, Show, Theatre, Review } from "@/types/domain";

export default function MovieDetailsPage() {
  const { movieId } = useParams();
  const router = useRouter();
  const { user, accessToken, isAuthenticated } = useAuth();

  const [movie, setMovie] = useState<Movie | null>(null);
  const [shows, setShows] = useState<Show[]>([]);
  const [theatres, setTheatres] = useState<Theatre[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected date filter state
  const [selectedDate, setSelectedDate] = useState<string>("");

  // Watchlist & Favorites states
  const [isFavorite, setIsFavorite] = useState(false);
  const [isWatchlist, setIsWatchlist] = useState(false);

  // Add Review form states
  const [reviewRating, setReviewRating] = useState(10);
  const [reviewComment, setReviewComment] = useState("");
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitPending, setIsSubmitPending] = useState(false);

  // Edit Review states
  const [editingReviewId, setEditingReviewId] = useState<number | null>(null);
  const [editRating, setEditRating] = useState(10);
  const [editComment, setEditComment] = useState("");

  // Load Movie, Shows, and Reviews
  const loadMovieAndShows = useCallback(async () => {
    if (!movieId) return;
    try {
      const idNum = Number(movieId);
      const [movieData, showsData, theatresData, reviewsData] = await Promise.all([
        moviesApi.detail(idNum),
        scheduleApi.showsByMovie(idNum),
        scheduleApi.theatres(),
        reviewsApi.byMovie(idNum).catch(() => [] as Review[]),
      ]);

      setMovie(movieData);
      setShows(showsData ?? []);
      setTheatres(theatresData ?? []);
      setReviews(reviewsData ?? []);

      // Pick the first available date as default
      if (showsData && showsData.length > 0) {
        const uniqueDates = Array.from(new Set(showsData.map((s) => s.date))).sort();
        setSelectedDate(uniqueDates[0] || "");
      }
    } catch (err) {
      console.error("Error loading movie detail info:", err);
      setError("Failed to load movie details.");
    } finally {
      setLoading(false);
    }
  }, [movieId]);

  useEffect(() => {
    loadMovieAndShows();
  }, [loadMovieAndShows]);

  // Handle Watchlist, Favorites, and Recently Viewed updates
  useEffect(() => {
    if (!movieId) return;
    const idNum = Number(movieId);

    // Favorites check
    const favs = localStorage.getItem("cinema_plus_favorites");
    if (favs) {
      try {
        const parsed = JSON.parse(favs) as number[];
        setIsFavorite(parsed.includes(idNum));
      } catch {}
    }

    // Watchlist check
    const watch = localStorage.getItem("cinema_plus_watchlist");
    if (watch) {
      try {
        const parsed = JSON.parse(watch) as number[];
        setIsWatchlist(parsed.includes(idNum));
      } catch {}
    }

    // Recently viewed track
    const recent = localStorage.getItem("cinema_plus_recently_viewed");
    let recentList: number[] = [];
    if (recent) {
      try {
        recentList = JSON.parse(recent) as number[];
      } catch {}
    }
    // Remove if already in list, then prepend
    recentList = recentList.filter(id => id !== idNum);
    recentList.unshift(idNum);
    recentList = recentList.slice(0, 10); // Limit to 10
    localStorage.setItem("cinema_plus_recently_viewed", JSON.stringify(recentList));

  }, [movieId]);

  const toggleFavorite = () => {
    if (!movieId) return;
    const idNum = Number(movieId);
    const favs = localStorage.getItem("cinema_plus_favorites");
    let list: number[] = [];
    if (favs) {
      try {
        list = JSON.parse(favs) as number[];
      } catch {}
    }
    
    if (list.includes(idNum)) {
      list = list.filter(id => id !== idNum);
      setIsFavorite(false);
    } else {
      list.push(idNum);
      setIsFavorite(true);
    }
    localStorage.setItem("cinema_plus_favorites", JSON.stringify(list));
  };

  const toggleWatchlist = () => {
    if (!movieId) return;
    const idNum = Number(movieId);
    const watch = localStorage.getItem("cinema_plus_watchlist");
    let list: number[] = [];
    if (watch) {
      try {
        list = JSON.parse(watch) as number[];
      } catch {}
    }

    if (list.includes(idNum)) {
      list = list.filter(id => id !== idNum);
      setIsWatchlist(false);
    } else {
      list.push(idNum);
      setIsWatchlist(true);
    }
    localStorage.setItem("cinema_plus_watchlist", JSON.stringify(list));
  };

  // Submit Review
  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessToken || !movieId) return;
    setSubmitSuccess(null);
    setSubmitError(null);

    if (!reviewComment.trim()) {
      setSubmitError("Review comment is required.");
      return;
    }

    setIsSubmitPending(true);
    try {
      await reviewsApi.create(accessToken, {
        movie_id: Number(movieId),
        rating: reviewRating,
        comment: reviewComment
      });

      setSubmitSuccess("Review submitted successfully!");
      setReviewComment("");
      setReviewRating(10);
      
      // Reload reviews
      const updated = await reviewsApi.byMovie(Number(movieId));
      setReviews(updated ?? []);

    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : "Failed to submit review.");
    } finally {
      setIsSubmitPending(false);
    }
  };

  // Delete Review
  const handleDeleteReview = async (reviewId: number) => {
    if (!accessToken || !movieId) return;
    if (!confirm("Are you sure you want to delete your review?")) return;

    try {
      await reviewsApi.remove(accessToken, reviewId);
      // Reload reviews
      const updated = await reviewsApi.byMovie(Number(movieId));
      setReviews(updated ?? []);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete review.");
    }
  };

  // Edit Review triggers
  const startEditReview = (review: Review) => {
    setEditingReviewId(review.id);
    setEditRating(review.rating);
    setEditComment(review.comment);
  };

  const handleUpdateReview = async (e: React.FormEvent, reviewId: number) => {
    e.preventDefault();
    if (!accessToken || !movieId) return;

    try {
      await reviewsApi.update(accessToken, reviewId, {
        movie_id: Number(movieId),
        rating: editRating,
        comment: editComment
      });

      setEditingReviewId(null);
      // Reload reviews
      const updated = await reviewsApi.byMovie(Number(movieId));
      setReviews(updated ?? []);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to update review.");
    }
  };

  // Extract unique dates that have shows
  const uniqueDates = useMemo(() => {
    return Array.from(new Set(shows.map((s) => s.date))).sort();
  }, [shows]);

  const getTheatreName = useCallback((theatreId: number) => {
    return theatres.find((t) => t.id === theatreId)?.name ?? `Theatre #${theatreId}`;
  }, [theatres]);

  const getTheatreAddress = useCallback((theatreId: number) => {
    const t = theatres.find((t) => t.id === theatreId);
    if (!t) return "";
    return [t.address, t.city].filter(Boolean).join(", ");
  }, [theatres]);

  // Group shows by Theatre and Screen for the selected date
  const groupedShows = useMemo(() => {
    if (!selectedDate) return [];

    const dateShows = shows.filter((s) => s.date === selectedDate);
    const map: Record<number, Record<number, Show[]>> = {};

    dateShows.forEach((show) => {
      const screen = show.screen;
      if (!screen) return;
      const tId = screen.theatre_id;
      const sId = screen.id;

      if (!map[tId]) map[tId] = {};
      if (!map[tId][sId]) map[tId][sId] = [];
      map[tId][sId].push(show);
    });

    return Object.entries(map).map(([tIdStr, screensMap]) => {
      const theatreId = Number(tIdStr);
      return {
        theatreId,
        theatreName: getTheatreName(theatreId),
        address: getTheatreAddress(theatreId),
        screens: Object.entries(screensMap).map(([sIdStr, screenShows]) => {
          const screenId = Number(sIdStr);
          const screenObj = screenShows[0].screen;
          screenShows.sort((a, b) => a.start_time.localeCompare(b.start_time));
          
          return {
            screenId,
            screenName: screenObj?.name ?? `Screen #${screenId}`,
            screenType: screenObj?.screen_type ?? "Standard",
            shows: screenShows,
          };
        }),
      };
    });
  }, [selectedDate, shows, getTheatreName, getTheatreAddress]);

  const formatDateReadable = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", { weekday: "short", day: "numeric", month: "short" });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[hsl(222,84%,2.5%)] flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

  if (error || !movie) {
    return (
      <div className="min-h-screen bg-[hsl(222,84%,2.5%)] flex flex-col items-center justify-center gap-4 text-zinc-300">
        <p>{error || "Movie not found"}</p>
        <button onClick={() => router.push("/")} className="px-4 py-2 bg-red-600 text-white rounded-xl text-xs font-bold">
          Back to Home
        </button>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[hsl(222,84%,2.5%)] text-zinc-100 pb-20">
      
      {/* Spotlight Backdrop Banner */}
      <section className="relative h-[320px] w-full overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat filter blur-sm scale-105 opacity-20"
          style={{ backgroundImage: `url(${movie.poster_url ? resolveMediaUrl(movie.poster_url) : "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"})` }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[hsl(222,84%,2.5%)] to-transparent" />
        
        <div className="relative z-10 max-w-5xl mx-auto px-6 h-full flex items-end pb-6">
          <button 
            onClick={() => router.push("/")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/[0.08] bg-black/40 backdrop-blur-md text-xs font-bold text-zinc-300 hover:bg-white/[0.04] transition-colors mb-auto mt-6"
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </button>
        </div>
      </section>

      {/* Main Details & Showtimes Layout */}
      <section className="max-w-5xl mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-10 -mt-20 relative z-20">
        
        {/* Left Column: Movie Poster, Favorites & Watchlist */}
        <div className="md:col-span-1 space-y-6">
          <div className="aspect-[2/3] w-full rounded-2xl border border-white/[0.08] bg-zinc-950 overflow-hidden shadow-2xl">
            {movie.poster_url ? (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img src={resolveMediaUrl(movie.poster_url)} alt={movie.title} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center text-zinc-700 bg-white/[0.01]">
                <Film className="h-12 w-12 mb-2 stroke-[1.5]" />
                <span className="text-xs uppercase tracking-wide">Poster Unavailable</span>
              </div>
            )}
          </div>

          {/* Favorites & Watchlist controls (Task 6) */}
          <div className="flex gap-2.5">
            <button
              onClick={toggleFavorite}
              className={`flex-grow flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border text-xs font-bold transition-all ${
                isFavorite 
                  ? "bg-red-500/10 border-red-500/30 text-red-500 shadow-md"
                  : "bg-white/[0.02] border-white/[0.06] text-zinc-400 hover:border-white/[0.12] hover:text-zinc-200"
              }`}
            >
              <Heart className={`h-4 w-4 ${isFavorite ? "fill-red-500" : ""}`} />
              {isFavorite ? "Favorited" : "Favorite"}
            </button>

            <button
              onClick={toggleWatchlist}
              className={`flex-grow flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border text-xs font-bold transition-all ${
                isWatchlist
                  ? "bg-red-500/10 border-red-500/30 text-red-500 shadow-md"
                  : "bg-white/[0.02] border-white/[0.06] text-zinc-400 hover:border-white/[0.12] hover:text-zinc-200"
              }`}
            >
              <Bookmark className={`h-4 w-4 ${isWatchlist ? "fill-red-500" : ""}`} />
              {isWatchlist ? "On Watchlist" : "Watchlist"}
            </button>
          </div>

          <div className="space-y-4">
            <h1 className="text-2xl font-extrabold text-white">{movie.title}</h1>
            
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded bg-red-600/10 border border-red-500/20 px-2 py-0.5 text-[10px] font-bold text-red-400 capitalize">
                {movie.genre}
              </span>
              <span className="rounded bg-zinc-800 px-2 py-0.5 text-[10px] font-bold text-zinc-300">
                {movie.language}
              </span>
              {movie.rating && movie.rating > 0 && (
                <span className="flex items-center gap-1 rounded bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 text-[10px] font-extrabold text-amber-400">
                  <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                  {movie.rating.toFixed(1)} / 10
                </span>
              )}
            </div>

            <div className="space-y-2 text-xs text-zinc-400 border-t border-white/[0.04] pt-4">
              <div className="flex items-center justify-between">
                <span>Duration:</span>
                <span className="font-semibold text-zinc-200">
                  {movie.duration != null ? `${movie.duration} minutes` : "Runtime unavailable"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Format:</span>
                <span className="font-semibold text-zinc-200">{movie.format || "2D Digital"}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Showtime Schedule Picker & Reviews */}
        <div className="md:col-span-2 space-y-8">
          
          <div className="space-y-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-500">Synopsis</h2>
            <p className="text-zinc-300 text-sm leading-relaxed font-medium">
              {movie.description || "No synopsis available for this movie spotlight listing."}
            </p>
          </div>

          {/* Date Selector Header */}
          <div className="space-y-3 border-t border-white/[0.04] pt-6">
            <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5">
              <Calendar className="h-4 w-4 text-red-500" />
              Select Date
            </h2>
            
            {uniqueDates.length === 0 ? (
              <div className="rounded-xl border border-white/[0.04] bg-white/[0.01] p-8 text-center text-zinc-500 text-xs">
                No shows scheduled for this movie currently.
              </div>
            ) : (
              <div className="flex gap-2.5 overflow-x-auto pb-2 scrollbar-none">
                {uniqueDates.map((dateStr) => (
                  <button
                    key={dateStr}
                    onClick={() => setSelectedDate(dateStr)}
                    className={`
                      px-4 py-2.5 rounded-xl border text-xs font-bold shrink-0 transition-all
                      ${selectedDate === dateStr
                        ? "bg-red-600 border-red-500 text-white shadow-lg shadow-red-600/10"
                        : "bg-white/[0.01] border-white/[0.06] text-zinc-400 hover:border-white/[0.12] hover:text-zinc-200"
                      }
                    `}
                  >
                    {formatDateReadable(dateStr)}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Showtime Listings by Theatre */}
          {selectedDate && (
            <div className="space-y-6">
              <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1.5">
                <Clock className="h-4 w-4 text-red-500" />
                Available Showtimes
              </h2>

              {groupedShows.length === 0 ? (
                <div className="text-zinc-500 text-xs py-4">No screenings found on this date.</div>
              ) : (
                <div className="space-y-5">
                  {groupedShows.map((theatre) => (
                    <div 
                      key={theatre.theatreId}
                      className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5 space-y-4 shadow-sm"
                    >
                      <div>
                        <h3 className="font-extrabold text-sm text-zinc-100 flex items-center gap-1.5">
                          <MapPin className="h-4 w-4 text-zinc-500" />
                          {theatre.theatreName}
                        </h3>
                        <p className="text-[10px] text-zinc-500 ml-5">{theatre.address}</p>
                      </div>

                      <div className="space-y-4 border-t border-white/[0.04] pt-4">
                        {theatre.screens.map((screen) => (
                          <div key={screen.screenId} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white/[0.01] p-3 rounded-xl border border-white/[0.03]">
                            <span className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                              <Monitor className="h-3.5 w-3.5 text-red-500" />
                              {screen.screenName}
                              <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 font-extrabold ml-1.5">
                                {screen.screenType}
                              </span>
                            </span>

                            <div className="flex flex-wrap gap-2">
                              {screen.shows.map((show) => (
                                <Link
                                  key={show.id}
                                  href={`/book/${show.id}`}
                                  className="px-3.5 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-600 hover:text-white transition-all text-xs font-bold"
                                >
                                  {show.start_time.slice(0, 5)}
                                </Link>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Movie Reviews & Community Ratings (Task 7) */}
          <div className="space-y-6 border-t border-white/[0.04] pt-8">
            <h2 className="text-sm font-extrabold text-white flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-red-500" />
              Community Reviews ({reviews.length})
            </h2>

            {/* Write review form */}
            {isAuthenticated ? (
              <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5 space-y-4">
                <h3 className="text-xs font-bold text-zinc-300 uppercase tracking-wider">Write a Spotlight Review</h3>
                
                {submitSuccess && (
                  <div className="flex items-center gap-2 rounded-lg border border-green-500/20 bg-green-500/10 p-3 text-xs text-green-400">
                    <span>{submitSuccess}</span>
                  </div>
                )}
                {submitError && (
                  <div className="flex items-center gap-2 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span>{submitError}</span>
                  </div>
                )}

                <form onSubmit={handleSubmitReview} className="space-y-4">
                  <div className="flex items-center gap-4">
                    <label htmlFor="rating-sel" className="text-xs font-semibold text-zinc-400">Rating (1-10):</label>
                    <select
                      id="rating-sel"
                      value={reviewRating}
                      onChange={(e) => setReviewRating(Number(e.target.value))}
                      className="rounded-lg border border-white/[0.08] bg-zinc-900 px-3 py-1.5 text-xs text-white focus:outline-none"
                    >
                      {[10, 9, 8, 7, 6, 5, 4, 3, 2, 1].map(n => (
                        <option key={n} value={n}>{n} ★</option>
                      ))}
                    </select>
                  </div>

                  <div className="relative">
                    <textarea
                      placeholder="Share your thoughts on characters, direction, or recliner view quality..."
                      rows={3}
                      value={reviewComment}
                      onChange={(e) => setReviewComment(e.target.value)}
                      className="w-full rounded-xl border border-white/[0.08] bg-zinc-900/30 p-3 text-xs text-white placeholder-zinc-600 focus:border-red-500/30 outline-none"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmitPending}
                    className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-bold flex items-center gap-1.5 disabled:opacity-50 transition-all ml-auto"
                  >
                    {isSubmitPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                    Submit Review
                  </button>
                </form>
              </div>
            ) : (
              <div className="rounded-2xl border border-white/[0.04] bg-white/[0.005] p-5 text-center text-xs text-zinc-500">
                Please <Link href="/login" className="text-red-400 font-bold hover:underline">login</Link> to share a rating and review for this movie.
              </div>
            )}

            {/* List Reviews */}
            {reviews.length === 0 ? (
              <p className="text-xs text-zinc-500 italic pl-1">Be the first to leave a review!</p>
            ) : (
              <div className="space-y-4">
                {reviews.map((rev) => {
                  const isOwner = user && user.id === rev.user_id;
                  const isEditing = editingReviewId === rev.id;

                  return (
                    <div 
                      key={rev.id}
                      className="p-4 rounded-xl border border-white/[0.04] bg-white/[0.005] space-y-2 relative"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="h-7 w-7 rounded-full bg-zinc-800 text-zinc-300 flex items-center justify-center text-[10px] font-bold">
                            {rev.user?.username?.slice(0, 2).toUpperCase() || "US"}
                          </div>
                          <div>
                            <span className="text-xs font-bold text-zinc-200">{rev.user?.username || `User #${rev.user_id}`}</span>
                            <span className="text-[9px] text-zinc-500 block">
                              {new Date(rev.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>

                        {/* Rating Badge */}
                        <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-[10px] font-extrabold text-amber-400">
                          <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                          <span>{rev.rating}</span>
                        </div>
                      </div>

                      {/* Edit review form inside review card if editing */}
                      {isEditing ? (
                        <form onSubmit={(e) => handleUpdateReview(e, rev.id)} className="space-y-3 pt-2">
                          <div className="flex items-center gap-2">
                            <label className="text-[10px] font-bold text-zinc-500 uppercase">Rating:</label>
                            <select
                              value={editRating}
                              onChange={(e) => setEditRating(Number(e.target.value))}
                              className="rounded border border-white/[0.08] bg-zinc-900 py-1 px-2 text-xs text-white"
                            >
                              {[10, 9, 8, 7, 6, 5, 4, 3, 2, 1].map(n => (
                                <option key={n} value={n}>{n} ★</option>
                              ))}
                            </select>
                          </div>
                          <textarea
                            value={editComment}
                            onChange={(e) => setEditComment(e.target.value)}
                            className="w-full rounded-lg border border-white/[0.08] bg-zinc-900 p-2 text-xs text-white"
                          />
                          <div className="flex gap-2 justify-end">
                            <button
                              type="button"
                              onClick={() => setEditingReviewId(null)}
                              className="px-3 py-1 rounded bg-zinc-800 text-zinc-400 text-[10px] font-bold"
                            >
                              Cancel
                            </button>
                            <button
                              type="submit"
                              className="px-3 py-1 rounded bg-red-600 text-white text-[10px] font-bold"
                            >
                              Save
                            </button>
                          </div>
                        </form>
                      ) : (
                        <>
                          <p className="text-xs text-zinc-300 font-medium leading-relaxed">
                            {rev.comment}
                          </p>

                          {/* Owner controls */}
                          {isOwner && (
                            <div className="flex gap-3 justify-end pt-1">
                              <button
                                onClick={() => startEditReview(rev)}
                                className="text-[10px] font-bold text-zinc-500 hover:text-white flex items-center gap-0.5"
                              >
                                <Edit className="h-3 w-3" />
                                Edit
                              </button>
                              <button
                                onClick={() => handleDeleteReview(rev.id)}
                                className="text-[10px] font-bold text-red-500 hover:text-red-400 flex items-center gap-0.5"
                              >
                                <Trash2 className="h-3 w-3" />
                                Delete
                              </button>
                            </div>
                          )}
                        </>
                      )}

                    </div>
                  );
                })}
              </div>
            )}
          </div>

        </div>
      </section>
    </main>
  );
}
