"use client";

import Link from "next/link";
import Image from "next/image";
import { ListingSummary } from "@/types/listing/listing";
import { formatPrice } from "@/lib/utils";
import { STATIC_BASE_URL, LISTINGS_BASE_URL } from "@/lib/constants";
import { ImageIcon } from "lucide-react";

interface ListingCardProps {
  listing: ListingSummary;
  topMatch?: boolean;
  priority?: boolean;
}

export function ListingCard({ listing, topMatch = false, priority = false }: ListingCardProps) {
  const hasImage = listing.thumbnail_url;

  // Build image URL safely
  const imageUrl =
    hasImage && listing.thumbnail_url
      ? listing.thumbnail_url.startsWith("http")
        ? listing.thumbnail_url
        : `${STATIC_BASE_URL}${listing.thumbnail_url}`
      : null;

  return (
    <Link
      href={`${LISTINGS_BASE_URL}/${listing.id}`}
      className="group flex cursor-pointer flex-col gap-2"
    >
      {/* Image or placeholder */}
      <div className="relative aspect-square overflow-hidden rounded-md bg-muted">
        {topMatch && (
          <div
            className="absolute top-2 left-2 z-10 rounded-full bg-purple-600 px-2 py-0.5 text-xs font-medium text-white shadow"
            title={
              listing.relevance_score != null
                ? `Relevance ${listing.relevance_score.toFixed(2)}`
                : undefined
            }
          >
            Top match
          </div>
        )}
        {imageUrl ? (
          <>
            <Image
              src={imageUrl}
              alt={listing.title}
              fill
              priority={priority}
              sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 25vw"
              className="object-cover"
            />
            <div className="absolute inset-0 bg-black/0 transition-colors group-hover:bg-black/20" />
          </>
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            <ImageIcon className="h-12 w-12 text-muted-foreground" />
          </div>
        )}
      </div>

      {/* Title */}
      <h3 className="line-clamp-2 text-base font-semibold text-foreground transition-colors group-hover:text-purple-400">
        {listing.title}
      </h3>

      {/* Price */}
      <p className="text-base font-bold text-foreground">{formatPrice(listing.price)}</p>
    </Link>
  );
}
