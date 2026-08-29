"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, Film, Calendar, Star, PlayCircle } from "lucide-react";
import { moviesApi } from "@/lib/api/movies";
import { resolveMediaUrl } from "@/lib/api/client";
import type { Movie } from "@/types/domain";

export default function Home() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"all" | "now-showing" | "coming-soon">("all");

  useEffect(() => {
    async function loadMovies() {
      try {
        const data = await moviesApi.list();
        setMovies(data ?? []);
      } catch (err) {
        console.error("Failed to load movies:", err);
      } finally {
        setLoading(false);
      }
    }
    loadMovies();
  }, []);

  const filteredMovies = movies.filter((movie) => {
    // Matches search
    const matchesSearch = movie.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          movie.genre.toLowerCase().includes(searchQuery.toLowerCase());
    
    // Matches tabs. Note that movie detail doesn't have an explicit status field in Movie domain interface, 
    // but in Part 2 we replaced active flag with status mappings or rating-based logic. 
    // Since movie has is_deleted or rating, let's map status: 
    // If rating is >= 7, we treat it as Now Showing. If rating is null or less, it might be Coming Soon.
    // Or let's check rating/duration to classify them for UI purposes.
    if (activeTab === "all") return matchesSearch;
    if (activeTab === "now-showing") {
      return matchesSearch && (movie.rating && movie.rating > 0);
    }
    if (activeTab === "coming-soon") {
      return matchesSearch && (!movie.rating || movie.rating === 0);
    }
    return matchesSearch;
  });

  return (
    <main className="min-h-screen bg-[hsl(222,84%,2.5%)] text-zinc-100 pb-20">
      {/* Hero Spotlight Section */}
      <section className="relative w-full h-[450px] overflow-hidden flex items-center justify-center border-b border-white/[0.04]">
        <div className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-20 filter blur-sm scale-105" 
             style={{ backgroundImage: `url('https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070')` }} />
        <div className="absolute inset-0 bg-gradient-to-t from-[hsl(222,84%,2.5%)] via-[hsl(222,84%,2.5%)]/70 to-transparent" />
        
        <div className="relative z-10 max-w-5xl w-full mx-auto px-6 text-center space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full px-3.5 py-1 bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold uppercase tracking-wider">
            <PlayCircle className="h-3.5 w-3.5" />
            Now Spotlighting
          </div>
          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white drop-shadow-lg">
            Cinema Plus <span className="text-red-500">Spotlight</span>
          </h1>
          <p className="max-w-2xl mx-auto text-sm sm:text-base text-zinc-400 font-medium leading-relaxed">
            Reserve premium luxury recliners, access real-time occupancy maps, and experience state-of-the-art cinema layouts instantly.
          </p>
        </div>
      </section>

      {/* Discovery Shell */}
      <section className="max-w-5xl w-full mx-auto px-6 mt-12 space-y-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/[0.04] pb-5">
          {/* Tab Selector */}
          <div className="flex rounded-xl bg-white/[0.02] border border-white/[0.06] p-1 self-start">
            <button
              onClick={() => setActiveTab("all")}
              className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                activeTab === "all" ? "bg-red-600 text-white shadow-md" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              All Movies
            </button>
            <button
              onClick={() => setActiveTab("now-showing")}
              className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                activeTab === "now-showing" ? "bg-red-600 text-white shadow-md" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Now Showing
            </button>
            <button
              onClick={() => setActiveTab("coming-soon")}
              className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                activeTab === "coming-soon" ? "bg-red-600 text-white shadow-md" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Coming Soon
            </button>
          </div>

          {/* Search Input */}
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
            <input
              type="text"
              placeholder="Search movies, genres, language..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl border border-white/[0.06] bg-white/[0.02] py-2 pl-10 pr-4 text-xs text-zinc-200 placeholder-zinc-600 outline-none focus:border-red-500/30 transition-colors"
            />
          </div>
        </div>

        {/* Movie Listing Grid */}
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-3 animate-pulse">
                <div className="aspect-[2/3] w-full rounded-xl bg-white/[0.03]" />
                <div className="h-4 w-3/4 rounded bg-white/[0.03]" />
                <div className="h-3.5 w-1/2 rounded bg-white/[0.03]" />
              </div>
            ))}
          </div>
        ) : filteredMovies.length === 0 ? (
          <div className="rounded-2xl border border-white/[0.04] bg-white/[0.01] p-16 text-center">
            <Film className="mx-auto h-12 w-12 text-zinc-700 mb-3" />
            <p className="text-zinc-500 text-sm">No spotlight movies matched your query.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {filteredMovies.map((movie) => (
              <Link 
                href={`/movies/${movie.id}`} 
                key={movie.id}
                className="group flex flex-col gap-3.5"
              >
                {/* Poster Box */}
                <div className="aspect-[2/3] w-full rounded-2xl bg-white/[0.02] border border-white/[0.05] overflow-hidden relative shadow-md group-hover:border-red-500/20 group-hover:shadow-red-500/5 transition-all duration-300">
                  {movie.poster_url ? (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img
                      src={resolveMediaUrl(movie.poster_url)}
                      alt={movie.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center text-zinc-700 bg-white/[0.01]">
                      <Film className="h-10 w-10 mb-2 stroke-[1.5]" />
                      <span className="text-[10px] uppercase tracking-wide">Poster Unavailable</span>
                    </div>
                  )}
                  {/* Overlay rating badge */}
                  {movie.rating && movie.rating > 0 && (
                    <div className="absolute top-3 right-3 flex items-center gap-1 rounded bg-black/70 backdrop-blur-md px-1.5 py-0.5 text-[10px] font-extrabold text-amber-400">
                      <Star className="h-3 w-3 fill-amber-400 text-amber-400 shrink-0" />
                      {movie.rating.toFixed(1)}
                    </div>
                  )}
                </div>

                {/* Movie metadata details */}
                <div className="space-y-1">
                  <h3 className="font-bold text-sm text-zinc-100 group-hover:text-red-400 transition-colors line-clamp-1">
                    {movie.title}
                  </h3>
                  <p className="text-[11px] text-zinc-500 font-semibold uppercase tracking-wide">
                    {movie.genre} • {movie.language}
                  </p>
                  <p className="text-[11px] text-zinc-400 flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5 text-zinc-600" />
                    <span>Duration: {movie.duration} mins</span>
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
