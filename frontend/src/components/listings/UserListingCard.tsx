"use client";

import { useRouter } from "next/navigation";
import Image from "next/image";
import { ListingSummary } from "@/types/listing/listing";
import { formatPrice, getConditionColor } from "@/lib/utils";
import { STATIC_BASE_URL, LISTINGS_BASE_URL } from "@/lib/constants";
import { ImageIcon } from "lucide-react";

interface UserListingCardProps {
  listing: ListingSummary;
}

export function UserListingCard({ listing }: UserListingCardProps) {
  const router = useRouter();
  const hasImage = listing.thumbnail_url;

  const handleCardClick = () => {
    router.push(`${LISTINGS_BASE_URL}/${listing.id}`);
  };

  return (
    <div
      onClick={handleCardClick}
      className="group cursor-pointer overflow-hidden rounded-xl border bg-card backdrop-blur-sm transition-all hover:border-purple-500/50 hover:shadow-lg hover:shadow-purple-500/10"
    >
      {/* Image Section */}
      <div className="relative aspect-square w-full overflow-hidden bg-muted">
        {hasImage ? (
          <>
            <Image
              src={`${STATIC_BASE_URL}${listing.thumbnail_url}`}
              alt={listing.title}
              fill
              sizes="(max-width: 768px) 100vw, 50vw"
              className="object-cover"
            />
            <div className="absolute inset-0 bg-black/0 transition-colors group-hover:bg-black/20" />
          </>
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            <ImageIcon className="h-16 w-16 text-muted-foreground" />
          </div>
        )}

        {!listing.is_active && (
          <div className="absolute top-2 right-2">
            <span className="inline-flex items-center rounded border bg-background/90 px-2 py-1 text-xs font-medium text-muted-foreground">
              Inactive
            </span>
          </div>
        )}
      </div>

      {/* Content Section */}
      <div className="space-y-2 p-4">
        <h3 className="line-clamp-1 text-xl font-bold text-foreground transition-colors group-hover:text-purple-300">
          {listing.title}
        </h3>

        <p className="text-lg font-semibold text-foreground">
          {formatPrice(Number(listing.price))}
        </p>

        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className={`font-medium capitalize ${getConditionColor(listing.condition)}`}>
            {listing.condition.replace("_", " ")}
          </span>
          <span>•</span>
          <span className="capitalize">{listing.category.replace("_", " ")}</span>
        </div>

        <p className="text-sm text-muted-foreground">
          Posted {new Date(listing.created_at).toLocaleDateString()}
        </p>
      </div>
    </div>
  );
}
