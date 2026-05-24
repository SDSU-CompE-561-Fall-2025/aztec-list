"use client";

import { useQuery } from "@tanstack/react-query";
import { ListingCard } from "@/components/listings/ListingCard";
import { createSimilarListingsQueryOptions } from "@/queryOptions/createSimilarListingsQueryOptions";

interface SimilarListingsProps {
  listingId: string;
}

/**
 * "Similar listings" section for a listing detail page.
 *
 * Backed by the AI similarity endpoint; renders nothing when AI is disabled or there are no
 * neighbours (the backend returns an empty list), so the page degrades cleanly.
 */
export function SimilarListings({ listingId }: SimilarListingsProps) {
  const { data: listings } = useQuery(createSimilarListingsQueryOptions(listingId));

  if (!listings || listings.length === 0) {
    return null;
  }

  return (
    <section className="mt-12 border-t pt-8">
      <h2 className="mb-6 text-xl font-semibold text-foreground">Similar listings</h2>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {listings.map((listing) => (
          <ListingCard key={listing.id} listing={listing} />
        ))}
      </div>
    </section>
  );
}
