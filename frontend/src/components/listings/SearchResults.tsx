import { ListingSummary } from "@/types/listing/listing";
import { ListingCard } from "./ListingCard";
import { SKELETON_LOADING_COUNT } from "@/lib/constants";

interface SearchResultsProps {
  listings: ListingSummary[];
  isLoading: boolean;
}

export function SearchResults({ listings, isLoading }: SearchResultsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {Array.from({ length: SKELETON_LOADING_COUNT }).map((_, i) => (
          <div key={i} className="flex flex-col gap-2">
            <div className="aspect-square bg-muted rounded-md animate-pulse" />
            <div className="h-3 bg-muted rounded animate-pulse" />
            <div className="h-5 bg-muted rounded animate-pulse w-20" />
          </div>
        ))}
      </div>
    );
  }

  if (listings.length === 0) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-muted-foreground text-center">
          No listings match your search. Try adjusting your filters.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {listings.map((listing) => (
        <ListingCard key={listing.id} listing={listing} />
      ))}
    </div>
  );
}
