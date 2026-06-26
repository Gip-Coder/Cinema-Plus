"use client";

import { useEffect, useState, useCallback } from "react";
import { Search, FileSpreadsheet, Eye, X, AlertTriangle } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import * as adminApi from "@/lib/api/admin";
import type { AuditLog } from "@/types/admin";

export default function AdminAuditPage() {
  const { accessToken, role } = useAuth();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [entityFilter, setEntityFilter] = useState("all");
  const [error, setError] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const fetchLogs = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    try {
      const data = await adminApi.getAuditLogs(accessToken, 0, 200);
      setLogs(data ?? []);
      setError(null);
    } catch {
      setError("Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Authorization Check
  if (role && role !== "admin" && role !== "super_admin") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center p-6">
        <AlertTriangle className="h-12 w-12 text-amber-500 mb-4 animate-bounce" />
        <h2 className="text-xl font-bold text-zinc-200">Access Denied</h2>
        <p className="text-sm text-zinc-500 mt-2 max-w-sm">
          You do not have the required permissions to view the system audit logs. Only administrators and super administrators are authorized.
        </p>
      </div>
    );
  }

  const handleExportCSV = () => {
    if (logs.length === 0) return;
    const headers = ["ID", "User ID", "Entity Type", "Entity ID", "Action", "Old Value", "New Value", "IP Address", "Timestamp"];
    const rows = logs.map((log) => [
      log.id,
      log.user_id,
      log.entity_type,
      log.entity_id,
      log.action,
      log.old_value ?? "",
      log.new_value ?? "",
      log.ip_address ?? "",
      log.timestamp,
    ]);
    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e) => e.map((val) => `"${String(val).replace(/"/g, '""')}"`).join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filtered = logs.filter((l) => {
    const q = search.toLowerCase();
    const matchesSearch =
      !q ||
      String(l.user_id).includes(q) ||
      l.entity_type.toLowerCase().includes(q) ||
      l.action.toLowerCase().includes(q) ||
      (l.ip_address && l.ip_address.toLowerCase().includes(q));

    const matchesEntity = entityFilter === "all" || l.entity_type.toLowerCase() === entityFilter.toLowerCase();

    return matchesSearch && matchesEntity;
  });

  const uniqueEntities = Array.from(new Set(logs.map((l) => l.entity_type)));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Audit Logs</h1>
          <p className="text-sm text-zinc-500 mt-1">Track and audit administrative system actions</p>
        </div>
        <button
          onClick={handleExportCSV}
          disabled={logs.length === 0}
          className="inline-flex items-center gap-2 rounded-lg bg-zinc-800 border border-white/[0.08] px-4 py-2.5 text-sm font-semibold text-zinc-200 shadow-lg hover:bg-zinc-700 disabled:opacity-50 transition-colors"
        >
          <FileSpreadsheet className="h-4 w-4" />
          Export CSV
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-400">{error}</div>
      )}

      {/* Filters */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="relative md:col-span-2">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Search by action, user ID, or IP..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-white/[0.06] bg-white/[0.02] py-2.5 pl-10 pr-4 text-sm text-zinc-200 placeholder-zinc-600 outline-none focus:border-red-500/30 focus:ring-1 focus:ring-red-500/20 transition-colors"
          />
        </div>
        <div>
          <select
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            className="w-full rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2.5 text-sm text-zinc-200 outline-none focus:border-red-500/30 transition-colors"
          >
            <option value="all">All Entity Types</option>
            {uniqueEntities.map((ent) => (
              <option key={ent} value={ent.toLowerCase()}>
                {ent}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/[0.06] text-zinc-500 text-left">
                <th className="px-4 py-3 font-medium">Timestamp</th>
                <th className="px-4 py-3 font-medium">User ID</th>
                <th className="px-4 py-3 font-medium">Entity Type</th>
                <th className="px-4 py-3 font-medium">Entity ID</th>
                <th className="px-4 py-3 font-medium">Action</th>
                <th className="px-4 py-3 font-medium">IP Address</th>
                <th className="px-4 py-3 font-medium text-right">Details</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="border-b border-white/[0.04]">
                    <td colSpan={7} className="px-4 py-4">
                      <div className="h-5 animate-pulse rounded bg-white/[0.04]" />
                    </td>
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-zinc-500">
                    No audit logs matching selection
                  </td>
                </tr>
              ) : (
                filtered.map((log) => (
                  <tr
                    key={log.id}
                    className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="px-4 py-3 text-zinc-400 font-mono">
                      {new Date(log.timestamp).toLocaleString("en-IN")}
                    </td>
                    <td className="px-4 py-3 text-zinc-300 font-medium">User #{log.user_id}</td>
                    <td className="px-4 py-3">
                      <span className="rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300">
                        {log.entity_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-zinc-400 font-mono">#{log.entity_id}</td>
                    <td className="px-4 py-3 text-zinc-300">{log.action}</td>
                    <td className="px-4 py-3 text-zinc-400 font-mono">{log.ip_address ?? "N/A"}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="rounded p-1.5 text-zinc-500 hover:bg-white/[0.06] hover:text-zinc-300 transition-colors"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Details Dialog Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-white/[0.06] bg-[hsl(222,84%,5.5%)] p-6 shadow-2xl overflow-y-auto max-h-[90vh]">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-zinc-100">Audit Details (Log #{selectedLog.id})</h2>
              <button onClick={() => setSelectedLog(null)} className="text-zinc-500 hover:text-zinc-300">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4 text-sm text-zinc-300">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-xs text-zinc-500 block">Timestamp</span>
                  <span className="font-mono text-zinc-200">
                    {new Date(selectedLog.timestamp).toLocaleString("en-IN")}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-zinc-500 block">Operator ID</span>
                  <span className="text-zinc-200">User #{selectedLog.user_id}</span>
                </div>
                <div>
                  <span className="text-xs text-zinc-500 block">IP Address</span>
                  <span className="font-mono text-zinc-200">{selectedLog.ip_address ?? "N/A"}</span>
                </div>
                <div>
                  <span className="text-xs text-zinc-500 block">Action</span>
                  <span className="text-zinc-200">{selectedLog.action}</span>
                </div>
              </div>

              <div>
                <span className="text-xs text-zinc-500 block mb-1">Target Entity</span>
                <span className="rounded bg-zinc-800 px-2 py-1 text-xs text-zinc-300 font-mono">
                  {selectedLog.entity_type} ID: {selectedLog.entity_id}
                </span>
              </div>

              <div className="grid gap-4 mt-4">
                <div>
                  <span className="text-xs text-zinc-500 block mb-1">Old State</span>
                  <pre className="p-3 bg-zinc-950 rounded-lg text-xs font-mono text-zinc-400 overflow-x-auto max-h-[150px]">
                    {selectedLog.old_value ? JSON.stringify(JSON.parse(selectedLog.old_value), null, 2) : "N/A"}
                  </pre>
                </div>
                <div>
                  <span className="text-xs text-zinc-500 block mb-1">New State</span>
                  <pre className="p-3 bg-zinc-950 rounded-lg text-xs font-mono text-emerald-400 overflow-x-auto max-h-[150px]">
                    {selectedLog.new_value ? JSON.stringify(JSON.parse(selectedLog.new_value), null, 2) : "N/A"}
                  </pre>
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedLog(null)}
                className="rounded-lg border border-white/[0.08] px-4 py-2 text-sm text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04] transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
