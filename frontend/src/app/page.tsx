"use client";

import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Search } from "@/components/custom/search";
import createListingQueryOptions from "@/queryOptions/createListingQueryOptions";

export default function ListingsPage() {
  const searchParams = useSearchParams();

  const filters = {
    q: searchParams.get("q") ?? "",
  };

  const query = createListingQueryOptions(filters);
  const { data } = useQuery(query);

  return (
    <div>
      <Search />
      <div>{JSON.stringify(data)}</div>
    </div>
  );
}
