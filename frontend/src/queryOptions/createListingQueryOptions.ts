import { getListings } from "@/lib/api";
import { queryOptions } from "@tanstack/react-query";
import { listingParams } from "@/types/listingParams";

export default function createListingQueryOptions(filters: listingParams) {
  return queryOptions({
    queryKey: ["listings", filters],
    queryFn: () => getListings(filters),
  });

}