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
            <div className="text-2xl font-bold">
              <span className="text-purple-500">Aztec</span>
              <span className="text-white">List</span>
            </div>
          </div>
          <div className="flex-1 max-w-2xl">
            <div className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 bg-gray-700 rounded" />
              <div className="w-full h-9 bg-gray-900 border border-gray-700 rounded-md pl-10 pr-3" />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gray-800 rounded-full animate-pulse" />
          </div>
        </div>
      </header>
    );
  }

  return <Header />;
}
