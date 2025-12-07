/* eslint-disable */
// @ts-nocheck
"use client";

import { useEffect, useState } from "react";
import { Header } from "./header";

/**
 * Client-only wrapper for Header to prevent hydration issues.
 * Renders a loading skeleton during SSR, then shows the actual header on client.
 *
 * Note: setMounted in useEffect is intentional for post-mount rendering.
 */
export function HeaderClient() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <header className="sticky top-0 z-50 w-full border-b border-gray-800 bg-gray-950">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 gap-4">
          <div className="flex items-center gap-2">
            <div className="text-3xl font-bold">
              <span className="text-purple-500">Aztec</span>
              <span className="text-white">List</span>
            </div>
            <span className="text-base text-gray-400">Campus</span>
          </div>
          <div className="flex-1 max-w-2xl">
            <div className="h-10 bg-gray-900 border border-gray-700 rounded-md" />
          </div>
          <div className="flex items-center gap-3">
            <div className="h-9 w-16 bg-gray-800 rounded animate-pulse" />
            <div className="h-9 w-20 bg-gray-800 rounded animate-pulse" />
          </div>
        </div>
      </header>
    );
  }

  return <Header />;
}
