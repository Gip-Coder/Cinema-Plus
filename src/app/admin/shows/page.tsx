"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import {
  Plus,
  Search,
  Trash2,
  Ticket,
  X,
  Calendar,
  Clock,
  AlertTriangle,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import * as adminApi from "@/lib/api/admin";
import type { Show, ShowCreate, Movie, Screen, Theatre } from "@/types/admin";

function timeToMinutes(time: string): number {
  const [h, m] = time.split(":").map(Number);
  return h * 60 + m;
}

function checkOverlap(
  existing: Show[],
  screenId: number,
  date: string,
  startTime: string,
  endTime: string,
  excludeId?: number,
): Show | null {
  const newStart = timeToMinutes(startTime);
  const newEnd = timeToMinutes(endTime);

  for (const show of existing) {
    if (show.screen_id !== screenId) continue;
    if (show.date !== date) continue;
    if (excludeId && show.id === excludeId) continue;

    const existStart = timeToMinutes(show.start_time);
    const existEnd = timeToMinutes(show.end_time);

    if (newStart < existEnd && newEnd > existStart) {
      return show;
    }
  }
  return null;
}

export default function AdminShowsPage() {
  const { accessToken, role } = useAuth();
  const [shows, setShows] = useState<Show[]>([]);
  const [movies, setMovies] = useState<Movie[]>([]);
  const [screens, setScreens] = useState<Screen[]>([]);
  const [theatres, setTheatres] = useState<Theatre[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [overlapWarning, setOverlapWarning] = useState<string | null>(null);

  const isReadOnly = role === "staff";

  // Form state
  const [formMovieId, setFormMovieId] = useState<number | "">("");
  const [formScreenId, setFormScreenId] = useState<number | "">("");
  const [formDate, setFormDate] = useState("");
  const [formStartTime, setFormStartTime] = useState("");
  const [formEndTime, setFormEndTime] = useState("");
  const [formMultiplier, setFormMultiplier] = useState(1.0);
  const [formBuffer, setFormBuffer] = useState(15);

  const fetchData = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    try {
      const [showsData, moviesData, screensData, theatresData] = await Promise.all([
        adminApi.getShows(accessToken),
        adminApi.getMovies(accessToken),
        adminApi.getScreens(accessToken),
        adminApi.getTheatres(accessToken),
      ]);
      setShows(showsData ?? []);
      setMovies(moviesData ?? []);
      setScreens(screensData ?? []);
      setTheatres(theatresData ?? []);
      setError(null);
    } catch {
      setError("Failed to load shows");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-compute end time from movie duration
  useEffect(() => {
    if (formMovieId && formStartTime) {
      const movie = movies.find((m) => m.id === formMovieId);
      if (movie) {
        const startMinutes = timeToMinutes(formStartTime);
        const duration = movie.duration ?? movie.duration_minutes ?? 120;
        const endMinutes = startMinutes + duration + formBuffer;
        const endH = Math.floor(endMinutes / 60) % 24;
        const endM = endMinutes % 60;
        setFormEndTime(`${String(endH).padStart(2, "0")}:${String(endM).padStart(2, "0")}`);
      }
    }
  }, [formMovieId, formStartTime, formBuffer, movies]);

  // Overlap check
  useEffect(() => {
    if (formScreenId && formDate && formStartTime && formEndTime) {
      const overlap = checkOverlap(shows, Number(formScreenId), formDate, formStartTime, formEndTime);
      if (overlap) {
        const movieName = overlap.movie?.title ?? `Movie #${overlap.movie_id}`;
        setOverlapWarning(
          `Conflicts with "${movieName}" (${overlap.start_time}–${overlap.end_time}) on this screen`,
        );
      } else {
        setOverlapWarning(null);
      }
    } else {
      setOverlapWarning(null);
    }
  }, [formScreenId, formDate, formStartTime, formEndTime, shows]);

  const getScreenName = (screenId: number) => {
    const screen = screens.find((s) => s.id === screenId);
    if (!screen) return `Screen #${screenId}`;
    const theatre = theatres.find((t) => t.id === screen.theatre_id);
    return `${screen.name} — ${theatre?.name ?? ""}`;
  };

  const openCreate = () => {
    setModalOpen(true);
    setFormMovieId(movies[0]?.id ?? "");
    setFormScreenId(screens[0]?.id ?? "");
    setFormDate(new Date().toISOString().split("T")[0]);
    setFormStartTime("");
    setFormEndTime("");
    setFormMultiplier(1.0);
    setOverlapWarning(null);
  };

  const handleSave = async () => {
    if (!accessToken || formMovieId === "" || formScreenId === "" || !formDate || !formStartTime || !formEndTime) return;
    if (overlapWarning) return;
    setSaving(true);
    try {
      const payload: ShowCreate = {
        movie_id: Number(formMovieId),
        screen_id: Number(formScreenId),
        date: formDate,
        start_time: formStartTime,
        end_time: formEndTime,
        price_multiplier: formMultiplier,
      };
      await adminApi.createShow(accessToken, payload);
      setModalOpen(false);
      fetchData();
    } catch {
      setError("Failed to create show");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!accessToken) return;
    if (!confirm("Delete this showtime?")) return;
    try {
      await adminApi.deleteShow(accessToken, id);
      fetchData();
    } catch {
      setError("Failed to delete show");
    }
  };

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    if (!q) return shows;
    return shows.filter(
      (s) =>
        s.movie?.title?.toLowerCase().includes(q) ||
        s.date.includes(q) ||
        getScreenName(s.screen_id).toLowerCase().includes(q),
    );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shows, search, screens, theatres]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Shows</h1>
          <p className="text-sm text-zinc-500 mt-1">Schedule and manage showtimes</p>
        </div>
        {!isReadOnly && (
          <button
            onClick={openCreate}
            className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-red-600/20 hover:bg-red-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Schedule Show
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-400">{error}</div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
        <input
          type="text"
          placeholder="Search by movie, date, or screen..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-white/[0.06] bg-white/[0.02] py-2.5 pl-10 pr-4 text-sm text-zinc-200 placeholder-zinc-600 outline-none focus:border-red-500/30 focus:ring-1 focus:ring-red-500/20 transition-colors"
        />
        {search && (
          <button onClick={() => setSearch("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300">
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Table */}
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/[0.06] text-zinc-500 text-left">
                <th className="px-4 py-3 font-medium">Movie</th>
                <th className="px-4 py-3 font-medium">Screen</th>
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium">Time</th>
                <th className="px-4 py-3 font-medium">Multiplier</th>
                <th className="px-4 py-3 font-medium text-right">{!isReadOnly && "Actions"}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="border-b border-white/[0.04]">
                    <td colSpan={isReadOnly ? 5 : 6} className="px-4 py-4">
                      <div className="h-5 animate-pulse rounded bg-white/[0.04]" />
                    </td>
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={isReadOnly ? 5 : 6} className="px-4 py-12 text-center text-zinc-500">
                    <Ticket className="mx-auto h-10 w-10 mb-2 text-zinc-600" />
                    No shows scheduled
                  </td>
                </tr>
              ) : (
                filtered.map((show) => (
                  <tr
                    key={show.id}
                    className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="px-4 py-3 font-medium text-zinc-200">
                      {show.movie?.title ?? `Movie #${show.movie_id}`}
                    </td>
                    <td className="px-4 py-3 text-zinc-400">{getScreenName(show.screen_id)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5 text-zinc-400">
                        <Calendar className="h-3.5 w-3.5" />
                        {show.date}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5 text-zinc-400">
                        <Clock className="h-3.5 w-3.5" />
                        {show.start_time} – {show.end_time}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-zinc-300">{show.price_multiplier}×</span>
                    </td>
                    {!isReadOnly && (
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleDelete(show.id)}
                          className="rounded p-1.5 text-zinc-500 hover:bg-red-500/10 hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!loading && filtered.length > 0 && (
          <div className="flex items-center justify-between border-t border-white/[0.06] px-4 py-3">
            <p className="text-xs text-zinc-500">Showing {filtered.length} shows</p>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl border border-white/[0.06] bg-[hsl(222,84%,5.5%)] p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-zinc-100">Schedule Show</h2>
              <button onClick={() => setModalOpen(false)} className="text-zinc-500 hover:text-zinc-300">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Movie *</label>
                <select
                  value={formMovieId}
                  onChange={(e) => setFormMovieId(Number(e.target.value))}
                  className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                >
                  <option value="">Select movie</option>
                  {movies.filter((m) => m.status !== "Archived").map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.title} ({m.duration ?? m.duration_minutes ?? 120} min)
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Screen *</label>
                <select
                  value={formScreenId}
                  onChange={(e) => setFormScreenId(Number(e.target.value))}
                  className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                >
                  <option value="">Select screen</option>
                  {screens.filter((s) => s.is_active).map((s) => (
                    <option key={s.id} value={s.id}>
                      {getScreenName(s.id)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Date *</label>
                <input
                  type="date"
                  value={formDate}
                  onChange={(e) => setFormDate(e.target.value)}
                  className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Start Time *</label>
                  <input
                    type="time"
                    value={formStartTime}
                    onChange={(e) => setFormStartTime(e.target.value)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">End Time</label>
                  <input
                    type="time"
                    value={formEndTime}
                    onChange={(e) => setFormEndTime(e.target.value)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  />
                  <p className="text-[10px] text-zinc-600 mt-1">Auto-calculated with {formBuffer} min buffer</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Price Multiplier</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    value={formMultiplier}
                    onChange={(e) => setFormMultiplier(Number(e.target.value))}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Turnaround Buffer (min)</label>
                  <input
                    type="number"
                    min="0"
                    value={formBuffer}
                    onChange={(e) => setFormBuffer(Number(e.target.value))}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  />
                </div>
              </div>

              {overlapWarning && (
                <div className="flex items-start gap-2 rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-sm text-amber-400">
                  <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
                  {overlapWarning}
                </div>
              )}
            </div>

            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                onClick={() => setModalOpen(false)}
                className="rounded-lg border border-white/[0.08] px-4 py-2 text-sm text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !!overlapWarning || formMovieId === "" || formScreenId === "" || !formStartTime}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {saving ? "Scheduling..." : "Schedule Show"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
