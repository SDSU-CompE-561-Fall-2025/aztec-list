"use client";

import dynamic from "next/dynamic";

// Import Header with SSR disabled to prevent hydration mismatches
export const HeaderClient = dynamic(
  () => import("./header").then((mod) => ({ default: mod.Header })),
  {
    ssr: false,
    loading: () => (
      <header className="sticky top-0 z-50 w-full border-b border-gray-800 bg-gray-950">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 gap-4">
          <div className="flex items-center gap-2">
            <div className="text-2xl font-bold">
              <span className="text-purple-500">Aztec</span>
              <span className="text-white">List</span>
            </div>
            <span className="text-sm text-gray-400">Campus</span>
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
    ),
  }
);
