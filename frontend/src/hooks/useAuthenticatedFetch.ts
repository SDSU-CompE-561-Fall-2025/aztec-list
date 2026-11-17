/**
 * Custom hook for making authenticated API requests.
 */

import { endSession, getAuthToken } from "@/lib/auth";

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
  options: FetchOptions = {},
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

  // Handle 401 Unauthorized - token expired or invalid: clear auth, then go to login
  if (response.status === 401 && requiresAuth && typeof window !== "undefined") {
    endSession("/login?redirect=" + encodeURIComponent(window.location.pathname));
  }

  return response;
}
