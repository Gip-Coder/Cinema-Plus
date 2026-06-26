"use client";

import { useState, useEffect, useTransition } from "react";
import { User as UserIcon, Mail, Lock, Shield, Loader2, CheckCircle2, AlertCircle, Bell, Sparkles, Image as ImageIcon, Check } from "lucide-react";
import { authApi } from "@/lib/api/auth";
import { useAuth } from "@/hooks/use-auth";

const PRESET_AVATARS = [
  "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150", // Movie Fan
  "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150", // Cinephile
  "https://images.unsplash.com/photo-1599566150163-29194dcaad36?w=150", // Director
  "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150", // Critic
  "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150", // Screenwriter
];

const GENRES_LIST = ["Action", "Comedy", "Drama", "Sci-Fi", "Thriller", "Horror", "Romance", "Documentary", "Animation"];

export default function ProfilePage() {
  const { user, accessToken, setUser } = useAuth();

  // Profile fields state
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [isProfilePending, startProfileTransition] = useTransition();

  // Password fields state
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passSuccess, setPassSuccess] = useState<string | null>(null);
  const [passError, setPassError] = useState<string | null>(null);
  const [isPassPending, startPassTransition] = useTransition();

  // Avatar states
  const [selectedAvatar, setSelectedAvatar] = useState("");
  
  // Notification states
  const [notifications, setNotifications] = useState({
    email: true,
    sms: false,
    push: true
  });

  // Personalization preferences
  const [prefTheatre, setPrefTheatre] = useState("Downtown Luxe Screen 1");
  const [prefSeat, setPrefSeat] = useState("Executive");
  const [prefLanguage, setPrefLanguage] = useState("English");
  const [selectedGenres, setSelectedGenres] = useState<string[]>(["Action", "Sci-Fi"]);

  const [prefsSuccess, setPrefsSuccess] = useState<string | null>(null);

  // Sync initial state when user is loaded
  useEffect(() => {
    if (user) {
      setUsername(user.username ?? "");
      setEmail(user.email ?? "");
    }
  }, [user]);

  // Load from local storage on mount
  useEffect(() => {
    const cachedAvatar = localStorage.getItem("cinema_plus_avatar");
    if (cachedAvatar) {
      setSelectedAvatar(cachedAvatar);
    } else {
      setSelectedAvatar(PRESET_AVATARS[0]);
    }

    const cachedNotifs = localStorage.getItem("cinema_plus_notification_prefs");
    if (cachedNotifs) {
      try {
        setNotifications(JSON.parse(cachedNotifs));
      } catch {}
    }

    const cachedPrefs = localStorage.getItem("cinema_plus_profile_prefs");
    if (cachedPrefs) {
      try {
        const parsed = JSON.parse(cachedPrefs);
        setPrefTheatre(parsed.preferredTheatre || "Downtown Luxe Screen 1");
        setPrefSeat(parsed.preferredSeatCategory || "Executive");
        setPrefLanguage(parsed.preferredLanguage || "English");
        setSelectedGenres(parsed.preferredGenres || ["Action", "Sci-Fi"]);
      } catch {}
    }
  }, []);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileSuccess(null);
    setProfileError(null);

    if (!username.trim() || !email.trim()) {
      setProfileError("Username and Email fields cannot be empty.");
      return;
    }

    if (!accessToken) {
      setProfileError("Session expired. Please log in again.");
      return;
    }

    startProfileTransition(async () => {
      try {
        const updatedUser = await authApi.updateProfile(accessToken, { username, email });
        setUser(updatedUser);
        setProfileSuccess("Profile updated successfully!");
      } catch (err: unknown) {
        if (err instanceof Error) {
          setProfileError(err.message || "Failed to update profile details.");
        } else {
          setProfileError("Failed to update profile.");
        }
      }
    });
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPassSuccess(null);
    setPassError(null);

    if (!oldPassword || !newPassword || !confirmPassword) {
      setPassError("All password fields are required.");
      return;
    }

    if (newPassword.length < 6) {
      setPassError("New password must be at least 6 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setPassError("New passwords do not match.");
      return;
    }

    if (!accessToken) {
      setPassError("Session expired. Please log in again.");
      return;
    }

    startPassTransition(async () => {
      try {
        await authApi.changePassword(accessToken, oldPassword, newPassword);
        setPassSuccess("Password updated successfully!");
        setOldPassword("");
        setNewPassword("");
        setConfirmPassword("");
      } catch (err: unknown) {
        if (err instanceof Error) {
          setPassError(err.message || "Failed to change password. Double check your old password.");
        } else {
          setPassError("Failed to update password.");
        }
      }
    });
  };

  // Save Preferences to LocalStorage
  const handleSavePreferences = (e: React.FormEvent) => {
    e.preventDefault();
    setPrefsSuccess(null);

    // Save avatar
    localStorage.setItem("cinema_plus_avatar", selectedAvatar);
    
    // Save notification preferences
    localStorage.setItem("cinema_plus_notification_prefs", JSON.stringify(notifications));

    // Save personalization tastes
    const profilePrefs = {
      preferredTheatre: prefTheatre,
      preferredSeatCategory: prefSeat,
      preferredLanguage: prefLanguage,
      preferredGenres: selectedGenres
    };
    localStorage.setItem("cinema_plus_profile_prefs", JSON.stringify(profilePrefs));

    setPrefsSuccess("Preferences saved successfully!");
    setTimeout(() => setPrefsSuccess(null), 3000);
  };

  // Handle custom image upload base64 conversion
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = () => {
      if (typeof reader.result === "string") {
        setSelectedAvatar(reader.result);
      }
    };
    reader.readAsDataURL(file);
  };

  const toggleGenre = (genre: string) => {
    setSelectedGenres(prev => 
      prev.includes(genre) ? prev.filter(g => g !== genre) : [...prev, genre]
    );
  };

  return (
    <div className="container max-w-5xl mx-auto px-4 py-8 md:py-12 text-zinc-100">
      <h1 className="text-3xl font-extrabold tracking-tight text-white mb-8 border-l-4 border-red-600 pl-4">
        My Profile Settings
      </h1>

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Left Column: Avatar & Prefs */}
        <div className="lg:col-span-1 space-y-6">
          
          {/* Avatar Settings */}
          <div className="rounded-xl border border-white/[0.06] bg-zinc-950/50 p-6 shadow-xl backdrop-blur-md text-center space-y-4">
            <h2 className="text-base font-bold text-white flex items-center justify-center gap-2 border-b border-white/[0.04] pb-3">
              <ImageIcon className="h-4 w-4 text-red-500" />
              Profile Avatar
            </h2>

            {/* Avatar Display */}
            <div className="relative inline-block">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={selectedAvatar || PRESET_AVATARS[0]}
                alt="Avatar"
                className="h-28 w-28 rounded-full border-4 border-red-600 object-cover mx-auto shadow-lg"
              />
              <label htmlFor="avatar-file" className="absolute bottom-0 right-2 p-1.5 rounded-full bg-red-600 hover:bg-red-700 text-white cursor-pointer shadow-md select-none border border-zinc-900">
                <ImageIcon className="h-3.5 w-3.5" />
                <input id="avatar-file" type="file" accept="image/*" onChange={handleImageUpload} className="hidden" />
              </label>
            </div>

            <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Choose preset or upload custom</p>
            
            {/* Presets Grid */}
            <div className="flex items-center justify-center gap-2 flex-wrap">
              {PRESET_AVATARS.map((url, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedAvatar(url)}
                  className={`h-10 w-10 rounded-full overflow-hidden border-2 transition-all relative ${
                    selectedAvatar === url ? "border-red-500 scale-105" : "border-transparent opacity-60 hover:opacity-100"
                  }`}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={url} alt={`Preset ${idx}`} className="h-full w-full object-cover" />
                  {selectedAvatar === url && (
                    <div className="absolute inset-0 bg-red-600/20 flex items-center justify-center text-white">
                      <Check className="h-4 w-4 stroke-[3]" />
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Account Overview details */}
          <div className="rounded-xl border border-white/[0.06] bg-zinc-950/50 p-6 shadow-xl backdrop-blur-md space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-white/[0.04] pb-3">
              <Shield className="h-4 w-4 text-red-500" />
              Account Metadata
            </h2>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between">
                <span className="text-zinc-500">Membership Tier:</span>
                <span className="font-bold text-amber-400">Gold Club VIP</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Points Balance:</span>
                <span className="font-bold text-zinc-200">450 pts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Joined Date:</span>
                <span className="font-bold text-zinc-300">June 2026</span>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column: Preferences, details, password */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Details & Preferences form combined */}
          <div className="rounded-xl border border-white/[0.06] bg-zinc-950/50 p-6 shadow-xl backdrop-blur-md">
            
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <UserIcon className="h-5 w-5 text-red-500" />
              Account Details
            </h2>

            {profileSuccess && (
              <div className="mb-4 flex items-center gap-2 rounded-lg border border-green-500/20 bg-green-500/10 p-3 text-sm text-green-400">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>{profileSuccess}</span>
              </div>
            )}

            {profileError && (
              <div className="mb-4 flex items-center gap-2 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{profileError}</span>
              </div>
            )}

            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="p-username" className="block text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Username
                  </label>
                  <div className="relative mt-1">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                      <UserIcon className="h-4 w-4 text-gray-500" />
                    </div>
                    <input
                      id="p-username"
                      type="text"
                      required
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="block w-full rounded-lg border border-white/[0.08] bg-zinc-900/30 py-2.5 pl-9 pr-3 text-sm text-white focus:border-red-600 focus:outline-none focus:ring-1 focus:ring-red-600"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="p-email" className="block text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Email Address
                  </label>
                  <div className="relative mt-1">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                      <Mail className="h-4 w-4 text-gray-500" />
                    </div>
                    <input
                      id="p-email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="block w-full rounded-lg border border-white/[0.08] bg-zinc-900/30 py-2.5 pl-9 pr-3 text-sm text-white focus:border-red-600 focus:outline-none focus:ring-1 focus:ring-red-600"
                    />
                  </div>
                </div>
              </div>

              <div>
                <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Account Role
                </span>
                <div className="relative mt-1">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <Shield className="h-4 w-4 text-gray-500" />
                  </div>
                  <input
                    type="text"
                    disabled
                    value={user?.role ?? "customer"}
                    className="block w-full rounded-lg border border-white/[0.04] bg-zinc-900/20 py-2.5 pl-9 pr-3 text-sm text-gray-500 capitalize select-none cursor-not-allowed"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isProfilePending}
                className="flex items-center justify-center rounded-lg bg-red-600 px-6 py-2.5 text-sm font-bold text-white shadow-sm hover:bg-red-700 focus:outline-none active:scale-95 disabled:opacity-50 disabled:pointer-events-none transition-all ml-auto"
              >
                {isProfilePending ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Saving Account Info...</span>
                  </div>
                ) : (
                  "Update Account Info"
                )}
              </button>
            </form>
          </div>

          {/* Preferences & Personalization Form (LocalStorage) */}
          <div className="rounded-xl border border-white/[0.06] bg-zinc-950/50 p-6 shadow-xl backdrop-blur-md">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-red-500" />
              Spotlight Tastes & Personalization
            </h2>

            {prefsSuccess && (
              <div className="mb-4 flex items-center gap-2 rounded-lg border border-green-500/20 bg-green-500/10 p-3 text-sm text-green-400">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>{prefsSuccess}</span>
              </div>
            )}

            <form onSubmit={handleSavePreferences} className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <label htmlFor="pref-theatre" className="block text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Preferred Theatre
                  </label>
                  <select
                    id="pref-theatre"
                    value={prefTheatre}
                    onChange={(e) => setPrefTheatre(e.target.value)}
                    className="block w-full rounded-lg border border-white/[0.08] bg-zinc-900/30 mt-1 py-2.5 px-3 text-xs text-white focus:border-red-600 focus:outline-none focus:ring-1 focus:ring-red-600"
                  >
                    <option value="Downtown Luxe Screen 1">Downtown Luxe Screen 1</option>
                    <option value="Uptown Cineplex Screen 4">Uptown Cineplex Screen 4</option>
                    <option value="Mall Multiplex Screen 3">Mall Multiplex Screen 3</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="pref-seat" className="block text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Preferred Seat Category
                  </label>
                  <select
                    id="pref-seat"
                    value={prefSeat}
                    onChange={(e) => setPrefSeat(e.target.value)}
                    className="block w-full rounded-lg border border-white/[0.08] bg-zinc-900/30 mt-1 py-2.5 px-3 text-xs text-white focus:border-red-600 focus:outline-none focus:ring-1 focus:ring-red-600"
                  >
                    <option value="Normal">Normal (Budget)</option>
                    <option value="Executive">Executive (Standard)</option>
                    <option value="Premium">Premium (Luxury Recliner)</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="pref-lang" className="block text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Preferred Language
                  </label>
                  <select
                    id="pref-lang"
                    value={prefLanguage}
                    onChange={(e) => setPrefLanguage(e.target.value)}
                    className="block w-full rounded-lg border border-white/[0.08] bg-zinc-900/30 mt-1 py-2.5 px-3 text-xs text-white focus:border-red-600 focus:outline-none focus:ring-1 focus:ring-red-600"
                  >
                    <option value="English">English</option>
                    <option value="Spanish">Spanish</option>
                    <option value="French">French</option>
                    <option value="Japanese">Japanese</option>
                  </select>
                </div>
              </div>

              {/* Genre Selector */}
              <div className="space-y-2">
                <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Favorite Genres
                </span>
                <div className="flex flex-wrap gap-2">
                  {GENRES_LIST.map((genre) => {
                    const isSelected = selectedGenres.includes(genre);
                    return (
                      <button
                        type="button"
                        key={genre}
                        onClick={() => toggleGenre(genre)}
                        className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all border ${
                          isSelected
                            ? "bg-red-600 border-red-500 text-white shadow-md"
                            : "bg-white/[0.01] border-white/[0.06] text-zinc-400 hover:border-white/[0.12] hover:text-zinc-200"
                        }`}
                      >
                        {genre}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Notification Preferences */}
              <div className="space-y-3 border-t border-white/[0.04] pt-4">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1">
                  <Bell className="h-4 w-4 text-red-500" />
                  Notification Preferences
                </h3>
                
                <div className="grid gap-3 sm:grid-cols-3">
                  <label className="flex items-center gap-2.5 p-3 rounded-xl border border-white/[0.04] bg-white/[0.005] hover:bg-white/[0.015] cursor-pointer transition-colors text-xs font-semibold text-zinc-300">
                    <input
                      type="checkbox"
                      checked={notifications.email}
                      onChange={(e) => setNotifications(prev => ({ ...prev, email: e.target.checked }))}
                      className="rounded border-white/[0.12] bg-zinc-900 text-red-600 focus:ring-red-600 focus:ring-offset-zinc-950"
                    />
                    <span>Email Bookings</span>
                  </label>

                  <label className="flex items-center gap-2.5 p-3 rounded-xl border border-white/[0.04] bg-white/[0.005] hover:bg-white/[0.015] cursor-pointer transition-colors text-xs font-semibold text-zinc-300">
                    <input
                      type="checkbox"
                      checked={notifications.sms}
                      onChange={(e) => setNotifications(prev => ({ ...prev, sms: e.target.checked }))}
                      className="rounded border-white/[0.12] bg-zinc-900 text-red-600 focus:ring-red-600 focus:ring-offset-zinc-950"
                    />
                    <span>SMS Reminders</span>
                  </label>

                  <label className="flex items-center gap-2.5 p-3 rounded-xl border border-white/[0.04] bg-white/[0.005] hover:bg-white/[0.015] cursor-pointer transition-colors text-xs font-semibold text-zinc-300">
                    <input
                      type="checkbox"
                      checked={notifications.push}
                      onChange={(e) => setNotifications(prev => ({ ...prev, push: e.target.checked }))}
                      className="rounded border-white/[0.12] bg-zinc-900 text-red-600 focus:ring-red-600 focus:ring-offset-zinc-950"
                    />
                    <span>Push Alerts</span>
                  </label>
                </div>
              </div>

              <button
                type="submit"
                className="flex items-center justify-center rounded-lg bg-red-600 px-6 py-2.5 text-sm font-bold text-white shadow-sm hover:bg-red-700 focus:outline-none active:scale-95 transition-all ml-auto"
              >
                Save Preferences
              </button>
            </form>
          </div>

          {/* Change Password Card */}
          <div className="rounded-xl border border-white/[0.06] bg-zinc-950/50 p-6 shadow-xl backdrop-blur-md">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Lock className="h-5 w-5 text-red-500" />
              Security & Password
            </h2>

            {passSuccess && (
              <div className="mb-4 flex items-center gap-2 rounded-lg border border-green-500/20 bg-green-500/10 p-3 text-sm text-green-400">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>{passSuccess}</span>
              </div>
            )}

            {passError && (
              <div className="mb-4 flex items-center gap-2 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{passError}</span>
              </div>
            )}

            <form onSubmit={handleChangePassword} className="space-y-4">
              <div>
                <label htmlFor="old-pass" className="block text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Current Password
                </label>
                <div className="relative mt-1">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <Lock className="h-4 w-4 text-gray-500" />
                  </div>
                  <input
                    id="old-pass"
                    type="password"
                    required
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    className="block w-full rounded-lg border border-white/[0.08] bg-zinc-900/30 py-2.5 pl-9 pr-3 text-sm text-white focus:border-red-600 focus:outline-none focus:ring-1 focus:ring-red-600"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="new-pass" className="block text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    New Password
                  </label>
                  <div className="relative mt-1">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                      <Lock className="h-4 w-4 text-gray-500" />
                    </div>
                    <input
                      id="new-pass"
                      type="password"
                      required
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="block w-full rounded-lg border border-white/[0.08] bg-zinc-900/30 py-2.5 pl-9 pr-3 text-sm text-white focus:border-red-600 focus:outline-none focus:ring-1 focus:ring-red-600"
                      placeholder="••••••••"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="confirm-pass" className="block text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Confirm New Password
                  </label>
                  <div className="relative mt-1">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                      <Lock className="h-4 w-4 text-gray-500" />
                    </div>
                    <input
                      id="confirm-pass"
                      type="password"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="block w-full rounded-lg border border-white/[0.08] bg-zinc-900/30 py-2.5 pl-9 pr-3 text-sm text-white focus:border-red-600 focus:outline-none focus:ring-1 focus:ring-red-600"
                      placeholder="••••••••"
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={isPassPending}
                className="flex items-center justify-center rounded-lg bg-red-600 px-6 py-2.5 text-sm font-bold text-white shadow-sm hover:bg-red-700 focus:outline-none active:scale-95 disabled:opacity-50 disabled:pointer-events-none transition-all ml-auto"
              >
                {isPassPending ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Updating...</span>
                  </div>
                ) : (
                  "Update Password"
                )}
              </button>
            </form>
          </div>

        </div>
      </div>
    </div>
  );
}
