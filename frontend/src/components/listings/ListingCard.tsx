import { ListingSummary } from "@/types/listing/listing";
import { formatPrice } from "@/lib/utils";

interface ListingCardProps {
  listing: ListingSummary;
}

export function ListingCard({ listing }: ListingCardProps) {
  return (
    <div className="flex flex-col gap-2">
      {/* Placeholder image - square aspect ratio */}
      <div className="aspect-square bg-gray-800 rounded-md" />
      
      {/* Title */}
      <h3 className="text-sm font-medium text-gray-100 line-clamp-2">
        {listing.title}
      </h3>
      
      {/* Price */}
      <p className="text-lg font-semibold text-gray-100">
        {formatPrice(listing.price)}
      </p>
    </div>
  );
}
