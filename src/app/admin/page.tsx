"use client";

import { useEffect, useState } from "react";
import {
  BarChart3,
  Clapperboard,
  DollarSign,
  Ticket,
  TrendingUp,
  Users,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import * as adminApi from "@/lib/api/admin";
import type { AdminStats, AdminBooking, RevenueChartPoint } from "@/types/admin";

interface StatCard {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(amount);
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

// Mini bar chart renderer
function MiniBarChart({ data }: { data: RevenueChartPoint[] }) {
  if (!data.length) return <div className="text-xs text-zinc-500">No data</div>;
  const max = Math.max(...data.map((d) => d.revenue), 1);
  const recent = data.slice(-14);

  return (
    <div className="flex items-end gap-1 h-32">
      {recent.map((point, i) => {
        const height = Math.max((point.revenue / max) * 100, 2);
        return (
          <div
            key={i}
            className="flex-1 group relative"
          >
            <div
              className="w-full rounded-t bg-gradient-to-t from-red-500/60 to-red-400/80 group-hover:from-red-500 group-hover:to-red-400 transition-all duration-200 cursor-pointer"
              style={{ height: `${height}%` }}
            />
            <div className="absolute -top-8 left-1/2 -translate-x-1/2 hidden group-hover:block bg-zinc-800 text-zinc-200 text-[10px] px-2 py-1 rounded whitespace-nowrap shadow-lg z-10">
              {formatCurrency(point.revenue)}
              <br />
              {point.date}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function AdminDashboardPage() {
  const { accessToken } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [revenueData, setRevenueData] = useState<RevenueChartPoint[]>([]);
  const [recentBookings, setRecentBookings] = useState<AdminBooking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    setLoading(true);
    Promise.all([
      adminApi.getStats(accessToken).catch(() => null),
      adminApi.getRevenueChart(accessToken).catch(() => []),
      adminApi.getBookings(accessToken, 0, 8).catch(() => []),
    ])
      .then(([statsData, chartData, bookingsData]) => {
        setStats(statsData);
        setRevenueData(chartData as RevenueChartPoint[]);
        setRecentBookings(bookingsData as AdminBooking[]);
        setError(null);
      })
      .catch(() => setError("Failed to load dashboard data"))
      .finally(() => setLoading(false));
  }, [accessToken]);

  const statCards: StatCard[] = stats
    ? [
        {
          label: "Today's Revenue",
          value: formatCurrency(stats.today_revenue ?? 0),
          icon: <DollarSign className="h-5 w-5" />,
          color: "text-emerald-400",
          bgColor: "bg-emerald-500/10",
        },
        {
          label: "Active Reservations",
          value: stats.active_reservations ?? 0,
          icon: <Ticket className="h-5 w-5" />,
          color: "text-amber-400",
          bgColor: "bg-amber-500/10",
        },
        {
          label: "Occupancy Rate",
          value: `${stats.occupancy_percentage ?? 0}%`,
          icon: <TrendingUp className="h-5 w-5" />,
          color: "text-cyan-400",
          bgColor: "bg-cyan-500/10",
        },
        {
          label: "Top Movie",
          value: stats.most_booked_movie ?? "N/A",
          icon: <Clapperboard className="h-5 w-5" />,
          color: "text-purple-400",
          bgColor: "bg-purple-500/10",
        },
        {
          label: "Total Revenue",
          value: formatCurrency(stats.total_revenue ?? 0),
          icon: <DollarSign className="h-5 w-5" />,
          color: "text-emerald-400",
          bgColor: "bg-emerald-500/10",
        },
        {
          label: "Total Bookings",
          value: stats.total_bookings ?? 0,
          icon: <Ticket className="h-5 w-5" />,
          color: "text-blue-400",
          bgColor: "bg-blue-500/10",
        },
        {
          label: "Total Users",
          value: stats.total_users ?? 0,
          icon: <Users className="h-5 w-5" />,
          color: "text-indigo-400",
          bgColor: "bg-indigo-500/10",
        },
        {
          label: "Active Shows",
          value: stats.total_shows ?? 0,
          icon: <BarChart3 className="h-5 w-5" />,
          color: "text-rose-400",
          bgColor: "bg-rose-500/10",
        },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Dashboard</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Welcome back. Here&apos;s an overview of your cinema platform.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Stats grid */}
      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-[104px] rounded-xl border border-white/[0.06] bg-white/[0.02] animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {statCards.map((card) => (
            <div
              key={card.label}
              className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 transition-all hover:border-white/[0.1] hover:bg-white/[0.03]"
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-zinc-500">{card.label}</p>
                <div className={`rounded-lg p-2 ${card.bgColor}`}>
                  <span className={card.color}>{card.icon}</span>
                </div>
              </div>
              <p className="mt-2 text-2xl font-bold text-zinc-100">{card.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Revenue chart & recent bookings */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Revenue chart */}
        <div className="lg:col-span-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-zinc-200">Revenue Overview</h2>
              <p className="text-xs text-zinc-500">Last 14 days</p>
            </div>
            <div className="rounded-lg bg-emerald-500/10 p-2">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
            </div>
          </div>
          {loading ? (
            <div className="h-32 animate-pulse rounded-lg bg-white/[0.03]" />
          ) : (
            <MiniBarChart data={revenueData} />
          )}
        </div>

        {/* Recent bookings */}
        <div className="lg:col-span-2 rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-zinc-200">Recent Bookings</h2>
            <span className="rounded-full bg-blue-500/10 px-2.5 py-0.5 text-xs font-medium text-blue-400">
              {recentBookings.length}
            </span>
          </div>
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-12 animate-pulse rounded-lg bg-white/[0.03]" />
              ))}
            </div>
          ) : recentBookings.length === 0 ? (
            <p className="text-sm text-zinc-500">No bookings found.</p>
          ) : (
            <div className="space-y-2 max-h-[280px] overflow-y-auto">
              {recentBookings.map((booking) => (
                <div
                  key={booking.id}
                  className="flex items-center justify-between rounded-lg bg-white/[0.02] px-3 py-2.5 border border-white/[0.04] hover:border-white/[0.08] transition-colors"
                >
                  <div>
                    <p className="text-sm font-medium text-zinc-300">Booking #{booking.id}</p>
                    <p className="text-xs text-zinc-500">{formatDate(booking.created_at)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-zinc-200">
                      {formatCurrency(booking.total_amount)}
                    </p>
                    <span
                      className={`text-[10px] font-medium uppercase tracking-wider px-1.5 py-0.5 rounded ${
                        booking.status === "confirmed"
                          ? "bg-emerald-500/10 text-emerald-400"
                          : booking.status === "cancelled"
                            ? "bg-red-500/10 text-red-400"
                            : "bg-amber-500/10 text-amber-400"
                      }`}
                    >
                      {booking.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
