"use client";

import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { createListingQueryOptions } from "@/queryOptions/createListingQueryOptions";
import { SearchResults } from "@/components/listings/SearchResults";
import { PaginationControls } from "@/components/listings/PaginationControls";
import { ErrorState } from "@/components/custom/ErrorState";
import { DEFAULT_SORT, DEFAULT_LIMIT } from "@/lib/constants";
import { ListingsParams } from "@/types/listing/listingParams";

export default function HomePage() {
  const searchParams = useSearchParams();

  // Use default parameters for landing page, but read offset from URL for pagination
  const filters: ListingsParams = {
    sort: DEFAULT_SORT,
    limit: DEFAULT_LIMIT,
    offset: parseInt(searchParams.get("offset") ?? "0", 10) || 0,
  };

  // Use TanStack Query to fetch listings
  const { data, isLoading, isError, error } = useQuery(createListingQueryOptions(filters));

  if (isError) {
    return <ErrorState error={error} showHero />;
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto">
        {/* Hero Section */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold mb-3">
            Welcome to <span className="text-purple-500">Aztec</span>
            <span className="text-foreground">List</span>
          </h1>
          <p className="text-muted-foreground text-base">
            Buy and sell items on campus. Find great deals from fellow students.
          </p>
        </div>

        {/* Listings Section */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-foreground">Latest Listings</h2>
            {data && (
              <p className="text-base text-muted-foreground">
                {data.count} {data.count === 1 ? "listing" : "listings"} available
              </p>
            )}
          </div>

          {/* Results grid */}
          <SearchResults listings={data?.items || []} isLoading={isLoading} />

          {/* Pagination controls */}
          {data && <PaginationControls count={data.count} />}
        </div>
      </div>
    </div>
  );
}
