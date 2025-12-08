import { queryOptions } from "@tanstack/react-query";
import { API_BASE_URL } from "@/lib/constants";
import { getAuthToken } from "@/lib/auth";
import type { ProfilePublic } from "@/types/user";

/**
 * Create query options for fetching user profile data
 * Returns null if profile doesn't exist (404) or user is not authenticated
 */
export const createProfileQueryOptions = (userId: string | undefined) => {
  return queryOptions({
    queryKey: ["profile", userId],
    queryFn: async (): Promise<ProfilePublic | null> => {
      const token = getAuthToken();
      if (!token) return null;

      try {
        const response = await fetch(`${API_BASE_URL}/users/profile/`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        // Profile doesn't exist yet (404 is acceptable)
        if (response.status === 404) return null;

        if (!response.ok) {
          // Return null instead of throwing to prevent console errors
          return null;
        }

        return response.json();
      } catch (error) {
        // Silently handle errors and return null
        return null;
      }
    },
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
  });
};
