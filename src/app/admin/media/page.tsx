"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import NextImage from "next/image";
import {
  Plus,
  Trash2,
  Image as ImageIcon,
  Upload,
  Link as LinkIcon,
  X,
  FileImage,
  ExternalLink,
  Info,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import * as adminApi from "@/lib/api/admin";
import type { MediaAsset } from "@/types/admin";

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

type UploadTab = "file" | "url";

export default function AdminMediaPage() {
  const { accessToken } = useAuth();
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedMetadata, setSelectedMetadata] = useState<MediaAsset | null>(null);
  const [uploadTab, setUploadTab] = useState<UploadTab>("file");
  const [uploading, setUploading] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchAssets = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    // Media assets may be returned by different endpoints;
    // currently we just load an empty state if the list endpoint doesn't exist
    try {
      // The backend doesn't have a dedicated list endpoint; we fetch what we can
      setAssets([]);
      setError(null);
    } catch {
      setError("Failed to load media assets");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchAssets();
  }, [fetchAssets]);

  const handleFileUpload = async (file: File) => {
    if (!accessToken) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("asset_type", "original");
      const asset = await adminApi.uploadMediaFile(accessToken, formData);
      if (asset) {
        setAssets((prev) => [asset, ...prev]);
      }
      setModalOpen(false);
    } catch {
      setError("Failed to upload file");
    } finally {
      setUploading(false);
    }
  };

  const handleUrlUpload = async () => {
    if (!accessToken || !urlInput.trim()) return;
    setUploading(true);
    try {
      const asset = await adminApi.uploadMediaUrl(accessToken, urlInput.trim());
      if (asset) {
        setAssets((prev) => [asset, ...prev]);
      }
      setModalOpen(false);
      setUrlInput("");
    } catch {
      setError("Failed to register external media");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (assetId: number) => {
    if (!accessToken) return;
    if (!confirm("Delete this media asset?")) return;
    try {
      await adminApi.deleteMediaAsset(accessToken, assetId);
      setAssets((prev) => prev.filter((a) => a.id !== assetId));
    } catch {
      setError("Failed to delete media asset");
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileUpload(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => setDragActive(false);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Media Library</h1>
          <p className="text-sm text-zinc-500 mt-1">Upload and manage media assets</p>
        </div>
        <button
          onClick={() => {
            setModalOpen(true);
            setUploadTab("file");
            setUrlInput("");
          }}
          className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-red-600/20 hover:bg-red-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Upload Media
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-400">{error}</div>
      )}

      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          rounded-xl border-2 border-dashed p-8 text-center transition-all
          ${
            dragActive
              ? "border-red-500/50 bg-red-500/5"
              : "border-white/[0.06] bg-white/[0.01] hover:border-white/[0.1]"
          }
        `}
      >
        <Upload className={`mx-auto h-10 w-10 mb-3 ${dragActive ? "text-red-400" : "text-zinc-600"}`} />
        <p className="text-sm text-zinc-400">
          Drop files here or{" "}
          <button
            onClick={() => setModalOpen(true)}
            className="text-red-400 hover:text-red-300 underline"
          >
            browse
          </button>
        </p>
        <p className="text-xs text-zinc-600 mt-1">Supports images and videos</p>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="aspect-[4/3] animate-pulse rounded-xl border border-white/[0.06] bg-white/[0.02]" />
          ))}
        </div>
      ) : assets.length === 0 ? (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-12 text-center">
          <ImageIcon className="mx-auto h-12 w-12 text-zinc-600 mb-3" />
          <p className="text-zinc-500">No media assets yet</p>
          <p className="text-xs text-zinc-600 mt-1">Upload your first image or video</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {assets.map((asset) => (
            <div
              key={asset.id}
              className="group relative rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden hover:border-white/[0.1] transition-all"
            >
              {/* Preview */}
              <div className="aspect-[4/3] bg-zinc-900 flex items-center justify-center">
                {asset.public_url || asset.thumbnail_url ? (
                  <NextImage
                    src={asset.thumbnail_url ?? asset.public_url ?? ""}
                    alt={asset.filename}
                    width={400}
                    height={300}
                    className="w-full h-full object-cover"
                    unoptimized
                  />
                ) : (
                  <FileImage className="h-10 w-10 text-zinc-700" />
                )}
              </div>

              {/* Overlay actions */}
              <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                {asset.public_url && (
                  <a
                    href={asset.public_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded-lg bg-white/10 p-2 text-white hover:bg-white/20 transition-colors"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
                <button
                  onClick={() => setSelectedMetadata(asset)}
                  className="rounded-lg bg-white/10 p-2 text-white hover:bg-white/20 transition-colors"
                  title="View Metadata"
                >
                  <Info className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(asset.id)}
                  className="rounded-lg bg-red-500/20 p-2 text-red-400 hover:bg-red-500/30 transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>

              {/* Info */}
              <div className="p-3">
                <p className="text-sm font-medium text-zinc-300 truncate">{asset.filename}</p>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-zinc-600">{formatBytes(asset.size_bytes)}</span>
                  <span className="text-xs text-zinc-600">{formatDate(asset.created_at)}</span>
                </div>
                <div className="flex items-center gap-1 mt-1">
                  <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-400">
                    {asset.mime_type}
                  </span>
                  <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-400">
                    {asset.source_type}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl border border-white/[0.06] bg-[hsl(222,84%,5.5%)] p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-zinc-100">Upload Media</h2>
              <button onClick={() => setModalOpen(false)} className="text-zinc-500 hover:text-zinc-300">
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex rounded-lg border border-white/[0.06] mb-6">
              <button
                onClick={() => setUploadTab("file")}
                className={`flex-1 flex items-center justify-center gap-2 rounded-l-lg py-2 text-sm font-medium transition-colors ${
                  uploadTab === "file"
                    ? "bg-red-500/10 text-red-400"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                <Upload className="h-4 w-4" />
                File Upload
              </button>
              <button
                onClick={() => setUploadTab("url")}
                className={`flex-1 flex items-center justify-center gap-2 rounded-r-lg py-2 text-sm font-medium transition-colors ${
                  uploadTab === "url"
                    ? "bg-red-500/10 text-red-400"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                <LinkIcon className="h-4 w-4" />
                External URL
              </button>
            </div>

            {uploadTab === "file" ? (
              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,video/*"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) handleFileUpload(f);
                  }}
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="w-full rounded-xl border-2 border-dashed border-white/[0.08] bg-white/[0.02] p-8 text-center hover:border-white/[0.15] transition-colors"
                >
                  <FileImage className="mx-auto h-10 w-10 text-zinc-600 mb-2" />
                  <p className="text-sm text-zinc-400">
                    {uploading ? "Uploading..." : "Click to select a file"}
                  </p>
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1.5">Image URL</label>
                  <input
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="https://example.com/image.jpg"
                    className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-200 outline-none focus:border-red-500/30"
                  />
                </div>
                <button
                  onClick={handleUrlUpload}
                  disabled={uploading || !urlInput.trim()}
                  className="w-full rounded-lg bg-red-600 py-2.5 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
                >
                  {uploading ? "Registering..." : "Register External Media"}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Rich Metadata Modal */}
      {selectedMetadata && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl border border-white/[0.06] bg-[hsl(222,84%,5.5%)] p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-zinc-100">Media Asset Metadata</h2>
              <button onClick={() => setSelectedMetadata(null)} className="text-zinc-500 hover:text-zinc-300">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4 text-sm text-zinc-300">
              <div className="aspect-[16/9] bg-zinc-900 rounded-lg overflow-hidden flex items-center justify-center relative border border-white/[0.04]">
                {selectedMetadata.public_url || selectedMetadata.thumbnail_url ? (
                  <NextImage
                    src={selectedMetadata.thumbnail_url ?? selectedMetadata.public_url ?? ""}
                    alt={selectedMetadata.filename}
                    fill
                    className="object-contain"
                    unoptimized
                  />
                ) : (
                  <FileImage className="h-12 w-12 text-zinc-700" />
                )}
              </div>

              <div>
                <span className="text-xs text-zinc-500 block">Filename</span>
                <span className="font-semibold text-zinc-200 break-all">{selectedMetadata.filename}</span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-xs text-zinc-500 block">Asset Type</span>
                  <span className="rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300 font-mono">
                    {selectedMetadata.asset_type}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-zinc-500 block">MIME Type</span>
                  <span className="rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300 font-mono">
                    {selectedMetadata.mime_type}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-zinc-500 block">Storage Provider</span>
                  <span className="text-zinc-200">{selectedMetadata.storage_provider}</span>
                </div>
                <div>
                  <span className="text-xs text-zinc-500 block">File Size</span>
                  <span className="text-zinc-200 font-mono">{formatBytes(selectedMetadata.size_bytes)}</span>
                </div>
              </div>

              <div>
                <span className="text-xs text-zinc-500 block">Storage Key / Path</span>
                <span className="font-mono text-xs text-zinc-400 break-all block p-2 bg-zinc-950 rounded-lg mt-1 border border-white/[0.04]">
                  {selectedMetadata.storage_key ?? "N/A"}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-xs text-zinc-500 block">Source Type</span>
                  <span className="text-zinc-200">{selectedMetadata.source_type}</span>
                </div>
                <div>
                  <span className="text-xs text-zinc-500 block">Created At</span>
                  <span className="text-zinc-200 font-mono">{formatDate(selectedMetadata.created_at)}</span>
                </div>
              </div>

              {selectedMetadata.original_source_url && (
                <div>
                  <span className="text-xs text-zinc-500 block">Original Source URL</span>
                  <a
                    href={selectedMetadata.original_source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-red-400 hover:text-red-300 break-all underline block mt-0.5"
                  >
                    {selectedMetadata.original_source_url}
                  </a>
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedMetadata(null)}
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
