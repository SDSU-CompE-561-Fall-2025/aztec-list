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
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 gap-4">
          <div className="flex items-center gap-2">
            <div className="text-2xl font-bold">
              <span className="text-purple-500">Aztec</span>
              <span className="text-foreground">List</span>
            </div>
          </div>
          <div className="flex-1 max-w-2xl" />
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-muted rounded-full animate-pulse" />
          </div>
        </div>
      </header>
    );
  }

  return <Header />;
}
