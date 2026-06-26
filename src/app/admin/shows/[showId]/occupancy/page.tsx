"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  ChevronLeft, 
  TrendingUp, 
  Activity, 
  Users
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { scheduleApi } from "@/lib/api/schedule";
import * as adminApi from "@/lib/api/admin";
import { reservationsApi } from "@/lib/api/reservations";
import { apiClient } from "@/lib/api/client";
import type { Show, SeatDefinition, TheatreLayout } from "@/types/domain";

interface ShowStats {
  capacity: number;
  booked_count: number;
  reserved_count: number;
  occupancy_rate: number;
  reservation_rate: number;
  conversion_rate: number;
  reservation_metrics: {
    converted: number;
    expired: number;
    cancelled: number;
  };
}

export default function AdminShowOccupancyPage() {
  const { showId } = useParams();
  const router = useRouter();
  const { accessToken } = useAuth();

  const [show, setShow] = useState<Show | null>(null);
  const [layout, setLayout] = useState<TheatreLayout | null>(null);
  const [stats, setStats] = useState<ShowStats | null>(null);
  const [bookedSeats, setBookedSeats] = useState<string[]>([]);
  const [reservedSeats, setReservedSeats] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const seatSize = 28;
  const gapSize = 8;

  const canvasWidth = useMemo(() => (layout ? layout.cols * (seatSize + gapSize) + 80 : 500), [layout]);
  const canvasHeight = useMemo(() => (layout ? layout.rows * (seatSize + gapSize) + 160 : 400), [layout]);

  const fetchData = useCallback(async () => {
    if (!showId || !accessToken) return;
    try {
      const showData = await scheduleApi.show(Number(showId));
      setShow(showData);

      if (showData) {
        const [layoutData, statsData, statusData] = await Promise.all([
          adminApi.getLayoutForScreen(accessToken, showData.screen_id),
          apiClient.get<ShowStats>(`/api/admin/shows/${showId}/stats`, { token: accessToken }),
          reservationsApi.seatStatus(Number(showId)),
        ]);

        setLayout(layoutData);
        setStats(statsData);
        
        if (statusData) {
          const cast = statusData as unknown as { booked: string[]; reserved: string[] };
          setBookedSeats(cast.booked || []);
          setReservedSeats(cast.reserved || []);
        }
      }
      setError(null);
    } catch (err) {
      console.error("Failed to load show monitoring data:", err);
      setError("Failed to load active show monitoring stats.");
    } finally {
      setLoading(false);
    }
  }, [showId, accessToken]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Polling updates every 4 seconds
  useEffect(() => {
    if (loading || error) return;
    const interval = setInterval(async () => {
      try {
        const [statsData, statusData] = await Promise.all([
          apiClient.get<ShowStats>(`/api/admin/shows/${showId}/stats`, { token: accessToken || "" }),
          reservationsApi.seatStatus(Number(showId)),
        ]);
        setStats(statsData);
        if (statusData) {
          const cast = statusData as unknown as { booked: string[]; reserved: string[] };
          setBookedSeats(cast.booked || []);
          setReservedSeats(cast.reserved || []);
        }
      } catch (err) {
        console.error("Polling error in admin monitoring:", err);
      }
    }, 4000);

    return () => clearInterval(interval);
  }, [showId, accessToken, loading, error]);

  const getSeatColor = (seat: SeatDefinition) => {
    const code = seat.seat_code;
    if (bookedSeats.includes(code)) return "bg-zinc-800 border-zinc-700 text-zinc-500";
    if (reservedSeats.includes(code)) return "bg-amber-500 border-amber-400 text-amber-950";
    
    // Available colors
    if (seat.seat_type === "wheelchair") return "bg-cyan-900 border-cyan-500 text-cyan-200";
    if (seat.seat_type === "couple") return "bg-pink-900 border-pink-500 text-pink-200";
    
    switch (seat.category) {
      case "Premium": return "bg-rose-900 border-rose-600 text-rose-200";
      case "Executive": return "bg-amber-900 border-amber-600 text-amber-200";
      default: return "bg-slate-900 border-slate-700 text-slate-300";
    }
  };

  // Projected show revenue based on standard seat pricing (Normal 250, Executive 400, Premium 600)
  const projectedRevenue = useMemo(() => {
    if (!layout) return 0;
    return bookedSeats.reduce((acc, code) => {
      const seat = layout.seats.find((s) => s.seat_code === code);
      if (!seat) return acc + 250;
      if (seat.category === "Premium") return acc + 600;
      if (seat.category === "Executive") return acc + 400;
      return acc + 250;
    }, 0);
  }, [bookedSeats, layout]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[hsl(222,84%,2.5%)] flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <main className="space-y-6 text-left">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => router.back()}
            className="rounded-lg border border-white/[0.08] p-2 text-zinc-400 hover:text-zinc-200"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="text-xl font-extrabold text-white flex items-center gap-2">
              Live Occupancy: {show?.movie?.title}
            </h1>
            <p className="text-xs text-zinc-500 font-semibold mt-0.5">
              Screen: {show?.screen?.name} • Showtime: {show?.start_time.slice(0, 5)} • {show?.date}
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 text-xs text-red-400">
          {error}
        </div>
      )}

      {/* Operational Metrics Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 space-y-2">
            <div className="flex items-center justify-between text-zinc-500">
              <span className="text-[10px] uppercase font-bold tracking-wider">Occupancy Rate</span>
              <Users className="h-4 w-4 text-red-500" />
            </div>
            <p className="text-2xl font-extrabold text-white">{stats.occupancy_rate}%</p>
            <p className="text-[10px] text-zinc-500">
              {stats.booked_count} of {stats.capacity} seats sold
            </p>
          </div>

          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 space-y-2">
            <div className="flex items-center justify-between text-zinc-500">
              <span className="text-[10px] uppercase font-bold tracking-wider">Active holds</span>
              <Activity className="h-4 w-4 text-amber-500" />
            </div>
            <p className="text-2xl font-extrabold text-amber-400">{stats.reserved_count}</p>
            <p className="text-[10px] text-zinc-500">
              {stats.reservation_rate}% holding capacity
            </p>
          </div>

          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 space-y-2">
            <div className="flex items-center justify-between text-zinc-500">
              <span className="text-[10px] uppercase font-bold tracking-wider">Conversion rate</span>
              <TrendingUp className="h-4 w-4 text-emerald-400" />
            </div>
            <p className="text-2xl font-extrabold text-emerald-400">{stats.conversion_rate}%</p>
            <p className="text-[10px] text-zinc-500">
              {stats.reservation_metrics.converted} reserves purchased
            </p>
          </div>

          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 space-y-2">
            <div className="flex items-center justify-between text-zinc-500">
              <span className="text-[10px] uppercase font-bold tracking-wider">Show revenue</span>
              <span className="text-sm font-extrabold text-emerald-500">₹</span>
            </div>
            <p className="text-2xl font-extrabold text-white">
              {new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(
                projectedRevenue
              )}
            </p>
            <p className="text-[10px] text-zinc-500">Based on confirmed tickets</p>
          </div>
        </div>
      )}

      {/* Main visual tracker splits */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Side Seating Grid Map */}
        <div className="lg:col-span-3 rounded-2xl border border-white/[0.06] bg-[hsl(222,84%,1.5%)] p-6 overflow-x-auto min-h-[400px] flex items-center justify-center relative">
          <div className="absolute top-4 left-4 flex items-center gap-1.5 rounded-full px-2.5 py-1 bg-red-500/10 text-red-500 text-[10px] font-bold uppercase tracking-wider animate-pulse">
            <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
            Live Polling
          </div>

          {layout && (
            <div style={{ width: `${canvasWidth}px`, height: `${canvasHeight}px` }} className="relative">
              {/* Screen graphic */}
              <div className="absolute top-4 left-1/2 -translate-x-1/2 flex flex-col items-center">
                <div className="w-[200px] h-[4px] rounded-full bg-red-500/40 shadow-[0_0_12px_rgba(239,68,68,0.3)]" />
                <span className="text-[8px] text-zinc-700 mt-1 uppercase tracking-widest font-extrabold">Screen</span>
              </div>

              {/* Seating map loop */}
              {layout.seats.map((seat) => {
                if (!seat.is_active || seat.seat_type === "blocked") return null;
                const x = seat.position_x * (seatSize + gapSize) + 40;
                const y = seat.position_y * (seatSize + gapSize) + 85;

                return (
                  <div
                    key={seat.seat_code}
                    style={{
                      position: "absolute",
                      left: `${x}px`,
                      top: `${y}px`,
                      width: `${seatSize}px`,
                      height: `${seatSize}px`,
                    }}
                    className={`
                      rounded border flex items-center justify-center text-[8px] font-bold transition-all
                      ${getSeatColor(seat)}
                    `}
                  >
                    {seat.seat_code}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Side Legending and metrics */}
        <div className="space-y-4">
          <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500">Live Status Legend</h3>
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2.5">
                <span className="w-4 h-4 rounded border bg-slate-900 border-slate-700" />
                <span>Available</span>
              </div>
              <div className="flex items-center gap-2.5">
                <span className="w-4 h-4 rounded border bg-amber-500 border-amber-400" />
                <span>Reserved (Hold Session)</span>
              </div>
              <div className="flex items-center gap-2.5">
                <span className="w-4 h-4 rounded border bg-zinc-800 border-zinc-700" />
                <span>Booked (Sold Out)</span>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500">Session Actions logs</h3>
            {stats && (
              <div className="space-y-2 text-xs text-zinc-400">
                <div className="flex items-center justify-between border-b border-white/[0.03] pb-1.5">
                  <span>Reservations Converted:</span>
                  <span className="font-bold text-white">{stats.reservation_metrics.converted}</span>
                </div>
                <div className="flex items-center justify-between border-b border-white/[0.03] pb-1.5">
                  <span>Expired/Released:</span>
                  <span className="font-bold text-white">{stats.reservation_metrics.expired}</span>
                </div>
                <div className="flex items-center justify-between pb-1">
                  <span>Cancelled/Abandoned:</span>
                  <span className="font-bold text-white">{stats.reservation_metrics.cancelled}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
