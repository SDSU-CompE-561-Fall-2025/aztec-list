"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAuth?: boolean;
}

/**
 * Protected route wrapper component.
 * Redirects unauthenticated users to login page.
 *
 * @param requireAuth - If true, requires authentication. Default: true
 */
export function ProtectedRoute({ children, requireAuth = true }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && requireAuth && !isAuthenticated) {
      // Redirect to login with current path so user can return after login
      const redirectUrl = `/login?redirect=${encodeURIComponent(pathname)}`;
      router.push(redirectUrl);
    }
  }, [isAuthenticated, isLoading, requireAuth, router, pathname]);

  // Show nothing while checking authentication (Next.js will handle redirect)
  // Each page should implement its own loading skeleton
  if (isLoading || (requireAuth && !isAuthenticated)) {
    return null;
  }

  return <>{children}</>;
}
