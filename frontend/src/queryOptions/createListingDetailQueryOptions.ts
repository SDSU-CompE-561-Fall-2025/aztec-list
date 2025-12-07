import { queryOptions } from "@tanstack/react-query";
import { getListing } from "@/lib/api";

export function createListingDetailQueryOptions(listingId: string) {
  return queryOptions({
    queryKey: ["listing", listingId],
    queryFn: () => getListing(listingId),
    retry: 1,
  });
}
