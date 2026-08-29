"use client";

import { useEffect, useState, useMemo, useRef, useCallback } from "react";
import NextImage from "next/image";
import { Plus, Search, Pencil, Trash2, Film, X, FileSpreadsheet, Upload, Link as LinkIcon } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import * as adminApi from "@/lib/api/admin";
import { resolveMediaUrl } from "@/lib/api/client";
import type { Movie } from "@/types/admin";

type ModalMode = "create" | "edit" | null;

export default function AdminMoviesPage() {
  const { accessToken, role } = useAuth();
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Selection for bulk actions
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  // Modal State
  const [modalMode, setModalMode] = useState<ModalMode>(null);
  const [editTarget, setEditTarget] = useState<Movie | null>(null);
  const [saving, setSaving] = useState(false);

  // Form State
  const [formTitle, setFormTitle] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formGenre, setFormGenre] = useState("");
  const [formLanguage, setFormLanguage] = useState("");
  const [formFormat, setFormFormat] = useState("2D");
  const [formDuration, setFormDuration] = useState(120);
  const [formRating, setFormRating] = useState<number | "">("");
  const [formReleaseDate, setFormReleaseDate] = useState("");
  const [formRunningDays, setFormRunningDays] = useState(14);
  const [formStatus, setFormStatus] = useState("Now Showing");
  const [formPosterSource, setFormPosterSource] = useState<"file" | "url">("url");
  const [formPosterUrl, setFormPosterUrl] = useState("");
  const [uploadingPoster, setUploadingPoster] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isReadOnly = role === "staff";

  const fetchMovies = useCallback(() => {
    if (!accessToken) return;
    setLoading(true);
    adminApi
      .getMovies(accessToken)
      .then((data) => {
        setMovies(data ?? []);
        setError(null);
      })
      .catch(() => setError("Failed to load movies"))
      .finally(() => setLoading(false));
  }, [accessToken]);

  useEffect(() => {
    fetchMovies();
  }, [fetchMovies]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    if (!q) return movies;
    return movies.filter(
      (m) =>
        m.title.toLowerCase().includes(q) ||
        m.genre?.toLowerCase().includes(q) ||
        m.language.toLowerCase().includes(q),
    );
  }, [movies, search]);

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(filtered.map((m) => m.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectRow = (checked: boolean, id: number) => {
    if (checked) {
      setSelectedIds((prev) => [...prev, id]);
    } else {
      setSelectedIds((prev) => prev.filter((x) => x !== id));
    }
  };

  const handleExportCSV = () => {
    if (filtered.length === 0) return;
    const headers = ["ID", "Title", "Genre", "Language", "Format", "Duration", "Rating", "Status", "Release Date"];
    const rows = filtered.map((m) => [
      m.id,
      m.title,
      m.genre ?? "",
      m.language,
      m.format,
      m.duration ?? m.duration_minutes ?? 0,
      m.rating ?? "",
      m.status ?? "Now Showing",
      m.release_date ?? "",
    ]);
    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e) => e.map((val) => `"${String(val).replace(/"/g, '""')}"`).join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `movies_catalog_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleBulkDelete = async () => {
    if (isReadOnly || selectedIds.length === 0 || !accessToken) return;
    if (!confirm(`Are you sure you want to delete the ${selectedIds.length} selected movies?`)) return;
    
    setLoading(true);
    try {
      await Promise.all(selectedIds.map((id) => adminApi.deleteMovie(accessToken, id)));
      setSelectedIds([]);
      fetchMovies();
    } catch {
      setError("Failed to delete some selected movies");
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (isReadOnly || !accessToken) return;
    if (!confirm("Are you sure you want to delete this movie?")) return;
    try {
      await adminApi.deleteMovie(accessToken, id);
      fetchMovies();
    } catch {
      setError("Failed to delete movie");
    }
  };

  const openCreate = () => {
    if (isReadOnly) return;
    setModalMode("create");
    setEditTarget(null);
    setFormTitle("");
    setFormDescription("");
    setFormGenre("");
    setFormLanguage("");
    setFormFormat("2D");
    setFormDuration(120);
    setFormRating("");
    setFormReleaseDate(new Date().toISOString().split("T")[0]);
    setFormRunningDays(14);
    setFormStatus("Now Showing");
    setFormPosterSource("url");
    setFormPosterUrl("");
  };

  const openEdit = (movie: Movie) => {
    if (isReadOnly) return;
    setModalMode("edit");
    setEditTarget(movie);
    setFormTitle(movie.title);
    setFormDescription(movie.description ?? "");
    setFormGenre(movie.genre ?? "");
    setFormLanguage(movie.language);
    setFormFormat(movie.format);
    setFormDuration(movie.duration ?? movie.duration_minutes ?? 120);
    setFormRating(movie.rating ? Number(movie.rating) : "");
    setFormReleaseDate(movie.release_date ? movie.release_date.split("T")[0] : "");
    setFormRunningDays(14);
    setFormStatus(movie.status ?? "Now Showing");
    setFormPosterSource("url");
    setFormPosterUrl(movie.poster_url ?? "");
  };

  const handlePosterFileUpload = async (file: File) => {
    if (!accessToken) return;
    setUploadingPoster(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await adminApi.uploadMoviePoster(accessToken, formData);
      if (res && res.poster_url) {
        setFormPosterUrl(res.poster_url);
      }
    } catch {
      alert("Failed to upload poster image");
    } finally {
      setUploadingPoster(false);
    }
  };

  const handleSave = async () => {
    if (isReadOnly || !accessToken || !formTitle.trim()) return;
    setSaving(true);
    try {
      const payload = {
        title: formTitle.trim(),
        description: formDescription.trim() || null,
        genre: formGenre.trim() || null,
        language: formLanguage.trim(),
        format: formFormat,
        duration: Number(formDuration),
        rating: formRating !== "" ? Number(formRating) : null,
        release_date: formReleaseDate || null,
        running_days: Number(formRunningDays),
        status: formStatus,
        poster_url: formPosterUrl.trim() || null,
        poster_source_type: formPosterSource,
      };

      if (modalMode === "create") {
        await adminApi.createMovie(accessToken, payload);
      } else if (editTarget) {
        await adminApi.updateMovie(accessToken, editTarget.id, payload);
      }
      setModalMode(null);
      fetchMovies();
    } catch {
      setError("Failed to save movie data");
    } finally {
      setSaving(false);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "Now Showing":
        return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/25";
      case "Coming Soon":
        return "bg-cyan-500/10 text-cyan-400 border border-cyan-500/25";
      case "Archived":
        return "bg-zinc-500/10 text-zinc-500 border border-white/[0.04]";
      default:
        return "bg-zinc-500/10 text-zinc-400";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Movies Catalog</h1>
          <p className="text-sm text-zinc-500 mt-1">
            {isReadOnly ? "View cinema movie listings" : "Manage cinema movie catalog and listings"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleExportCSV}
            disabled={filtered.length === 0}
            className="inline-flex items-center gap-2 rounded-lg bg-zinc-800 border border-white/[0.08] px-4 py-2.5 text-sm font-semibold text-zinc-200 shadow-lg hover:bg-zinc-700 disabled:opacity-50 transition-colors"
          >
            <FileSpreadsheet className="h-4 w-4" />
            Export CSV
          </button>
          {!isReadOnly && (
            <button
              onClick={openCreate}
              className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-red-600/20 hover:bg-red-700 transition-colors"
            >
              <Plus className="h-4 w-4" />
              Add Movie
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-400">{error}</div>
      )}

      {/* Bulk actions and search */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center justify-between">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Search movies by title, genre, or language..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-white/[0.06] bg-white/[0.02] py-2.5 pl-10 pr-4 text-sm text-zinc-200 placeholder-zinc-600 outline-none focus:border-red-500/30 focus:ring-1 focus:ring-red-500/20 transition-colors"
          />
        </div>
        {!isReadOnly && selectedIds.length > 0 && (
          <button
            onClick={handleBulkDelete}
            className="inline-flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/25 px-4 py-2.5 text-sm font-semibold text-red-400 hover:bg-red-500/20 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
            Delete Selected ({selectedIds.length})
          </button>
        )}
      </div>

      {/* Table */}
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/[0.06] text-zinc-500 text-left">
                {!isReadOnly && (
                  <th className="w-12 px-4 py-3 text-center">
                    <input
                      type="checkbox"
                      className="rounded border-white/[0.08] bg-white/[0.03] text-red-600 focus:ring-0"
                      checked={filtered.length > 0 && selectedIds.length === filtered.length}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                    />
                  </th>
                )}
                <th className="px-4 py-3 font-medium">Movie</th>
                <th className="px-4 py-3 font-medium">Genre</th>
                <th className="px-4 py-3 font-medium">Language</th>
                <th className="px-4 py-3 font-medium">Format</th>
                <th className="px-4 py-3 font-medium">Duration</th>
                <th className="px-4 py-3 font-medium">Rating</th>
                <th className="px-4 py-3 font-medium">Status</th>
                {!isReadOnly && <th className="px-4 py-3 font-medium text-right">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="border-b border-white/[0.04]">
                    <td colSpan={isReadOnly ? 8 : 9} className="px-4 py-4">
                      <div className="h-5 animate-pulse rounded bg-white/[0.04]" />
                    </td>
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={isReadOnly ? 8 : 9} className="px-4 py-12 text-center text-zinc-500">
                    <Film className="mx-auto h-10 w-10 mb-2 text-zinc-600" />
                    No movies found
                  </td>
                </tr>
              ) : (
                filtered.map((movie) => (
                  <tr
                    key={movie.id}
                    className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors"
                  >
                    {!isReadOnly && (
                      <td className="px-4 py-3 text-center">
                        <input
                          type="checkbox"
                          className="rounded border-white/[0.08] bg-white/[0.03] text-red-600 focus:ring-0"
                          checked={selectedIds.includes(movie.id)}
                          onChange={(e) => handleSelectRow(e.target.checked, movie.id)}
                        />
                      </td>
                    )}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {movie.poster_url ? (
                          <NextImage
                            src={resolveMediaUrl(movie.poster_url)}
                            alt={movie.title}
                            width={28}
                            height={40}
                            className="h-10 w-7 rounded object-cover bg-zinc-800"
                            unoptimized
                          />
                        ) : (
                          <div className="flex h-10 w-7 items-center justify-center rounded bg-zinc-800">
                            <Film className="h-4 w-4 text-zinc-600" />
                          </div>
                        )}
                        <span className="font-medium text-zinc-200 truncate max-w-[200px]">{movie.title}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-zinc-400">{movie.genre ?? "—"}</td>
                    <td className="px-4 py-3 text-zinc-400">{movie.language}</td>
                    <td className="px-4 py-3">
                      <span className="rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300">
                        {movie.format}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-zinc-400">{movie.duration ?? movie.duration_minutes} min</td>
                    <td className="px-4 py-3">
                      {movie.rating ? (
                        <span className="rounded bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-400">
                          {movie.rating}
                        </span>
                      ) : (
                        <span className="text-zinc-600">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusBadgeClass(movie.status)}`}>
                        {movie.status ?? "Now Showing"}
                      </span>
                    </td>
                    {!isReadOnly && (
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            title="Edit"
                            onClick={() => openEdit(movie)}
                            className="rounded p-1.5 text-zinc-500 hover:bg-white/[0.06] hover:text-zinc-300 transition-colors"
                          >
                            <Pencil className="h-4 w-4" />
                          </button>
                          <button
                            title="Delete"
                            onClick={() => handleDelete(movie.id)}
                            className="rounded p-1.5 text-zinc-500 hover:bg-red-500/10 hover:text-red-400 transition-colors"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        {!loading && filtered.length > 0 && (
          <div className="flex items-center justify-between border-t border-white/[0.06] px-4 py-3">
            <p className="text-xs text-zinc-500">
              Showing {filtered.length} of {movies.length} movies
            </p>
          </div>
        )}
      </div>

      {/* Modal CRUD dialog */}
      {modalMode && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-white/[0.06] bg-[hsl(222,84%,5.5%)] p-6 shadow-2xl overflow-y-auto max-h-[90vh]">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-zinc-100">
                {modalMode === "create" ? "Add Movie" : "Edit Movie"}
              </h2>
              <button onClick={() => setModalMode(null)} className="text-zinc-500 hover:text-zinc-300">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Title *</label>
                <input
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  placeholder="Inception"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Description</label>
                <textarea
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  rows={3}
                  className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30 resize-none"
                  placeholder="Movie plot description..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Genre *</label>
                  <input
                    value={formGenre}
                    onChange={(e) => setFormGenre(e.target.value)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                    placeholder="Sci-Fi / Action"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Language *</label>
                  <input
                    value={formLanguage}
                    onChange={(e) => setFormLanguage(e.target.value)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                    placeholder="English"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Format</label>
                  <select
                    value={formFormat}
                    onChange={(e) => setFormFormat(e.target.value)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  >
                    <option value="2D">2D</option>
                    <option value="3D">3D</option>
                    <option value="IMAX 3D">IMAX 3D</option>
                    <option value="4DX">4DX</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Duration (min)</label>
                  <input
                    type="number"
                    value={formDuration}
                    onChange={(e) => setFormDuration(Number(e.target.value))}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Rating (1-10)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="1"
                    max="10"
                    value={formRating}
                    onChange={(e) => setFormRating(e.target.value !== "" ? Number(e.target.value) : "")}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                    placeholder="8.8"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Release Date</label>
                  <input
                    type="date"
                    value={formReleaseDate}
                    onChange={(e) => setFormReleaseDate(e.target.value)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Status</label>
                  <select
                    value={formStatus}
                    onChange={(e) => setFormStatus(e.target.value)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  >
                    <option value="Now Showing">Now Showing</option>
                    <option value="Coming Soon">Coming Soon</option>
                    <option value="Archived">Archived</option>
                  </select>
                </div>
              </div>

              {/* Poster Upload Area */}
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Poster Source</label>
                <div className="flex gap-4 mb-2">
                  <button
                    type="button"
                    onClick={() => setFormPosterSource("url")}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border ${
                      formPosterSource === "url"
                        ? "border-red-500/30 bg-red-500/10 text-red-400"
                        : "border-white/[0.08] bg-white/[0.02] text-zinc-400 hover:text-zinc-300"
                    }`}
                  >
                    <LinkIcon className="h-3.5 w-3.5" />
                    External URL
                  </button>
                  <button
                    type="button"
                    onClick={() => setFormPosterSource("file")}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border ${
                      formPosterSource === "file"
                        ? "border-red-500/30 bg-red-500/10 text-red-400"
                        : "border-white/[0.08] bg-white/[0.02] text-zinc-400 hover:text-zinc-300"
                    }`}
                  >
                    <Upload className="h-3.5 w-3.5" />
                    File Upload
                  </button>
                </div>

                {formPosterSource === "url" ? (
                  <input
                    value={formPosterUrl}
                    onChange={(e) => setFormPosterUrl(e.target.value)}
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                    placeholder="https://example.com/poster.jpg"
                  />
                ) : (
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="rounded-lg border-2 border-dashed border-white/[0.08] bg-white/[0.02] p-4 text-center cursor-pointer hover:border-red-500/30 transition-colors"
                  >
                    <input
                      type="file"
                      ref={fileInputRef}
                      className="hidden"
                      accept="image/*"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handlePosterFileUpload(file);
                      }}
                    />
                    <Upload className="mx-auto h-6 w-6 text-zinc-500 mb-2" />
                    <span className="text-xs text-zinc-400">
                      {uploadingPoster ? "Uploading..." : formPosterUrl ? "Poster uploaded! Click to replace." : "Click to select poster image"}
                    </span>
                    {formPosterUrl && (
                      <p className="text-[10px] text-emerald-400 truncate mt-1">{formPosterUrl}</p>
                    )}
                  </div>
                )}
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
                disabled={saving || !formTitle.trim() || !formLanguage.trim() || uploadingPoster}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {saving ? "Saving..." : modalMode === "create" ? "Add Movie" : "Update Movie"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
