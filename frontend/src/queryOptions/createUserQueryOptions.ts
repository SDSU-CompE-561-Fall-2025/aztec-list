import { getUser } from "@/lib/api";
import { queryOptions } from "@tanstack/react-query";

export const createUserQueryOptions = (userId: string) => {
  return queryOptions({
    queryKey: ["user", userId],
    queryFn: () => getUser(userId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};
