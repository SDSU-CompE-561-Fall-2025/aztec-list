"use client";

import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { createListingQueryOptions } from "@/queryOptions/createListingQueryOptions";
import { SearchFilters } from "@/components/listings/SearchFilters";
import { SearchResults } from "@/components/listings/SearchResults";
import { PaginationControls } from "@/components/listings/PaginationControls";
import { ErrorState } from "@/components/custom/ErrorState";
import { DEFAULT_SORT, DEFAULT_LIMIT } from "@/lib/constants";
import { CATEGORIES, Category } from "@/types/listing/filters/category";
import { CONDITIONS, Condition } from "@/types/listing/filters/condition";
import { SORT_OPTIONS, Sort } from "@/types/listing/filters/sort";

export default function ListingsPage() {
  const searchParams = useSearchParams();

  // Extract and validate filter parameters from URL
  const parsePrice = (value: string | null): number | undefined => {
    if (!value) return undefined;
    const parsed = parseInt(value, 10);
    return isNaN(parsed) || parsed < 0 ? undefined : parsed;
  };

  const categoryParam = searchParams.get("category");
  const conditionParam = searchParams.get("condition");
  const sortParam = searchParams.get("sort");

  const filters = {
    q: searchParams.get("q") || undefined,
    category:
      categoryParam && CATEGORIES.includes(categoryParam as Category)
        ? (categoryParam as Category)
        : undefined,
    minPrice: parsePrice(searchParams.get("minPrice")),
    maxPrice: parsePrice(searchParams.get("maxPrice")),
    condition:
      conditionParam && CONDITIONS.includes(conditionParam as Condition)
        ? (conditionParam as Condition)
        : undefined,
    sort:
      sortParam && SORT_OPTIONS.includes(sortParam as Sort) ? (sortParam as Sort) : DEFAULT_SORT,
    limit: DEFAULT_LIMIT,
    offset: parseInt(searchParams.get("offset") ?? "0", 10) || 0,
  };

  // Use TanStack Query to fetch listings
  const { data, isLoading, isError, error } = useQuery(createListingQueryOptions(filters));

  if (isError) {
    return <ErrorState error={error} />;
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
            <SearchResults listings={data?.items || []} isLoading={isLoading} />

            {/* Pagination controls */}
            {data && <PaginationControls count={data.count} />}
          </div>
        </div>
      </div>
    </div>
  );
}
