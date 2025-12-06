import { getUserListings } from "@/lib/api";
import { queryOptions } from "@tanstack/react-query";
import { UserListingsParams } from "@/types/listing/userListingsParams";

export const createUserListingsQueryOptions = (userId: string, params: UserListingsParams) => {
  return queryOptions({
    queryKey: ["user-listings", userId, params],
    queryFn: () => getUserListings(userId, params),
  });
};
