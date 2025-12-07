"use client";

import { useState } from "react";
import Link from "next/link";
import { ListingSummary } from "@/types/listing/listing";
import { formatPrice } from "@/lib/utils";
import { STATIC_BASE_URL, LISTINGS_BASE_URL } from "@/lib/constants";
import { ImageIcon } from "lucide-react";

interface ListingCardProps {
  listing: ListingSummary;
}

export function ListingCard({ listing }: ListingCardProps) {
  const [imageError, setImageError] = useState(false);
  const hasImage = listing.thumbnail_url && !imageError;

  return (
    <Link
      href={`${LISTINGS_BASE_URL}/${listing.id}`}
      className="flex flex-col gap-2 group cursor-pointer"
    >
      {/* Image or placeholder */}
      <div className="relative aspect-square bg-gray-800 rounded-md overflow-hidden transition-transform group-hover:scale-105">
        {hasImage ? (
          <img
            src={`${STATIC_BASE_URL}${listing.thumbnail_url}`}
            alt={listing.title}
            className="w-full h-full object-cover"
            loading="lazy"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <ImageIcon className="w-12 h-12 text-gray-600" />
          </div>
        )}
      </div>

      {/* Title */}
      <h3 className="text-lg font-bold text-gray-100 line-clamp-2 group-hover:text-purple-400 transition-colors">
        {listing.title}
      </h3>

      {/* Price */}
      <p className="text-xl font-bold text-gray-100">{formatPrice(listing.price)}</p>
    </Link>
  );
}
