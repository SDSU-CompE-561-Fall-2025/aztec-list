import { queryOptions } from "@tanstack/react-query";

export default function createListingQueryOptions() {
  return queryOptions({
    queryKey: ["listings"],
    queryFn: () => getListings(),
  });

}