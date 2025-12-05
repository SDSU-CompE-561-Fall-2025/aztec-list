"use client";

import { useQuery } from "@tanstack/react-query";
import { createListingQueryOptions } from "@/queryOptions/createListingQueryOptions";
import { SearchResults } from "@/components/listings/SearchResults";
import { PaginationControls } from "@/components/listings/PaginationControls";
import { ErrorState } from "@/components/custom/ErrorState";
import { DEFAULT_SORT, DEFAULT_LIMIT } from "@/lib/constants";
import { ListingsParams } from "@/types/listing/listingParams";

export default function HomePage() {
  // Use default parameters for landing page
  const filters: ListingsParams = {
    sort: DEFAULT_SORT,
    limit: DEFAULT_LIMIT,
    offset: 0,
  };

  // Use TanStack Query to fetch listings
  const { data, isLoading, isError, error } = useQuery(createListingQueryOptions(filters));

  if (isError) {
    return <ErrorState error={error} showHero />;
  }

  return (
    <div className="min-h-screen bg-gray-950 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Hero Section */}
        <div className="mb-12 text-center">
          <h1 className="text-4xl font-bold text-white mb-4">
            Welcome to <span className="text-purple-500">AztecList</span> Campus
          </h1>
          <p className="text-gray-400 text-lg">
            Buy and sell items on campus. Find great deals from fellow students.
          </p>
        </div>

        {/* Listings Section */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold text-gray-100">Latest Listings</h2>
            {data && (
              <p className="text-sm text-gray-400">
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
