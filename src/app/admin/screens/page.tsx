"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Plus, Search, Pencil, Monitor, X, ToggleLeft, ToggleRight, LayoutGrid } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import * as adminApi from "@/lib/api/admin";
import type { Screen, ScreenCreate, Theatre } from "@/types/admin";

type ModalMode = "create" | "edit" | null;

const SCREEN_TYPES = ["Standard", "IMAX", "4DX", "Dolby Atmos", "Gold Class", "VIP"];

export default function AdminScreensPage() {
  const { accessToken } = useAuth();
  const [screens, setScreens] = useState<Screen[]>([]);
  const [theatres, setTheatres] = useState<Theatre[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [modalMode, setModalMode] = useState<ModalMode>(null);
  const [editTarget, setEditTarget] = useState<Screen | null>(null);
  const [saving, setSaving] = useState(false);

  // Form state
  const [formName, setFormName] = useState("");
  const [formTheatreId, setFormTheatreId] = useState<number | "">("");
  const [formType, setFormType] = useState("Standard");
  const [formSeats, setFormSeats] = useState(220);
  const [formActive, setFormActive] = useState(true);

  const fetchData = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    try {
      const [screensData, theatresData] = await Promise.all([
        adminApi.getScreens(accessToken),
        adminApi.getTheatres(accessToken),
      ]);
      setScreens(screensData ?? []);
      setTheatres(theatresData ?? []);
      setError(null);
    } catch {
      setError("Failed to load screens");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getTheatreName = (theatreId: number) => {
    return theatres.find((t) => t.id === theatreId)?.name ?? `Theatre #${theatreId}`;
  };

  const openCreate = () => {
    setModalMode("create");
    setEditTarget(null);
    setFormName("");
    setFormTheatreId(theatres[0]?.id ?? "");
    setFormType("Standard");
    setFormSeats(220);
    setFormActive(true);
  };

  const openEdit = (screen: Screen) => {
    setModalMode("edit");
    setEditTarget(screen);
    setFormName(screen.name);
    setFormTheatreId(screen.theatre_id);
    setFormType(screen.screen_type);
    setFormSeats(screen.total_seats);
    setFormActive(screen.is_active);
  };

  const handleSave = async () => {
    if (!accessToken || !formName.trim() || formTheatreId === "") return;
    setSaving(true);
    try {
      if (modalMode === "create") {
        const payload: ScreenCreate = {
          name: formName.trim(),
          theatre_id: Number(formTheatreId),
          screen_type: formType,
          total_seats: formSeats,
          is_active: formActive,
        };
        await adminApi.createScreen(accessToken, payload);
      } else if (editTarget) {
        await adminApi.updateScreen(accessToken, editTarget.id, {
          name: formName.trim(),
          screen_type: formType,
          total_seats: formSeats,
          is_active: formActive,
        });
      }
      setModalMode(null);
      fetchData();
    } catch {
      setError("Failed to save screen");
    } finally {
      setSaving(false);
    }
  };

  const filtered = screens.filter((s) => {
    const q = search.toLowerCase();
    return (
      !q ||
      s.name.toLowerCase().includes(q) ||
      s.screen_type.toLowerCase().includes(q) ||
      getTheatreName(s.theatre_id).toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Screens</h1>
          <p className="text-sm text-zinc-500 mt-1">Manage cinema screens and auditoriums</p>
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-red-600/20 hover:bg-red-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add Screen
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-400">{error}</div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
        <input
          type="text"
          placeholder="Search by name, type, or theatre..."
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
                <th className="px-4 py-3 font-medium">Screen</th>
                <th className="px-4 py-3 font-medium">Theatre</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Capacity</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="border-b border-white/[0.04]">
                    <td colSpan={6} className="px-4 py-4">
                      <div className="h-5 animate-pulse rounded bg-white/[0.04]" />
                    </td>
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-zinc-500">
                    <Monitor className="mx-auto h-10 w-10 mb-2 text-zinc-600" />
                    No screens found
                  </td>
                </tr>
              ) : (
                filtered.map((screen) => (
                  <tr
                    key={screen.id}
                    className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="rounded-lg bg-cyan-500/10 p-2">
                          <Monitor className="h-4 w-4 text-cyan-400" />
                        </div>
                        <span className="font-medium text-zinc-200">{screen.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-zinc-400">{getTheatreName(screen.theatre_id)}</td>
                    <td className="px-4 py-3">
                      <span className="rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300">
                        {screen.screen_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-zinc-300 font-mono">{screen.total_seats}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          screen.is_active
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-zinc-500/10 text-zinc-500"
                        }`}
                      >
                        {screen.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Link
                          href={`/admin/layout-designer/${screen.id}`}
                          title="Design Seating Layout"
                          className="rounded p-1.5 text-zinc-500 hover:bg-white/[0.06] hover:text-cyan-400 transition-colors"
                        >
                          <LayoutGrid className="h-4 w-4" />
                        </Link>
                        <button
                          onClick={() => openEdit(screen)}
                          title="Edit Screen Details"
                          className="rounded p-1.5 text-zinc-500 hover:bg-white/[0.06] hover:text-zinc-300 transition-colors"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {!loading && filtered.length > 0 && (
          <div className="flex items-center justify-between border-t border-white/[0.06] px-4 py-3">
            <p className="text-xs text-zinc-500">
              Showing {filtered.length} of {screens.length} screens
            </p>
          </div>
        )}
      </div>

      {/* Modal */}
      {modalMode && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl border border-white/[0.06] bg-[hsl(222,84%,5.5%)] p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-zinc-100">
                {modalMode === "create" ? "Add Screen" : "Edit Screen"}
              </h2>
              <button onClick={() => setModalMode(null)} className="text-zinc-500 hover:text-zinc-300">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Name *</label>
                <input
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  placeholder="Screen 1"
                />
              </div>
              {modalMode === "create" && (
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Theatre *</label>
                  <select
                    value={formTheatreId}
                    onChange={(e) => setFormTheatreId(Number(e.target.value))}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  >
                    <option value="">Select theatre</option>
                    {theatres.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Type</label>
                  <select
                    value={formType}
                    onChange={(e) => setFormType(e.target.value)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  >
                    {SCREEN_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Total Seats</label>
                  <input
                    type="number"
                    value={formSeats}
                    onChange={(e) => setFormSeats(Number(e.target.value))}
                    min={1}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => setFormActive(!formActive)} className="text-zinc-400 hover:text-zinc-200">
                  {formActive ? (
                    <ToggleRight className="h-6 w-6 text-emerald-400" />
                  ) : (
                    <ToggleLeft className="h-6 w-6" />
                  )}
                </button>
                <span className="text-sm text-zinc-400">{formActive ? "Active" : "Inactive"}</span>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                onClick={() => setModalMode(null)}
                className="rounded-lg border border-white/[0.08] px-4 py-2 text-sm text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !formName.trim() || (modalMode === "create" && formTheatreId === "")}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {saving ? "Saving..." : modalMode === "create" ? "Create Screen" : "Update Screen"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
