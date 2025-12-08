import { queryOptions } from "@tanstack/react-query";
import { API_BASE_URL } from "@/lib/constants";
import { getAuthToken } from "@/lib/auth";
import type { ProfilePublic } from "@/types/user";

/**
 * Create query options for fetching user profile data
 * Returns null only for expected cases: no auth token or profile doesn't exist (404)
 * Throws errors for actual failures to enable proper error handling in components
 */
export const createProfileQueryOptions = (userId: string | undefined) => {
  return queryOptions({
    queryKey: ["profile", userId],
    queryFn: async (): Promise<ProfilePublic | null> => {
      const token = getAuthToken();
      if (!token) return null;

      const response = await fetch(`${API_BASE_URL}/users/profile/`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      // Profile doesn't exist yet (404 is expected for users without profiles)
      if (response.status === 404) return null;

      // Unauthorized - token might be expired or invalid
      if (response.status === 401) {
        throw new Error("Authentication failed. Please log in again.");
      }

      // Other errors should be thrown for proper error handling
      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Failed to fetch profile" }));
        throw new Error(errorData.detail || `Failed to fetch profile: ${response.status}`);
      }

      return response.json();
    },
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes("Authentication failed")) {
        return false;
      }
      return failureCount < 2;
    },
  });
};
