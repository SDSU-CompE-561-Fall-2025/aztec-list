"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ChevronLeft, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { useMemo, useState } from "react";
import { createListingDetailQueryOptions } from "@/queryOptions/createListingDetailQueryOptions";
import { createUserQueryOptions } from "@/queryOptions/createUserQueryOptions";
import { STATIC_BASE_URL } from "@/lib/constants";
import { Category } from "@/types/listing/filters/category";

const CONDITION_LABELS = {
  new: "New",
  like_new: "Like New",
  good: "Good",
  fair: "Fair",
  poor: "Poor",
} as const;

type GalleryImage = {
  id: string;
  url: string;
  alt: string;
};

function formatPrice(price: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(price);
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function formatCategory(category: Category): string {
  return category
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export default function ListingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const listingId = params.listing_id as string;

  const { data: listing, isLoading, error } = useQuery(createListingDetailQueryOptions(listingId));

  // Fetch seller information
  const { data: seller } = useQuery({
    ...createUserQueryOptions(listing?.seller_id ?? ""),
    enabled: !!listing?.seller_id,
  });

  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  const galleryImages = useMemo<GalleryImage[]>(() => {
    if (!listing) {
      return [];
    }

    if (listing.images?.length) {
      return listing.images.map((image) => ({
        id: image.id,
        url: `${STATIC_BASE_URL}${image.url}`,
        alt: image.alt_text ?? listing.title,
      }));
    }

    if (listing.thumbnail_url) {
      return [
        {
          id: "thumbnail",
          url: `${STATIC_BASE_URL}${listing.thumbnail_url}`,
          alt: listing.title,
        },
      ];
    }

    return [];
  }, [listing]);

  const hasImages = galleryImages.length > 0;
  const hasMultipleImages = galleryImages.length > 1;
  const boundedImageIndex = hasImages ? Math.min(currentImageIndex, galleryImages.length - 1) : 0;
  const activeImage = hasImages ? galleryImages[boundedImageIndex] : null;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950">
        <div className="border-b border-gray-800/50 bg-gray-950/95 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="h-10 w-40 bg-gray-800 rounded animate-pulse" />
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-6 py-8 lg:py-12">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-12">
            <div className="order-1 md:order-1 md:col-span-7 space-y-4">
              <div className="flex flex-col md:flex-row gap-3 justify-center">
                <div className="flex md:flex-col gap-2 w-full md:w-24 overflow-x-auto md:overflow-x-visible order-2 md:order-1">
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="w-24 h-24 bg-gray-900/50 rounded-lg animate-pulse flex-shrink-0"
                    />
                  ))}
                </div>
                <div
                  className="w-full max-w-3xl bg-gray-900/50 rounded-xl animate-pulse border border-gray-800/50 order-1 md:order-2"
                  style={{ aspectRatio: "9/10" }}
                />
              </div>
              <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6 h-36 animate-pulse" />
            </div>
            <div className="order-2 md:order-2 md:col-span-5 space-y-4">
              {[1, 2].map((card) => (
                <div
                  key={card}
                  className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6 h-28 animate-pulse"
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !listing) {
    return (
      <div className="min-h-screen bg-gray-950">
        <div className="border-b border-gray-800/50 bg-gray-950/95 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <Button
              variant="ghost"
              className="text-gray-400 hover:text-gray-100 hover:bg-gray-800/50 -ml-3"
              onClick={() => router.push("/")}
            >
              <ChevronLeft className="w-4 h-4 mr-2" />
              Back to listings
            </Button>
          </div>
        </div>
        <div className="max-w-2xl mx-auto px-6 py-20 text-center">
          <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-2xl p-12">
            <div className="w-16 h-16 bg-gray-800/50 rounded-full flex items-center justify-center mx-auto mb-6">
              <User className="w-8 h-8 text-gray-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-100 mb-3">Listing Not Found</h1>
            <p className="text-gray-400 mb-8 leading-relaxed">
              {error instanceof Error
                ? error.message
                : "This listing could not be found or may have been removed."}
            </p>
            <Button onClick={() => router.push("/")} className="bg-purple-600 hover:bg-purple-700">
              Browse All Listings
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const isUpdated = listing.created_at !== listing.updated_at;
  const descriptionText = listing.description?.trim().length
    ? listing.description
    : "No description provided.";

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="border-b border-gray-800/50 bg-gray-950/95 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <Button
            variant="ghost"
            className="text-gray-400 hover:text-gray-100 hover:bg-gray-800/50 -ml-3"
            onClick={() => router.back()}
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Back to listings
          </Button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 lg:py-12">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-12">
          <section className="order-2 md:order-2 md:col-span-5 space-y-6">
            <div className="space-y-3">
              <p className="text-4xl font-bold text-white tracking-tight">
                {formatPrice(Number(listing.price))}
              </p>
              <h1 className="text-3xl font-semibold text-white leading-tight">{listing.title}</h1>
              <div className="flex flex-wrap gap-3">
                <span className="inline-flex items-center px-4 py-1.5 bg-purple-500/10 text-purple-200 text-sm font-semibold rounded-full border border-purple-500/30">
                  {formatCategory(listing.category)}
                </span>
                {!listing.is_active && (
                  <span className="inline-flex items-center px-4 py-1.5 bg-gray-800 text-gray-300 text-sm font-medium rounded-full border border-gray-700">
                    Inactive
                  </span>
                )}
              </div>
            </div>

            <div className="text-base text-gray-400 space-y-1">
              <p>Posted {formatDate(listing.created_at)}</p>
              {isUpdated && <p>Updated {formatDate(listing.updated_at)}</p>}
            </div>

            <div className="bg-gray-900/60 backdrop-blur-sm border border-gray-800/60 rounded-xl p-5 space-y-3">
              <p className="text-sm font-semibold text-gray-500 tracking-widest">Seller</p>
              <button
                onClick={() => router.push(`/profile/${listing.seller_id}`)}
                className="flex items-center gap-3 w-full rounded-lg p-2 group text-left cursor-pointer"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500/20 to-purple-600/20 rounded-full flex items-center justify-center border border-purple-500/20">
                  <User className="w-6 h-6 text-purple-300" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-gray-100 text-base font-medium truncate">
                    {seller?.username ?? "Loading..."}
                  </p>
                  <span className="text-purple-300 text-sm group-hover:text-purple-200 transition-colors">
                    View profile →
                  </span>
                </div>
              </button>
            </div>

            <div className="bg-gray-900/60 backdrop-blur-sm border border-gray-800/60 rounded-xl p-5 space-y-3">
              <h3 className="text-xl font-semibold text-white">Contact</h3>
              <Button
                size="lg"
                className="w-full bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-700 hover:to-purple-600 text-white font-semibold text-base"
              >
                Contact Seller
              </Button>
            </div>
          </section>

          <div className="order-1 md:order-1 md:col-span-7 flex flex-col gap-4">
            <div className="flex flex-col md:flex-row gap-4">
              {hasMultipleImages && (
                <div className="flex md:flex-col gap-2 w-full md:w-24 flex-shrink-0 order-2 md:order-1 overflow-x-auto md:overflow-y-auto md:overflow-x-visible md:max-h-[728px]">
                  {galleryImages.map((image, index) => (
                    <button
                      key={image.id}
                      onClick={() => setCurrentImageIndex(index)}
                      className={cn(
                        "w-24 h-24 bg-gray-900 rounded-lg overflow-hidden border-2 transition-all flex-shrink-0 cursor-pointer",
                        boundedImageIndex === index
                          ? "border-purple-500 ring-2 ring-purple-500/20"
                          : "border-gray-800 hover:border-gray-700 opacity-60 hover:opacity-100"
                      )}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={image.url} alt={image.alt} className="h-full w-full object-cover" />
                    </button>
                  ))}
                </div>
              )}

              <div
                className="relative w-full bg-gray-900 rounded-xl overflow-hidden border border-gray-800/60 shadow-xl order-1 md:order-2"
                style={{
                  aspectRatio: hasMultipleImages ? "652/728" : "720/728",
                  maxWidth: hasMultipleImages ? "652px" : "720px",
                }}
              >
                <div className="relative w-full h-full">
                  {activeImage ? (
                    <>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={activeImage.url}
                        alt={activeImage.alt}
                        className="w-full h-full object-cover"
                      />

                      {hasMultipleImages && (
                        <div className="absolute top-3 right-3 bg-gray-950/90 backdrop-blur-md px-2.5 py-1 rounded-full text-xs font-medium text-gray-100 border border-gray-800">
                          {boundedImageIndex + 1} / {galleryImages.length}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="absolute inset-0 w-full h-full flex items-center justify-center">
                      <div className="text-center">
                        <User className="w-20 h-20 text-gray-700 mx-auto mb-3" />
                        <p className="text-gray-500 text-sm">No image available</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Desktop: Description/Condition below images */}
            <div className="hidden md:block space-y-8">
              <div className="space-y-3">
                <p className="text-sm font-bold text-gray-400 uppercase tracking-widest">
                  Description
                </p>
                <p className="text-gray-200 text-lg leading-relaxed whitespace-pre-wrap">
                  {descriptionText}
                </p>
              </div>
              <div className="space-y-3">
                <p className="text-sm font-bold text-gray-400 uppercase tracking-widest">
                  Condition
                </p>
                <span className="inline-flex items-center px-4 py-2 bg-gray-800/50 text-gray-100 rounded-lg text-lg font-medium">
                  {CONDITION_LABELS[listing.condition]}
                </span>
              </div>
            </div>
          </div>

          {/* Mobile: Description/Condition after price section */}
          <div className="md:hidden order-3 space-y-8">
            <div className="space-y-3">
              <p className="text-sm font-bold text-gray-400 uppercase tracking-widest">
                Description
              </p>
              <p className="text-gray-200 text-lg leading-relaxed whitespace-pre-wrap">
                {descriptionText}
              </p>
            </div>
            <div className="space-y-3">
              <p className="text-sm font-bold text-gray-400 uppercase tracking-widest">Condition</p>
              <span className="inline-flex items-center px-4 py-2 bg-gray-800/50 text-gray-100 rounded-lg text-lg font-medium">
                {CONDITION_LABELS[listing.condition]}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
