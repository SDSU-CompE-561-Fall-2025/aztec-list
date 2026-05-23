import { queryOptions } from "@tanstack/react-query";
import { getSimilarListings } from "@/lib/api";

export function createSimilarListingsQueryOptions(listingId: string) {
  return queryOptions({
    queryKey: ["listing", listingId, "similar"],
    queryFn: () => getSimilarListings(listingId),
    enabled: !!listingId,
  });
}
