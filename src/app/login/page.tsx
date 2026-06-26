"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, useTransition, Suspense } from "react";
import { Film, Lock, User as UserIcon, Loader2, AlertCircle } from "lucide-react";
import { authApi } from "@/lib/api/auth";
import { useAuthStore } from "@/stores/auth-store";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const loginStore = useAuthStore((state) => state.login);
  
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!username.trim() || !password.trim()) {
      setError("Please fill in all fields.");
      return;
    }

    startTransition(async () => {
      try {
        const token = await authApi.login({ username, password });
        // Fetch current user details
        const userDetails = await authApi.me(token.access_token);
        
        loginStore(token, userDetails);
        
        // Redirect logic
        const redirectUrl = searchParams.get("from") || (userDetails.role === "admin" ? "/admin" : "/");
        router.push(redirectUrl);
        router.refresh();
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message || "Invalid username or password.");
        } else {
          setError("Failed to connect. Please ensure the backend is running.");
        }
      }
    });
  };

  return (
    <div className="flex min-h-[calc(100vh-8rem)] flex-col items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-border/40 bg-zinc-950/80 p-8 shadow-2xl backdrop-blur-md">
        
        {/* Brand/Header */}
        <div className="flex flex-col items-center justify-center text-center">
          <Film className="h-10 w-10 text-red-600 mb-2" />
          <h2 className="text-3xl font-extrabold tracking-tight text-white">
            Welcome Back
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Sign in to your Cinema Plus account
          </p>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="flex items-center gap-3 rounded-lg border border-destructive/20 bg-destructive/10 p-4 text-sm text-destructive">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-300">
                Username
              </label>
              <div className="relative mt-1">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <UserIcon className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="block w-full rounded-lg border border-border bg-zinc-900/50 py-3 pl-10 pr-3 text-white placeholder-gray-500 focus:border-red-600 focus:outline-none focus:ring-1 focus:ring-red-600 sm:text-sm"
                  placeholder="admin"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300">
                Password
              </label>
              <div className="relative mt-1">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <Lock className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full rounded-lg border border-border bg-zinc-900/50 py-3 pl-10 pr-3 text-white placeholder-gray-500 focus:border-red-600 focus:outline-none focus:ring-1 focus:ring-red-600 sm:text-sm"
                  placeholder="••••••••"
                />
              </div>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isPending}
              className="flex w-full justify-center rounded-lg bg-red-600 py-3 px-4 text-sm font-bold text-white shadow-sm hover:bg-red-700 focus:outline-none active:scale-95 disabled:opacity-50 disabled:pointer-events-none transition-all"
            >
              {isPending ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Logging in...</span>
                </div>
              ) : (
                "Sign In"
              )}
            </button>
          </div>
        </form>

        {/* Signup Link */}
        <div className="text-center text-sm">
          <span className="text-muted-foreground">Don&apos;t have an account? </span>
          <Link href="/register" className="font-semibold text-red-500 hover:text-red-400">
            Sign up now
          </Link>
        </div>

      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-[calc(100vh-8rem)] flex-col items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
        <div className="w-full max-w-md space-y-8 rounded-2xl border border-border/40 bg-zinc-950/80 p-8 shadow-2xl backdrop-blur-md flex items-center justify-center min-h-[400px]">
          <Loader2 className="h-8 w-8 animate-spin text-red-600" />
        </div>
      </div>
    }>
      <LoginForm />
    </Suspense>
  );
}
