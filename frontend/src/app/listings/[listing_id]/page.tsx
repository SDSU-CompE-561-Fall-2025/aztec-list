"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { ChevronLeft, User, Mail, Phone, Edit } from "lucide-react";
import { cn, getConditionColor } from "@/lib/utils";
import { useMemo, useState } from "react";
import { createListingDetailQueryOptions } from "@/queryOptions/createListingDetailQueryOptions";
import { createUserQueryOptions } from "@/queryOptions/createUserQueryOptions";
import { STATIC_BASE_URL, API_BASE_URL } from "@/lib/constants";
import { getProfilePictureUrl } from "@/lib/profile-picture";
import { Category } from "@/types/listing/filters/category";
import { useAuth } from "@/contexts/AuthContext";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

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
  const { user } = useAuth();

  const { data: listing, isLoading, error } = useQuery(createListingDetailQueryOptions(listingId));

  // Fetch seller information
  const { data: seller } = useQuery({
    ...createUserQueryOptions(listing?.seller_id ?? ""),
    enabled: !!listing?.seller_id,
  });

  // Fetch seller's profile for contact info
  const { data: sellerProfile, isLoading: isSellerProfileLoading } = useQuery({
    queryKey: ["profile", listing?.seller_id],
    queryFn: async () => {
      if (!listing?.seller_id) return null;
      try {
        const response = await fetch(`${API_BASE_URL}/users/${listing.seller_id}/profile`);
        if (!response.ok) return null;
        return response.json();
      } catch {
        return null;
      }
    },
    enabled: !!listing?.seller_id,
  });

  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [showContactDialog, setShowContactDialog] = useState(false);

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
      <div className="min-h-screen bg-background">
        <div className="border-b bg-background/95 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="h-10 w-40 bg-muted rounded animate-pulse" />
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-6 py-8 lg:py-12">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-12">
            {/* Sidebar - matches order-2 md:order-2 */}
            <div className="order-2 md:order-2 md:col-span-5 space-y-6">
              {/* Price and title skeleton */}
              <div className="space-y-3">
                <div className="h-9 w-32 bg-muted rounded animate-pulse" />
                <div className="h-8 w-full bg-muted rounded animate-pulse" />
                <div className="h-6 w-24 bg-muted rounded-full animate-pulse" />
              </div>

              {/* Dates skeleton */}
              <div className="space-y-1">
                <div className="h-5 w-40 bg-muted rounded animate-pulse" />
                <div className="h-5 w-40 bg-muted rounded animate-pulse" />
              </div>

              {/* Seller card skeleton */}
              <div className="bg-card backdrop-blur-sm border rounded-xl p-5 space-y-3">
                <div className="h-4 w-16 bg-muted rounded animate-pulse" />
                <div className="flex items-center gap-3 p-2">
                  <div className="w-12 h-12 bg-muted rounded-full animate-pulse" />
                  <div className="flex-1 space-y-2">
                    <div className="h-5 w-32 bg-muted rounded animate-pulse" />
                    <div className="h-4 w-24 bg-muted rounded animate-pulse" />
                    <div className="h-4 w-28 bg-muted rounded animate-pulse" />
                  </div>
                </div>
              </div>

              {/* Contact button skeleton */}
              <div className="bg-card backdrop-blur-sm border rounded-xl p-5 space-y-3">
                <div className="h-6 w-20 bg-muted rounded animate-pulse" />
                <div className="h-10 w-full bg-muted rounded animate-pulse" />
              </div>
            </div>

            {/* Images - matches order-1 md:order-1 */}
            <div className="order-1 md:order-1 md:col-span-7 flex flex-col gap-4">
              <div className="flex flex-col md:flex-row gap-4">
                {/* Thumbnail strip */}
                <div className="flex md:flex-col gap-2 w-full md:w-24 overflow-x-auto md:overflow-x-visible order-2 md:order-1">
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="w-24 h-24 bg-card rounded-lg animate-pulse flex-shrink-0 border"
                    />
                  ))}
                </div>
                {/* Main image */}
                <div
                  className="w-full bg-card rounded-xl animate-pulse border order-1 md:order-2"
                  style={{ aspectRatio: "652/728", maxWidth: "652px" }}
                />
              </div>
              {/* Description/Condition skeleton - desktop only */}
              <div className="hidden md:block space-y-6">
                <div className="space-y-2">
                  <div className="h-4 w-24 bg-muted rounded animate-pulse" />
                  <div className="space-y-2">
                    <div className="h-5 w-full bg-muted rounded animate-pulse" />
                    <div className="h-5 w-full bg-muted rounded animate-pulse" />
                    <div className="h-5 w-3/4 bg-muted rounded animate-pulse" />
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="h-4 w-20 bg-muted rounded animate-pulse" />
                  <div className="h-8 w-24 bg-muted rounded-lg animate-pulse" />
                </div>
              </div>
            </div>

            {/* Mobile description/condition - matches order-3 */}
            <div className="md:hidden order-3 space-y-8">
              <div className="space-y-3">
                <div className="h-5 w-24 bg-muted rounded animate-pulse" />
                <div className="space-y-2">
                  <div className="h-6 w-full bg-muted rounded animate-pulse" />
                  <div className="h-6 w-full bg-muted rounded animate-pulse" />
                  <div className="h-6 w-3/4 bg-muted rounded animate-pulse" />
                </div>
              </div>
              <div className="space-y-3">
                <div className="h-5 w-20 bg-muted rounded animate-pulse" />
                <div className="h-9 w-28 bg-muted rounded-lg animate-pulse" />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !listing) {
    return (
      <div className="min-h-screen bg-background">
        <div className="border-b bg-background/95 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <Button
              variant="ghost"
              className="text-muted-foreground hover:text-foreground -ml-3"
              onClick={() => router.push("/")}
            >
              <ChevronLeft className="w-4 h-4 mr-2" />
              Back to listings
            </Button>
          </div>
        </div>
        <div className="max-w-2xl mx-auto px-6 py-20 text-center">
          <div className="bg-card backdrop-blur-sm border rounded-2xl p-12">
            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-6">
              <User className="w-8 h-8 text-muted-foreground" />
            </div>
            <h1 className="text-2xl font-bold text-foreground mb-3">Listing Not Found</h1>
            <p className="text-muted-foreground mb-8 leading-relaxed">
              {error instanceof Error
                ? error.message
                : "This listing could not be found or may have been removed."}
            </p>
            <Button
              onClick={() => router.push("/")}
              className="bg-purple-600 hover:bg-purple-700 text-white"
            >
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
  const isOwnListing = user?.id === listing.seller_id;

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b bg-background/95 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <Button
            variant="ghost"
            className="text-muted-foreground hover:text-foreground -ml-3"
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
              <p className="text-3xl font-bold text-foreground tracking-tight">
                {formatPrice(Number(listing.price))}
              </p>
              <h1 className="text-2xl font-semibold text-foreground leading-tight">
                {listing.title}
              </h1>
              <div className="flex flex-wrap gap-3">
                <span className="inline-flex items-center px-3 py-1 bg-purple-500/10 text-purple-600 dark:text-purple-300 text-xs font-semibold rounded-full border border-purple-500/30">
                  {formatCategory(listing.category)}
                </span>
                {!listing.is_active && (
                  <span className="inline-flex items-center px-3 py-1 bg-muted text-muted-foreground text-xs font-medium rounded-full border">
                    Inactive
                  </span>
                )}
              </div>
            </div>

            <div className="text-sm text-muted-foreground space-y-1">
              <p>Posted {formatDate(listing.created_at)}</p>
              {isUpdated && <p>Updated {formatDate(listing.updated_at)}</p>}
            </div>

            <div className="bg-card backdrop-blur-sm border rounded-xl p-5 space-y-3">
              <p className="text-sm font-semibold text-muted-foreground tracking-widest">
                {isOwnListing ? "Your Listing" : "Seller"}
              </p>
              <button
                onClick={() => router.push(`/profile/${listing.seller_id}`)}
                className="flex items-center gap-3 w-full rounded-lg p-2 group text-left cursor-pointer"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500/20 to-purple-600/20 rounded-full flex items-center justify-center border border-purple-500/20 overflow-hidden relative">
                  {isSellerProfileLoading ? (
                    <div className="w-full h-full bg-muted animate-pulse" />
                  ) : sellerProfile?.profile_picture_url ? (
                    <Image
                      src={
                        getProfilePictureUrl(
                          sellerProfile.profile_picture_url,
                          sellerProfile.updated_at
                        ) || ""
                      }
                      alt={seller?.username || "Seller"}
                      fill
                      sizes="48px"
                      className="object-cover"
                    />
                  ) : (
                    <User className="w-6 h-6 text-purple-300" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-foreground text-base font-medium truncate">
                    {isSellerProfileLoading ? (
                      <span className="inline-block h-5 bg-muted animate-pulse rounded w-32" />
                    ) : (
                      sellerProfile?.name || seller?.username || "Loading..."
                    )}
                  </p>
                  {seller?.created_at && (
                    <p className="text-muted-foreground text-xs">
                      Joined{" "}
                      {new Date(seller.created_at).toLocaleDateString("en-US", {
                        month: "short",
                        year: "numeric",
                      })}
                    </p>
                  )}
                  <span className="text-purple-600 dark:text-purple-300 text-sm group-hover:text-purple-700 dark:group-hover:text-purple-200 transition-colors">
                    View profile →
                  </span>
                </div>
              </button>

              {isOwnListing && (
                <Button
                  size="sm"
                  onClick={() => router.push(`/listings/${listingId}/edit`)}
                  variant="outline"
                  className="w-full border-purple-500/50 hover:border-purple-500 bg-purple-500/10 hover:bg-purple-500/20 text-purple-600 hover:text-purple-700 dark:text-purple-300 dark:hover:text-purple-200"
                >
                  <Edit className="w-4 h-4 mr-2" />
                  Edit Listing
                </Button>
              )}
            </div>

            {!isOwnListing && (
              <div className="bg-card backdrop-blur-sm border rounded-xl p-5 space-y-3">
                <p className="text-sm font-semibold text-muted-foreground tracking-widest">
                  Contact
                </p>
                <Button
                  size="lg"
                  onClick={() => setShowContactDialog(true)}
                  className="w-full bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-700 hover:to-purple-600 text-white font-semibold"
                >
                  <Mail className="w-5 h-5 mr-2" />
                  Contact Seller
                </Button>
              </div>
            )}
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
                        "w-24 h-24 bg-card rounded-lg overflow-hidden border-2 transition-all flex-shrink-0 cursor-pointer",
                        boundedImageIndex === index
                          ? "border-purple-500 ring-2 ring-purple-500/20"
                          : "border opacity-60 hover:opacity-100"
                      )}
                    >
                      <div className="relative w-full h-full">
                        <Image
                          src={image.url}
                          alt={image.alt}
                          fill
                          sizes="96px"
                          className="object-cover"
                        />
                      </div>
                    </button>
                  ))}
                </div>
              )}

              <div
                className="relative w-full bg-card rounded-xl overflow-hidden border shadow-xl order-1 md:order-2"
                style={{
                  aspectRatio: hasMultipleImages ? "652/728" : "720/728",
                  maxWidth: hasMultipleImages ? "652px" : "720px",
                }}
              >
                <div className="relative w-full h-full">
                  {activeImage ? (
                    <>
                      <Image
                        src={activeImage.url}
                        alt={activeImage.alt}
                        fill
                        sizes="(max-width: 768px) 100vw, 720px"
                        className="object-cover"
                        priority
                      />

                      {hasMultipleImages && (
                        <div className="absolute top-3 right-3 bg-background/90 backdrop-blur-md px-2.5 py-1 rounded-full text-xs font-medium text-foreground border">
                          {boundedImageIndex + 1} / {galleryImages.length}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="absolute inset-0 w-full h-full flex items-center justify-center">
                      <div className="text-center">
                        <User className="w-20 h-20 text-muted-foreground mx-auto mb-3" />
                        <p className="text-muted-foreground text-sm">No image available</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Desktop: Description/Condition below images */}
            <div className="hidden md:block space-y-6">
              <div className="space-y-2">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest">
                  Description
                </p>
                <p className="text-foreground text-base leading-relaxed whitespace-pre-wrap">
                  {descriptionText}
                </p>
              </div>
              <div className="space-y-2">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest">
                  Condition
                </p>
                <span
                  className={`inline-flex items-center px-3 py-1.5 bg-muted rounded-lg text-sm font-medium ${getConditionColor(listing.condition)}`}
                >
                  {CONDITION_LABELS[listing.condition]}
                </span>
              </div>
            </div>
          </div>

          {/* Mobile: Description/Condition after price section */}
          <div className="md:hidden order-3 space-y-8">
            <div className="space-y-3">
              <p className="text-sm font-bold text-muted-foreground uppercase tracking-widest">
                Description
              </p>
              <p className="text-foreground text-lg leading-relaxed whitespace-pre-wrap">
                {descriptionText}
              </p>
            </div>
            <div className="space-y-3">
              <p className="text-sm font-bold text-muted-foreground uppercase tracking-widest">
                Condition
              </p>
              <span
                className={`inline-flex items-center px-4 py-2 bg-muted rounded-lg text-lg font-medium ${getConditionColor(listing.condition)}`}
              >
                {CONDITION_LABELS[listing.condition]}
              </span>
            </div>
          </div>
        </div>

        {/* Contact Dialog */}
        <Dialog open={showContactDialog} onOpenChange={setShowContactDialog}>
          <DialogContent className="bg-card border sm:max-w-md max-w-[calc(100vw-2rem)] p-4 sm:p-6">
            <DialogHeader className="space-y-1.5">
              <DialogTitle className="text-foreground text-lg sm:text-xl">
                Contact Seller
              </DialogTitle>
              <DialogDescription className="text-muted-foreground text-xs sm:text-sm">
                Choose how you&apos;d like to contact {seller?.username}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-2 pt-3 sm:pt-4 pb-1 sm:pb-2">
              {/* Email Option */}
              <a
                href={`mailto:${seller?.email}?subject=${encodeURIComponent(`Interested in: ${listing.title}`)}&body=${encodeURIComponent(`Hi ${seller?.username},\n\nI'm interested in your listing "${listing.title}" on AztecList.\n\n`)}`}
                className="flex items-center gap-2.5 sm:gap-3 p-3 sm:p-3.5 rounded-lg bg-muted hover:bg-muted/80 border hover:border-purple-500/50 transition-all group"
                onClick={() => setShowContactDialog(false)}
              >
                <div className="w-9 h-9 sm:w-10 sm:h-10 bg-purple-500/10 rounded-full flex items-center justify-center border border-purple-500/20 shrink-0">
                  <Mail className="w-4 h-4 sm:w-5 sm:h-5 text-purple-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-foreground font-semibold text-sm sm:text-base mb-0.5">
                    Send Email
                  </p>
                  <p className="text-muted-foreground text-xs truncate">{seller?.email}</p>
                </div>
              </a>

              {/* Phone Option - Only show if available */}
              {sellerProfile?.contact_info?.phone && (
                <a
                  href={`tel:${sellerProfile.contact_info.phone.replace(/\D/g, "")}`}
                  className="flex items-center gap-2.5 sm:gap-3 p-3 sm:p-3.5 rounded-lg bg-muted hover:bg-muted/80 border hover:border-green-500/50 transition-all group"
                  onClick={() => setShowContactDialog(false)}
                >
                  <div className="w-9 h-9 sm:w-10 sm:h-10 bg-green-500/10 rounded-full flex items-center justify-center border border-green-500/20 shrink-0">
                    <Phone className="w-4 h-4 sm:w-5 sm:h-5 text-green-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-foreground font-semibold text-sm sm:text-base mb-0.5">
                      Call
                    </p>
                    <p className="text-muted-foreground text-xs">
                      {sellerProfile.contact_info.phone}
                    </p>
                  </div>
                </a>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
