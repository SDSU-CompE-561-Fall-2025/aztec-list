import { queryOptions } from "@tanstack/react-query";
import { getOwnListings } from "@/lib/api";
import type { UserListingsParams } from "@/types/listing/listing";

/**
 * Create query options for fetching user's own listings with authentication
 * This supports include_inactive parameter for viewing hidden listings
 */
export const createOwnListingsQueryOptions = (userId: string, params: UserListingsParams = {}) => {
  return queryOptions({
    queryKey: ["own-listings", userId, params],
    queryFn: () => getOwnListings(userId, params),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};
