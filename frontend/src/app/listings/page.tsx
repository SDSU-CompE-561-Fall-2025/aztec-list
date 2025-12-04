"use client";

import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import createListingQueryOptions from "@/queryOptions/createListingQueryOptions";
import { SearchFilters } from "@/components/listings/SearchFilters";
import { SearchResults } from "@/components/listings/SearchResults";
import { PaginationControls } from "@/components/listings/PaginationControls";
import { DEFAULT_SORT, DEFAULT_LIMIT } from "@/lib/constants";
import { Category } from "@/types/listing/filters/category";
import { Condition } from "@/types/listing/filters/condition";
import { Sort } from "@/types/listing/filters/sort";

export default function ListingsPage() {
  const searchParams = useSearchParams();

  // Extract all filter parameters from URL
  const filters = {
    q: searchParams.get("q") || undefined,
    category: (searchParams.get("category") as Category) || undefined,
    minPrice: searchParams.get("minPrice") ? parseInt(searchParams.get("minPrice")!) : undefined,
    maxPrice: searchParams.get("maxPrice") ? parseInt(searchParams.get("maxPrice")!) : undefined,
    condition: (searchParams.get("condition") as Condition) || undefined,
    sort: (searchParams.get("sort") as Sort) || DEFAULT_SORT,
    limit: DEFAULT_LIMIT,
    offset: searchParams.get("offset") ? parseInt(searchParams.get("offset")!) : 0,
  };

  // Use TanStack Query to fetch listings
  const { data, isLoading, isError, error } = useQuery(
    createListingQueryOptions(filters)
  );

  if (isError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-500 font-semibold mb-2">Error loading listings</p>
          <p className="text-gray-400 text-sm">{error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex gap-8">
          {/* Sidebar with filters */}
          <SearchFilters />

          {/* Main content area */}
          <div className="flex-1">
            {/* Search query display */}
            {filters.q && (
              <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-100">
                  Search results for &quot;{filters.q}&quot;
                </h1>
                {data && (
                  <p className="text-sm text-gray-400 mt-1">
                    {data.count} {data.count === 1 ? "result" : "results"} found
                  </p>
                )}
              </div>
            )}

            {/* Results grid */}
            <SearchResults
              listings={data?.items || []}
              isLoading={isLoading}
            />

            {/* Pagination controls */}
            {data && <PaginationControls count={data.count} />}
          </div>
        </div>
      </div>
    </div>
  );
}
