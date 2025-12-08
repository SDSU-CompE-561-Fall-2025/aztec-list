"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LISTINGS_BASE_URL, DEFAULT_SORT, API_BASE_URL, STATIC_BASE_URL } from "@/lib/constants";
import { useAuth } from "@/contexts/AuthContext";
import { getAuthToken } from "@/lib/auth";
import { LogOut, Settings, User } from "lucide-react";

// Helper function to build full URL for profile picture
const getProfilePictureUrl = (path: string | null | undefined): string | null => {
  if (!path) return null;
  const timestamp = Date.now();
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return `${path}?t=${timestamp}`;
  }
  return `${STATIC_BASE_URL}${path}?t=${timestamp}`;
};

export function Header() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [profilePicture, setProfilePicture] = useState<string | null>(null);

  // Fetch profile picture when user is authenticated
  useEffect(() => {
    const fetchProfile = async () => {
      if (!isAuthenticated) {
        setProfilePicture(null);
        return;
      }

      try {
        const token = getAuthToken();
        if (!token) return;

        const response = await fetch(`${API_BASE_URL}/users/profile/`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const profile = await response.json();
          setProfilePicture(profile.profile_picture_url);
        } else if (response.status === 404) {
          // User doesn't have a profile yet, that's okay - silently skip
          setProfilePicture(null);
        } else if (response.status === 422) {
          // Validation error - should not happen now with correct URL
          setProfilePicture(null);
        } else {
          const errorData = await response.json().catch(() => ({}));
          console.error("Profile fetch error:", response.status, errorData);
        }
      } catch (error) {
        console.error("Failed to fetch profile:", error);
      }
    };

    fetchProfile();

    // Refresh profile picture every 10 seconds to detect updates
    const intervalId = setInterval(fetchProfile, 10000);

    return () => clearInterval(intervalId);
  }, [isAuthenticated]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();

    // Trim whitespace from the search query
    const trimmedQuery = searchQuery.trim();

    if (!trimmedQuery) {
      // If empty, just navigate to listings without search
      router.push(`${LISTINGS_BASE_URL}?sort=${DEFAULT_SORT}`);
      return;
    }

    // encodeURIComponent properly handles all special characters for URLs
    // Backend handles SQL injection protection via parameterized queries
    const isOnListingsPage = pathname === LISTINGS_BASE_URL;

    if (isOnListingsPage) {
      // If already on listings page, update the URL with new search
      router.replace(
        `${LISTINGS_BASE_URL}?q=${encodeURIComponent(trimmedQuery)}&sort=${DEFAULT_SORT}`
      );
    } else {
      // If on home page or elsewhere, navigate to listings
      router.push(
        `${LISTINGS_BASE_URL}?q=${encodeURIComponent(trimmedQuery)}&sort=${DEFAULT_SORT}`
      );
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-gray-800 bg-gray-950">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 gap-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="text-3xl font-bold">
            <span className="text-purple-500">Aztec</span>
            <span className="text-white">List</span>
          </div>
          <span className="text-base text-gray-400">Campus</span>
        </Link>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex-1 max-w-2xl">
          <Input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-gray-900 border-gray-700 text-gray-100 placeholder:text-gray-500"
          />
        </form>

        {/* Auth Buttons / User Menu */}
        <div className="flex items-center gap-3">
          {isLoading ? (
            // Show placeholder while checking auth to avoid hydration mismatch
            <div className="flex items-center gap-3">
              <div className="h-9 w-16 bg-gray-800 rounded animate-pulse" />
              <div className="h-9 w-20 bg-gray-800 rounded animate-pulse" />
            </div>
          ) : !isAuthenticated ? (
            <>
              <Button variant="outline" asChild>
                <Link href="/login">Login</Link>
              </Button>
              <Button asChild>
                <Link href="/signup">Sign Up</Link>
              </Button>
            </>
          ) : (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Avatar className="cursor-pointer">
                  <AvatarImage
                    src={getProfilePictureUrl(profilePicture) || undefined}
                    alt={user?.username || "User"}
                  />
                  <AvatarFallback className="bg-purple-600 text-white">
                    {user?.username ? user.username.charAt(0).toUpperCase() : "U"}
                  </AvatarFallback>
                </Avatar>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-60">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1 py-0.5">
                    <p className="text-sm font-semibold leading-none">{user?.username}</p>
                    <p className="text-xs leading-none text-muted-foreground">{user?.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/profile" className="cursor-pointer py-2">
                    <User className="mr-2 h-4 w-4" />
                    <span className="text-sm">Profile</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href="/settings" className="cursor-pointer py-2">
                    <Settings className="mr-2 h-4 w-4" />
                    <span className="text-sm">Settings</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="cursor-pointer py-2">
                  <LogOut className="mr-2 h-4 w-4" />
                  <span className="text-sm">Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </header>
  );
}
