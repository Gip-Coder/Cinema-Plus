"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Plus,
  Search,
  Pencil,
  Trash2,
  Theater,
  X,
  MapPin,
  Phone,
  Monitor,
  ToggleLeft,
  ToggleRight,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import * as adminApi from "@/lib/api/admin";
import type { Theatre, TheatreCreate } from "@/types/admin";

type ModalMode = "create" | "edit" | null;

export default function AdminTheatresPage() {
  const { accessToken } = useAuth();
  const [theatres, setTheatres] = useState<Theatre[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [modalMode, setModalMode] = useState<ModalMode>(null);
  const [editTarget, setEditTarget] = useState<Theatre | null>(null);
  const [saving, setSaving] = useState(false);

  // Form state
  const [formName, setFormName] = useState("");
  const [formAddress, setFormAddress] = useState("");
  const [formCity, setFormCity] = useState("");
  const [formState, setFormState] = useState("");
  const [formContact, setFormContact] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formTimezone, setFormTimezone] = useState("UTC");
  const [formActive, setFormActive] = useState(true);

  const fetchTheatres = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    try {
      const data = await adminApi.getTheatres(accessToken);
      setTheatres(data ?? []);
      setError(null);
    } catch {
      setError("Failed to load theatres");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchTheatres();
  }, [fetchTheatres]);

  const openCreate = () => {
    setModalMode("create");
    setEditTarget(null);
    setFormName("");
    setFormAddress("");
    setFormCity("");
    setFormState("");
    setFormContact("");
    setFormDescription("");
    setFormTimezone("UTC");
    setFormActive(true);
  };

  const openEdit = (theatre: Theatre) => {
    setModalMode("edit");
    setEditTarget(theatre);
    setFormName(theatre.name);
    setFormAddress(theatre.address ?? "");
    setFormCity(theatre.city ?? "");
    setFormState(theatre.state ?? "");
    setFormContact(theatre.contact_info ?? "");
    setFormDescription(theatre.description ?? "");
    setFormTimezone(theatre.timezone);
    setFormActive(theatre.is_active);
  };

  const handleSave = async () => {
    if (!accessToken || !formName.trim()) return;
    setSaving(true);
    try {
      const payload: TheatreCreate = {
        name: formName.trim(),
        address: formAddress || null,
        city: formCity || null,
        state: formState || null,
        contact_info: formContact || null,
        description: formDescription || null,
        timezone: formTimezone,
        is_active: formActive,
      };

      if (modalMode === "create") {
        await adminApi.createTheatre(accessToken, payload);
      } else if (editTarget) {
        await adminApi.updateTheatre(accessToken, editTarget.id, payload);
      }
      setModalMode(null);
      fetchTheatres();
    } catch {
      setError("Failed to save theatre");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!accessToken) return;
    if (!confirm("Are you sure you want to delete this theatre?")) return;
    try {
      await adminApi.deleteTheatre(accessToken, id);
      fetchTheatres();
    } catch {
      setError("Failed to delete theatre");
    }
  };

  const filtered = theatres.filter((t) => {
    const q = search.toLowerCase();
    return (
      !q ||
      t.name.toLowerCase().includes(q) ||
      t.city?.toLowerCase().includes(q) ||
      t.state?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Theatres</h1>
          <p className="text-sm text-zinc-500 mt-1">Manage cinema locations</p>
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-red-600/20 hover:bg-red-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add Theatre
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
          placeholder="Search by name, city, or state..."
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

      {/* Cards Grid */}
      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-48 animate-pulse rounded-xl border border-white/[0.06] bg-white/[0.02]" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-12 text-center">
          <Theater className="mx-auto h-12 w-12 text-zinc-600 mb-3" />
          <p className="text-zinc-500">No theatres found</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((theatre) => (
            <div
              key={theatre.id}
              className="group rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 hover:border-white/[0.1] hover:bg-white/[0.03] transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-purple-500/10 p-2.5">
                    <Theater className="h-5 w-5 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-zinc-200">{theatre.name}</h3>
                    <span
                      className={`text-[10px] uppercase tracking-wider font-medium px-1.5 py-0.5 rounded ${
                        theatre.is_active
                          ? "bg-emerald-500/10 text-emerald-400"
                          : "bg-zinc-500/10 text-zinc-500"
                      }`}
                    >
                      {theatre.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => openEdit(theatre)}
                    className="rounded p-1.5 text-zinc-500 hover:bg-white/[0.06] hover:text-zinc-300"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(theatre.id)}
                    className="rounded p-1.5 text-zinc-500 hover:bg-red-500/10 hover:text-red-400"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="mt-4 space-y-2 text-sm">
                {(theatre.city || theatre.state) && (
                  <div className="flex items-center gap-2 text-zinc-500">
                    <MapPin className="h-3.5 w-3.5" />
                    <span>{[theatre.city, theatre.state].filter(Boolean).join(", ")}</span>
                  </div>
                )}
                {theatre.contact_info && (
                  <div className="flex items-center gap-2 text-zinc-500">
                    <Phone className="h-3.5 w-3.5" />
                    <span>{theatre.contact_info}</span>
                  </div>
                )}
                <div className="flex items-center gap-2 text-zinc-500">
                  <Monitor className="h-3.5 w-3.5" />
                  <span>{theatre.screens.length} screen{theatre.screens.length !== 1 ? "s" : ""}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {modalMode && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-white/[0.06] bg-[hsl(222,84%,5.5%)] p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-zinc-100">
                {modalMode === "create" ? "Add Theatre" : "Edit Theatre"}
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
                  placeholder="Theatre name"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">City</label>
                  <input
                    value={formCity}
                    onChange={(e) => setFormCity(e.target.value)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                    placeholder="City"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">State</label>
                  <input
                    value={formState}
                    onChange={(e) => setFormState(e.target.value)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                    placeholder="State"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Address</label>
                <input
                  value={formAddress}
                  onChange={(e) => setFormAddress(e.target.value)}
                  className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  placeholder="Full address"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Contact</label>
                  <input
                    value={formContact}
                    onChange={(e) => setFormContact(e.target.value)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                    placeholder="Phone or email"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Timezone</label>
                  <input
                    value={formTimezone}
                    onChange={(e) => setFormTimezone(e.target.value)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                    placeholder="UTC"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Description</label>
                <textarea
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  rows={2}
                  className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30 resize-none"
                  placeholder="Optional description"
                />
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
                disabled={saving || !formName.trim()}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {saving ? "Saving..." : modalMode === "create" ? "Create Theatre" : "Update Theatre"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
