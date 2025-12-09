"use client";

import Link from "next/link";
import Image from "next/image";
import { ListingSummary } from "@/types/listing/listing";
import { formatPrice } from "@/lib/utils";
import { STATIC_BASE_URL, LISTINGS_BASE_URL } from "@/lib/constants";
import { ImageIcon } from "lucide-react";

interface ListingCardProps {
  listing: ListingSummary;
}

export function ListingCard({ listing }: ListingCardProps) {
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
      className="flex flex-col gap-2 group cursor-pointer"
    >
      {/* Image or placeholder */}
      <div className="relative aspect-square bg-muted rounded-md overflow-hidden">
        {imageUrl ? (
          <>
            <Image
              src={imageUrl}
              alt={listing.title}
              fill
              sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 25vw"
              className="object-cover"
            />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <ImageIcon className="w-12 h-12 text-muted-foreground" />
          </div>
        )}
      </div>

      {/* Title */}
      <h3 className="text-base font-semibold text-foreground line-clamp-2 group-hover:text-purple-400 transition-colors">
        {listing.title}
      </h3>

      {/* Price */}
      <p className="text-base font-bold text-foreground">{formatPrice(listing.price)}</p>
    </Link>
  );
}
