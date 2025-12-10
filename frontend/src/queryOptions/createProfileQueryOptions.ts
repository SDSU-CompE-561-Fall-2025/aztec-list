import { queryOptions } from "@tanstack/react-query";
import { getMyProfile } from "@/lib/api";
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
      try {
        return await getMyProfile();
      } catch (error) {
        // Profile doesn't exist yet (404 is expected for users without profiles)
        if (error instanceof Error && error.message.includes("Profile not found")) {
          return null;
        }
        // Authentication errors - return null to handle gracefully
        if (
          error instanceof Error &&
          (error.message.includes("Authentication required") ||
            error.message.includes("Authentication failed"))
        ) {
          return null;
        }
        throw error;
      }
    },
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes("Authentication")) {
        return false;
      }
      return failureCount < 2;
    },
  });
};
