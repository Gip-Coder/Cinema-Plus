"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Database,
  RefreshCw,
  AlertTriangle,
  Clock,
  Activity,
  Archive,
  Terminal,
  PlayCircle
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import * as adminApi from "@/lib/api/admin";
import { authApi } from "@/lib/api/auth";
import { moviesApi } from "@/lib/api/movies";
import { bookingsApi } from "@/lib/api/bookings";
import type { SystemHealth } from "@/types/admin";

interface LatencyTestPoint {
  endpoint: string;
  latencyMs: number;
  status: "fast" | "average" | "slow" | "error";
}

// Every one of these is a real live request measured client-side
// (round-trip time, including network — not a backend-instrumented figure).
// There is no fabricated/demo data here: each entry either reflects an
// actual call made during this poll, or is absent.
const LATENCY_PROBES: Array<{ label: string; run: (token: string) => Promise<unknown> }> = [
  { label: "/api/admin/stats", run: (token) => adminApi.getStats(token) },
  { label: "/api/auth/me", run: (token) => authApi.me(token) },
  { label: "/api/movies/", run: () => moviesApi.list() },
  { label: "/api/bookings/user/bookings", run: (token) => bookingsApi.userBookings(token) },
  { label: "/api/layouts/templates/list", run: (token) => adminApi.getLayoutTemplates(token) },
];

function classifyLatency(ms: number): LatencyTestPoint["status"] {
  if (ms > 200) return "slow";
  if (ms > 100) return "average";
  return "fast";
}

async function measureLatencies(token: string): Promise<LatencyTestPoint[]> {
  const results: LatencyTestPoint[] = [];
  for (const probe of LATENCY_PROBES) {
    const start = performance.now();
    try {
      await probe.run(token);
      const latencyMs = Math.round(performance.now() - start);
      results.push({ endpoint: probe.label, latencyMs, status: classifyLatency(latencyMs) });
    } catch {
      results.push({ endpoint: probe.label, latencyMs: 0, status: "error" });
    }
  }
  return results;
}

interface LogEntry {
  time: string;
  level: "info" | "warning";
  service: string;
  message: string;
}

export default function AdminHealthPage() {
  const { accessToken, role } = useAuth();

  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latencyTests, setLatencyTests] = useState<LatencyTestPoint[]>([]);

  // This console has no backend log-streaming API to read from — the
  // backend only writes to stdout (see backend/main.py's RequestLoggingMiddleware),
  // which isn't exposed over HTTP. Rather than fabricate log lines (as this
  // page previously did), this feed only ever contains entries this browser
  // session actually observed itself.
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const fetchHealth = useCallback(async (isRefresh = false) => {
    if (!accessToken) return;
    if (isRefresh) setRefreshing(true);
    else setLoading(true);

    try {
      const [data, latencies] = await Promise.all([
        adminApi.getSystemHealth(accessToken),
        measureLatencies(accessToken),
      ]);
      setHealth(data ?? null);
      setLatencyTests(latencies);
      setError(null);

      setLogs((prev) => [
        {
          time: new Date().toLocaleTimeString(),
          level: data?.status === "healthy" ? "info" : "warning",
          service: "health",
          message: `Health telemetry polled from this browser — status=${data?.status}, db=${data?.database.status} (${data?.database.engine}), storage=${data?.storage.status}.`,
        },
        ...prev.slice(0, 8),
      ]);
    } catch {
      setError("Failed to fetch system health status telemetry.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  // Authorization Check
  if (role && role !== "admin" && role !== "super_admin") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center p-6">
        <AlertTriangle className="h-12 w-12 text-amber-500 mb-4 animate-bounce" />
        <h2 className="text-xl font-bold text-zinc-200">Access Denied</h2>
        <p className="text-sm text-zinc-500 mt-2 max-w-sm">
          You do not have the required permissions to view the system health dashboard. Only administrators and super administrators are authorized.
        </p>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    if (status === "healthy" || status === "fast") return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    if (status === "degraded" || status === "average" || status === "on_demand") return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    if (status === "not_configured") return "bg-zinc-500/10 text-zinc-400 border-zinc-500/20";
    return "bg-red-500/10 text-red-400 border-red-500/20";
  };

  const schedulerRows = health
    ? [
        { name: "Reservation Expiry Cleanup", ...health.scheduler_tasks.reservation_expiry_cleanup },
        { name: "Daily Revenue Compiler", ...health.scheduler_tasks.daily_revenue_compiler },
        { name: "Media Thumbnail Optimizer", ...health.scheduler_tasks.media_thumbnail_optimizer },
      ]
    : [];

  return (
    <div className="space-y-8 text-zinc-100 pb-16">

      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-white/[0.04] pb-6">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Operational Health Console</h1>
          <p className="text-sm text-zinc-500 mt-1">Live status of the FastAPI backend, database, and storage — every value below is measured on each poll, not simulated.</p>
        </div>
        <button
          onClick={() => fetchHealth(true)}
          disabled={refreshing || loading}
          className="inline-flex items-center gap-2 rounded-lg bg-zinc-800 border border-white/[0.08] px-4 py-2.5 text-sm font-semibold text-zinc-200 shadow-lg hover:bg-zinc-700 disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
          {refreshing ? "Polling Health..." : "Poll Status"}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-400">{error}</div>
      )}

      {loading ? (
        <div className="grid gap-6 md:grid-cols-3 animate-pulse">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-32 rounded-xl border border-white/[0.06] bg-white/[0.02]" />
          ))}
        </div>
      ) : !health ? (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-12 text-center text-zinc-500">
          No operational details retrieved.
        </div>
      ) : (
        <>
          {/* Main Indicators grid */}
          <div className="grid gap-6 md:grid-cols-3">

            {/* Database & Latency */}
            <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-indigo-500/10 p-2">
                    <Database className="h-5 w-5 text-indigo-400" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-zinc-200">Database Connection</h3>
                    <p className="text-[10px] text-zinc-500 uppercase tracking-wide">{health.database.engine} pool</p>
                  </div>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-extrabold uppercase border ${getStatusColor(health.database.status)}`}>
                  {health.database.status}
                </span>
              </div>
              <div className="flex justify-between border-t border-white/[0.04] pt-4 text-xs font-semibold">
                <span className="text-zinc-500">FastAPI DB Latency:</span>
                <span className="font-mono text-zinc-200">{health.database.latency_ms} ms</span>
              </div>
            </div>

            {/* Storage Status */}
            <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-emerald-500/10 p-2">
                    <Archive className="h-5 w-5 text-emerald-400" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-zinc-200">Storage Provider</h3>
                    <p className="text-[10px] text-zinc-500">Local disk write test ({health.storage.path})</p>
                  </div>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-extrabold uppercase border ${getStatusColor(health.storage.status)}`}>
                  {health.storage.status}
                </span>
              </div>
              <div className="border-t border-white/[0.04] pt-4 text-[10px] text-zinc-500 leading-relaxed">
                {health.storage.note}
              </div>
            </div>

            {/* Reservation Guard Status */}
            <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-orange-500/10 p-2">
                    <Clock className="h-5 w-5 text-orange-400" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-zinc-200">Seat Reservation Guard</h3>
                    <p className="text-[10px] text-zinc-500">Database-level unique constraint</p>
                  </div>
                </div>
                <span className="rounded-full px-2 py-0.5 text-[10px] font-extrabold uppercase border bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                  ENFORCED
                </span>
              </div>
              <div className="flex justify-between border-t border-white/[0.04] pt-4 text-xs font-semibold">
                <span className="text-zinc-500">Hold Timeout:</span>
                <span className="font-mono text-zinc-200">{health.reservation.hold_minutes} min</span>
              </div>
              <p className="text-[10px] text-zinc-500 leading-relaxed">
                Double-booking is prevented by a permanent database constraint, not a
                monitored background process — there is no separate &quot;engine&quot; to be up or down.
              </p>
            </div>

          </div>

          {/* Latency & Tasks split */}
          <div className="grid gap-6 md:grid-cols-2">

            {/* API Latency Tests */}
            <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 space-y-4">
              <h3 className="font-bold text-sm text-zinc-200 flex items-center gap-2 border-b border-white/[0.04] pb-3">
                <Activity className="h-4 w-4 text-red-500" />
                API Endpoint Latency (live, client-measured round-trip)
              </h3>

              <div className="space-y-3">
                {latencyTests.map((test) => (
                  <div key={test.endpoint} className="flex items-center justify-between p-2.5 rounded-xl border border-white/[0.04] bg-white/[0.005] hover:bg-white/[0.015] transition-colors">
                    <span className="text-xs font-mono text-zinc-400 truncate max-w-[240px]">{test.endpoint}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-zinc-200">{test.status === "error" ? "—" : `${test.latencyMs} ms`}</span>
                      <span className={`px-1.5 py-0.5 rounded text-[8px] font-black uppercase ${getStatusColor(test.status)}`}>
                        {test.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Background Workers */}
            <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 space-y-4">
              <h3 className="font-bold text-sm text-zinc-200 flex items-center gap-2 border-b border-white/[0.04] pb-3">
                <PlayCircle className="h-4 w-4 text-red-500" />
                Scheduler Tasks
              </h3>

              <div className="space-y-3">
                {schedulerRows.map((task) => (
                  <div key={task.name} className="flex items-start justify-between gap-3 p-2.5 rounded-xl border border-white/[0.04] bg-white/[0.005]">
                    <div className="min-w-0">
                      <span className="text-xs font-bold text-zinc-300 block">{task.name}</span>
                      <span className="text-[10px] text-zinc-500 leading-relaxed block mt-1">{task.detail}</span>
                    </div>
                    <span className={`shrink-0 px-1.5 py-0.5 rounded text-[8px] font-black uppercase ${getStatusColor(task.status)}`}>
                      {task.status.replace("_", " ")}
                    </span>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* System logs shell */}
          <div className="rounded-2xl border border-white/[0.06] bg-zinc-950 p-6 space-y-4">
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <Terminal className="h-4 w-4 text-red-500" />
              Session Poll Log
            </h3>
            <p className="text-[10px] text-zinc-600">
              This backend does not expose a live log-streaming API, so this feed only records
              health polls made by this browser session — it is not a view into server-side logs.
              Check your Railway service logs directly for actual application/request logs.
            </p>

            <div className="p-4 bg-black/80 rounded-xl font-mono text-[11px] text-zinc-400 border border-white/[0.06] space-y-2 max-h-56 overflow-y-auto">
              {logs.length === 0 ? (
                <div className="text-zinc-600">No polls recorded yet this session.</div>
              ) : (
                logs.map((log, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <span className="text-zinc-600 shrink-0">{log.time}</span>
                    <span className={`uppercase font-bold shrink-0 w-16 ${
                      log.level === "warning" ? "text-amber-500" : "text-blue-400"
                    }`}>[{log.level}]</span>
                    <span className="text-zinc-500 shrink-0">[{log.service}]</span>
                    <span className="text-zinc-300">{log.message}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}

    </div>
  );
}
