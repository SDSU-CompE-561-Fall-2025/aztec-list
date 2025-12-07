"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ListingSummary } from "@/types/listing/listing";
import { formatPrice, getConditionColor } from "@/lib/utils";
import { STATIC_BASE_URL, LISTINGS_BASE_URL } from "@/lib/constants";
import { ImageIcon } from "lucide-react";

interface UserListingCardProps {
  listing: ListingSummary;
}

export function UserListingCard({ listing }: UserListingCardProps) {
  const router = useRouter();
  const [imageError, setImageError] = useState(false);
  const hasImage = listing.thumbnail_url && !imageError;

  const handleCardClick = () => {
    router.push(`${LISTINGS_BASE_URL}/${listing.id}`);
  };

  return (
    <div
      onClick={handleCardClick}
      className="group bg-gray-900/60 backdrop-blur-sm border border-gray-800/60 rounded-xl overflow-hidden hover:border-purple-500/50 transition-all cursor-pointer hover:shadow-lg hover:shadow-purple-500/10"
    >
      {/* Image Section */}
      <div className="relative w-full aspect-square bg-gray-800/50 overflow-hidden">
        {hasImage ? (
          <>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`${STATIC_BASE_URL}${listing.thumbnail_url}`}
              alt={listing.title}
              className="w-full h-full object-cover"
              onError={() => setImageError(true)}
            />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <ImageIcon className="w-16 h-16 text-gray-700" />
          </div>
        )}

        {!listing.is_active && (
          <div className="absolute top-2 right-2">
            <span className="inline-flex items-center px-2 py-1 bg-gray-900/90 text-gray-300 text-xs font-medium rounded border border-gray-700">
              Inactive
            </span>
          </div>
        )}
      </div>

      {/* Content Section */}
      <div className="p-4 space-y-2">
        <h3 className="text-xl font-bold text-white line-clamp-1 group-hover:text-purple-300 transition-colors">
          {listing.title}
        </h3>

        <p className="text-lg font-semibold text-white">{formatPrice(Number(listing.price))}</p>

        <div className="flex items-center gap-2 text-sm text-gray-400">
          <span className={`capitalize font-medium ${getConditionColor(listing.condition)}`}>
            {listing.condition.replace("_", " ")}
          </span>
          <span>•</span>
          <span className="capitalize">{listing.category.replace("_", " ")}</span>
        </div>

        <p className="text-sm text-gray-500">
          Posted {new Date(listing.created_at).toLocaleDateString()}
        </p>
      </div>
    </div>
  );
}
