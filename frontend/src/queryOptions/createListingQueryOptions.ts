import { getListings } from "@/lib/api";
import { queryOptions } from "@tanstack/react-query";
import { ListingsParams } from "@/types/listing/listingParams";

export const createListingQueryOptions = (filters: ListingsParams) => {
  return queryOptions({
    queryKey: ["listings", filters],
    queryFn: () => getListings(filters),
  });
};
