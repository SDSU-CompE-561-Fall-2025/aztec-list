"use client";

import { Toaster } from "@/components/ui/sonner";
import { useIsHydrated } from "@/hooks/use-hydrated";

/**
 * Client-only wrapper for Sonner Toaster to avoid hydration issues.
 * Toasts only render on the client after hydration, to prevent mismatches
 * with theme detection.
 */
export function ToasterClient() {
  const isHydrated = useIsHydrated();

  if (!isHydrated) {
    return null;
  }

  return <Toaster />;
}
