"use client";

import { useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
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
import { LISTINGS_BASE_URL, DEFAULT_SORT } from "@/lib/constants";
import { useAuth } from "@/contexts/AuthContext";
import { LogOut, Settings, User, Search, Shield, Mail } from "lucide-react";
import { createProfileQueryOptions } from "@/queryOptions/createProfileQueryOptions";
import { getProfilePictureUrl } from "@/lib/profile-picture";
import { ThemeSwitcher } from "@/components/custom/theme-switcher";

export function Header() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch profile data using React Query
  const { data: profileData } = useQuery(createProfileQueryOptions(user?.id));

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
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 gap-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="text-2xl font-bold">
            <span className="text-purple-500">Aztec</span>
            <span className="text-foreground">List</span>
          </div>
        </Link>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex-1 max-w-2xl">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10"
            />
          </div>
        </form>

        {/* Auth Buttons / User Menu */}
        <div className="flex items-center gap-3">
          <ThemeSwitcher />
          {isLoading ? (
            // Show placeholder while checking auth to avoid hydration mismatch
            <div className="flex items-center gap-3">
              <div className="h-9 w-16 bg-muted rounded animate-pulse" />
              <div className="h-9 w-20 bg-muted rounded animate-pulse" />
            </div>
          ) : !isAuthenticated ? (
            <>
              <Button variant="outline" asChild>
                <Link href="/login">Login</Link>
              </Button>
              <Button asChild className="bg-purple-600 text-white hover:bg-purple-700">
                <Link href="/signup">Sign Up</Link>
              </Button>
            </>
          ) : (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Avatar className="cursor-pointer">
                  <AvatarImage
                    src={
                      getProfilePictureUrl(
                        profileData?.profile_picture_url,
                        profileData?.updated_at
                      ) || undefined
                    }
                    alt={user?.username || "User"}
                  />
                  <AvatarFallback className="bg-purple-600 text-white">
                    {user?.username ? user.username.charAt(0).toUpperCase() : "U"}
                  </AvatarFallback>
                </Avatar>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" sideOffset={8} className="w-56">
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
                <DropdownMenuItem asChild>
                  <Link href="/support" className="cursor-pointer py-2">
                    <Mail className="mr-2 h-4 w-4" />
                    <span className="text-sm">Contact Support</span>
                  </Link>
                </DropdownMenuItem>
                {user?.role === "admin" && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem asChild>
                      <Link href="/admin" className="cursor-pointer py-2 text-purple-400">
                        <Shield className="mr-2 h-4 w-4" />
                        <span className="text-sm font-semibold">Admin Dashboard</span>
                      </Link>
                    </DropdownMenuItem>
                  </>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="cursor-pointer py-2">
                  <LogOut className="mr-2 h-4 w-4 text-red-600 dark:text-red-400" />
                  <span className="text-sm text-red-600 dark:text-red-400">Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </header>
  );
}
