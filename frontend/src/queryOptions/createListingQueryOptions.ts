import { getListings } from "@/lib/api";
import { queryOptions } from "@tanstack/react-query";
import { listingParams } from "@/types/listing/listingParams";

export default function createListingQueryOptions(filters: listingParams) {
  return queryOptions({
    queryKey: ["listings", filters],
    queryFn: () => getListings(filters),
  });
}