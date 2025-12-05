"use client";

import { useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { LISTINGS_BASE_URL, DEFAULT_SORT } from "@/lib/constants";

interface HeaderProps {
  isSignedIn?: boolean;
  userAvatar?: string;
  userName?: string;
}

export function Header({ isSignedIn = false, userAvatar, userName }: HeaderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = useState("");

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
          <div className="text-2xl font-bold">
            <span className="text-purple-500">Aztec</span>
            <span className="text-white">List</span>
          </div>
          <span className="text-sm text-gray-400">Campus</span>
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
          {!isSignedIn ? (
            <>
              <Button variant="outline" asChild>
                <Link href="/sign-in">Sign In</Link>
              </Button>
              <Button asChild>
                <Link href="/register">Register</Link>
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" asChild>
                <Link href="/settings">Settings</Link>
              </Button>
              <Avatar className="cursor-pointer">
                <AvatarImage src={userAvatar} alt={userName || "User"} />
                <AvatarFallback className="bg-purple-600 text-white">
                  {userName ? userName.charAt(0).toUpperCase() : "U"}
                </AvatarFallback>
              </Avatar>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
