/* eslint-disable */
// @ts-nocheck
"use client";

import { useEffect, useState } from "react";
import { Toaster } from "@/components/ui/sonner";

/**
 * Client-only wrapper for Sonner Toaster to avoid hydration issues.
 * This component ensures toasts only render on the client side after mount
 * to prevent hydration mismatches with theme detection.
 *
 * Note: setMounted in useEffect is intentional for post-mount rendering.
 */
export function ToasterClient() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return <Toaster />;
}
