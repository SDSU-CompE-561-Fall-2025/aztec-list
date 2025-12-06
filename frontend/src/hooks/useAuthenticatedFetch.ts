/**
 * Custom hook for making authenticated API requests.
 */

import { getAuthToken, removeAuthToken, removeStoredUser } from "@/lib/auth";

interface FetchOptions extends RequestInit {
  requiresAuth?: boolean;
}

/**
 * Fetch wrapper that automatically includes authentication token.
 * Handles 401 responses by clearing auth data and redirecting to login.
 *
 * @param url - The URL to fetch
 * @param options - Fetch options, including requiresAuth flag
 * @returns Response promise
 */
export async function authenticatedFetch(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { requiresAuth = false, headers, ...restOptions } = options;

  const requestHeaders = new Headers(headers);

  // Add authorization header if auth is required
  if (requiresAuth) {
    const token = getAuthToken();
    if (token) {
      requestHeaders.set("Authorization", `Bearer ${token}`);
    }
  }

  const response = await fetch(url, {
    ...restOptions,
    headers: requestHeaders,
  });

  // Handle 401 Unauthorized - token expired or invalid
  if (response.status === 401 && requiresAuth) {
    // Clear auth data
    removeAuthToken();
    removeStoredUser();

    // Redirect to login page
    if (typeof window !== "undefined") {
      window.location.href = "/login?redirect=" + encodeURIComponent(window.location.pathname);
    }
  }

  return response;
}
