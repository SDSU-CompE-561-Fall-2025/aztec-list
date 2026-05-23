"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { ChevronLeft, User, Mail, Edit, MessageSquare, Loader2 } from "lucide-react";
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
import { createOrGetConversation } from "@/lib/messaging-api";
import { SimilarListings } from "@/components/listings/SimilarListings";
import { toast } from "sonner";

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
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();

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

  // Message seller mutation
  const createConversationMutation = useMutation({
    mutationFn: (otherUserId: string) => createOrGetConversation(otherUserId),
    onSuccess: (conversation) => {
      const otherUserId =
        conversation.user_1_id === user?.id ? conversation.user_2_id : conversation.user_1_id;

      // Invalidate conversations query to refresh the list
      queryClient.invalidateQueries({ queryKey: ["conversations", user?.id] });

      setShowContactDialog(false);
      toast.success("Opening conversation...");
      router.push(`/messages?conversation=${conversation.id}&user=${otherUserId}`);
    },
    onError: (error) => {
      if (error instanceof Error && error.message === "SESSION_EXPIRED") {
        toast.error("Your session has expired. Please log in again.");
        // Clear auth state
        logout();
        router.push(`/login?redirect=/listings/${listingId}`);
      } else {
        toast.error(error instanceof Error ? error.message : "Failed to start conversation");
      }
    },
  });

  const handleMessageSeller = () => {
    if (!user) {
      toast.error("Please log in to message sellers");
      router.push(`/login?redirect=/listings/${listingId}`);
      return;
    }

    if (listing?.seller_id) {
      createConversationMutation.mutate(listing.seller_id);
    }
  };

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
          <div className="mx-auto max-w-7xl px-6 py-4">
            <div className="h-10 w-40 animate-pulse rounded bg-muted" />
          </div>
        </div>
        <div className="mx-auto max-w-7xl px-6 py-8 lg:py-12">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-12">
            {/* Sidebar - matches order-2 md:order-2 */}
            <div className="order-2 space-y-6 md:order-2 md:col-span-5">
              {/* Price and title skeleton */}
              <div className="space-y-3">
                <div className="h-9 w-32 animate-pulse rounded bg-muted" />
                <div className="h-8 w-full animate-pulse rounded bg-muted" />
                <div className="h-6 w-24 animate-pulse rounded-full bg-muted" />
              </div>

              {/* Dates skeleton */}
              <div className="space-y-1">
                <div className="h-5 w-40 animate-pulse rounded bg-muted" />
                <div className="h-5 w-40 animate-pulse rounded bg-muted" />
              </div>

              {/* Seller card skeleton */}
              <div className="space-y-3 rounded-xl border bg-card p-5 backdrop-blur-sm">
                <div className="h-4 w-16 animate-pulse rounded bg-muted" />
                <div className="flex items-center gap-3 p-2">
                  <div className="h-12 w-12 animate-pulse rounded-full bg-muted" />
                  <div className="flex-1 space-y-2">
                    <div className="h-5 w-32 animate-pulse rounded bg-muted" />
                    <div className="h-4 w-24 animate-pulse rounded bg-muted" />
                    <div className="h-4 w-28 animate-pulse rounded bg-muted" />
                  </div>
                </div>
              </div>

              {/* Contact button skeleton */}
              <div className="space-y-3 rounded-xl border bg-card p-5 backdrop-blur-sm">
                <div className="h-6 w-20 animate-pulse rounded bg-muted" />
                <div className="h-10 w-full animate-pulse rounded bg-muted" />
              </div>
            </div>

            {/* Images - matches order-1 md:order-1 */}
            <div className="order-1 flex flex-col gap-4 md:order-1 md:col-span-7">
              <div className="flex flex-col gap-4 md:flex-row">
                {/* Thumbnail strip */}
                <div className="order-2 flex w-full gap-2 overflow-x-auto md:order-1 md:w-24 md:flex-col md:overflow-x-visible">
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="h-24 w-24 flex-shrink-0 animate-pulse rounded-lg border bg-card"
                    />
                  ))}
                </div>
                {/* Main image */}
                <div
                  className="order-1 w-full animate-pulse rounded-xl border bg-card md:order-2"
                  style={{ aspectRatio: "652/728", maxWidth: "652px" }}
                />
              </div>
              {/* Description/Condition skeleton - desktop only */}
              <div className="hidden space-y-6 md:block">
                <div className="space-y-2">
                  <div className="h-4 w-24 animate-pulse rounded bg-muted" />
                  <div className="space-y-2">
                    <div className="h-5 w-full animate-pulse rounded bg-muted" />
                    <div className="h-5 w-full animate-pulse rounded bg-muted" />
                    <div className="h-5 w-3/4 animate-pulse rounded bg-muted" />
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                  <div className="h-8 w-24 animate-pulse rounded-lg bg-muted" />
                </div>
              </div>
            </div>

            {/* Mobile description/condition - matches order-3 */}
            <div className="order-3 space-y-8 md:hidden">
              <div className="space-y-3">
                <div className="h-5 w-24 animate-pulse rounded bg-muted" />
                <div className="space-y-2">
                  <div className="h-6 w-full animate-pulse rounded bg-muted" />
                  <div className="h-6 w-full animate-pulse rounded bg-muted" />
                  <div className="h-6 w-3/4 animate-pulse rounded bg-muted" />
                </div>
              </div>
              <div className="space-y-3">
                <div className="h-5 w-20 animate-pulse rounded bg-muted" />
                <div className="h-9 w-28 animate-pulse rounded-lg bg-muted" />
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
          <div className="mx-auto max-w-7xl px-6 py-4">
            <Button
              variant="ghost"
              className="-ml-3 text-muted-foreground hover:text-foreground"
              onClick={() => router.push("/")}
            >
              <ChevronLeft className="mr-2 h-4 w-4" />
              Back to listings
            </Button>
          </div>
        </div>
        <div className="mx-auto max-w-2xl px-6 py-20 text-center">
          <div className="rounded-2xl border bg-card p-12 backdrop-blur-sm">
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
              <User className="h-8 w-8 text-muted-foreground" />
            </div>
            <h1 className="mb-3 text-2xl font-bold text-foreground">Listing Not Found</h1>
            <p className="mb-8 leading-relaxed text-muted-foreground">
              {error instanceof Error
                ? error.message
                : "This listing could not be found or may have been removed."}
            </p>
            <Button
              onClick={() => router.push("/")}
              className="bg-purple-600 text-white hover:bg-purple-700"
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
      <div className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur-sm">
        <div className="mx-auto max-w-7xl px-6 py-4">
          <Button
            variant="ghost"
            className="-ml-3 text-muted-foreground hover:text-foreground"
            onClick={() => router.back()}
          >
            <ChevronLeft className="mr-2 h-4 w-4" />
            Back to listings
          </Button>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-6 py-8 lg:py-12">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-12">
          <section className="order-2 space-y-6 md:order-2 md:col-span-5">
            <div className="space-y-3">
              <p className="text-3xl font-bold tracking-tight text-foreground">
                {formatPrice(Number(listing.price))}
              </p>
              <h1 className="text-2xl leading-tight font-semibold text-foreground">
                {listing.title}
              </h1>
              <div className="flex flex-wrap gap-3">
                <span className="inline-flex items-center rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-semibold text-purple-600 dark:text-purple-300">
                  {formatCategory(listing.category)}
                </span>
                {!listing.is_active && (
                  <span className="inline-flex items-center rounded-full border bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                    Inactive
                  </span>
                )}
              </div>
            </div>

            <div className="space-y-1 text-sm text-muted-foreground">
              <p>Posted {formatDate(listing.created_at)}</p>
              {isUpdated && <p>Updated {formatDate(listing.updated_at)}</p>}
            </div>

            <div className="space-y-3 rounded-xl border bg-card p-5 backdrop-blur-sm">
              <p className="text-sm font-semibold tracking-widest text-muted-foreground">
                {isOwnListing ? "Your Listing" : "Seller"}
              </p>
              <button
                onClick={() => router.push(`/profile/${listing.seller_id}`)}
                className="group flex w-full cursor-pointer items-center gap-3 rounded-lg p-2 text-left"
              >
                <div className="relative flex h-12 w-12 items-center justify-center overflow-hidden rounded-full border border-purple-500/20 bg-gradient-to-br from-purple-500/20 to-purple-600/20">
                  {isSellerProfileLoading ? (
                    <div className="h-full w-full animate-pulse bg-muted" />
                  ) : sellerProfile?.profile_picture_url ? (
                    <Image
                      src={
                        getProfilePictureUrl(
                          sellerProfile.profile_picture_url,
                          sellerProfile.updated_at,
                        ) || ""
                      }
                      alt={seller?.username || "Seller"}
                      fill
                      sizes="48px"
                      className="object-cover"
                    />
                  ) : (
                    <User className="h-6 w-6 text-purple-300" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-base font-medium text-foreground">
                    {isSellerProfileLoading ? (
                      <span className="inline-block h-5 w-32 animate-pulse rounded bg-muted" />
                    ) : (
                      sellerProfile?.name || seller?.username || "Loading..."
                    )}
                  </p>
                  {seller?.created_at && (
                    <p className="text-xs text-muted-foreground">
                      Joined{" "}
                      {new Date(seller.created_at).toLocaleDateString("en-US", {
                        month: "short",
                        year: "numeric",
                      })}
                    </p>
                  )}
                  <span className="text-sm text-purple-600 transition-colors group-hover:text-purple-700 dark:text-purple-300 dark:group-hover:text-purple-200">
                    View profile →
                  </span>
                </div>
              </button>

              {isOwnListing && (
                <Button
                  size="sm"
                  onClick={() => router.push(`/listings/${listingId}/edit`)}
                  variant="outline"
                  className="w-full border-purple-500/50 bg-purple-500/10 text-purple-600 hover:border-purple-500 hover:bg-purple-500/20 hover:text-purple-700 dark:text-purple-300 dark:hover:text-purple-200"
                >
                  <Edit className="mr-2 h-4 w-4" />
                  Edit Listing
                </Button>
              )}
            </div>

            {!isOwnListing && (
              <div className="space-y-3 rounded-xl border bg-card p-5 backdrop-blur-sm">
                <p className="text-sm font-semibold tracking-widest text-muted-foreground">
                  Contact
                </p>
                <Button
                  size="lg"
                  onClick={() => setShowContactDialog(true)}
                  className="w-full bg-gradient-to-r from-purple-600 to-purple-500 font-semibold text-white hover:from-purple-700 hover:to-purple-600"
                >
                  <Mail className="mr-2 h-5 w-5" />
                  Contact Seller
                </Button>
              </div>
            )}
          </section>

          <div className="order-1 flex flex-col gap-4 md:order-1 md:col-span-7">
            <div className="flex flex-col gap-4 md:flex-row">
              {hasMultipleImages && (
                <div className="order-2 flex w-full flex-shrink-0 gap-2 overflow-x-auto md:order-1 md:max-h-[728px] md:w-24 md:flex-col md:overflow-x-visible md:overflow-y-auto">
                  {galleryImages.map((image, index) => (
                    <button
                      key={image.id}
                      onClick={() => setCurrentImageIndex(index)}
                      className={cn(
                        "h-24 w-24 flex-shrink-0 cursor-pointer overflow-hidden rounded-lg border-2 bg-card transition-all",
                        boundedImageIndex === index
                          ? "border-purple-500 ring-2 ring-purple-500/20"
                          : "border opacity-60 hover:opacity-100",
                      )}
                    >
                      <div className="relative h-full w-full">
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
                className="relative order-1 w-full overflow-hidden rounded-xl border bg-card shadow-xl md:order-2"
                style={{
                  aspectRatio: hasMultipleImages ? "652/728" : "720/728",
                  maxWidth: hasMultipleImages ? "652px" : "720px",
                }}
              >
                <div className="relative h-full w-full">
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
                        <div className="absolute top-3 right-3 rounded-full border bg-background/90 px-2.5 py-1 text-xs font-medium text-foreground backdrop-blur-md">
                          {boundedImageIndex + 1} / {galleryImages.length}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="absolute inset-0 flex h-full w-full items-center justify-center">
                      <div className="text-center">
                        <User className="mx-auto mb-3 h-20 w-20 text-muted-foreground" />
                        <p className="text-sm text-muted-foreground">No image available</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Desktop: Description/Condition below images */}
            <div className="hidden space-y-6 md:block">
              <div className="space-y-2">
                <p className="text-xs font-bold tracking-widest text-muted-foreground uppercase">
                  Description
                </p>
                <p className="text-base leading-relaxed whitespace-pre-wrap text-foreground">
                  {descriptionText}
                </p>
              </div>
              <div className="space-y-2">
                <p className="text-xs font-bold tracking-widest text-muted-foreground uppercase">
                  Condition
                </p>
                <span
                  className={`inline-flex items-center rounded-lg bg-muted px-3 py-1.5 text-sm font-medium ${getConditionColor(listing.condition)}`}
                >
                  {CONDITION_LABELS[listing.condition]}
                </span>
              </div>
            </div>
          </div>

          {/* Mobile: Description/Condition after price section */}
          <div className="order-3 space-y-8 md:hidden">
            <div className="space-y-3">
              <p className="text-sm font-bold tracking-widest text-muted-foreground uppercase">
                Description
              </p>
              <p className="text-lg leading-relaxed whitespace-pre-wrap text-foreground">
                {descriptionText}
              </p>
            </div>
            <div className="space-y-3">
              <p className="text-sm font-bold tracking-widest text-muted-foreground uppercase">
                Condition
              </p>
              <span
                className={`inline-flex items-center rounded-lg bg-muted px-4 py-2 text-lg font-medium ${getConditionColor(listing.condition)}`}
              >
                {CONDITION_LABELS[listing.condition]}
              </span>
            </div>
          </div>
        </div>

        <SimilarListings listingId={listingId} />

        {/* Contact Dialog */}
        <Dialog open={showContactDialog} onOpenChange={setShowContactDialog}>
          <DialogContent className="max-w-[calc(100vw-2rem)] border bg-card p-4 sm:max-w-md sm:p-6">
            <DialogHeader className="space-y-1.5">
              <DialogTitle className="text-lg text-foreground sm:text-xl">
                Contact Seller
              </DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground sm:text-sm">
                Send a message to {seller?.username}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-2 pt-3 pb-1 sm:pt-4 sm:pb-2">
              {/* Message Option */}
              <button
                onClick={handleMessageSeller}
                disabled={createConversationMutation.isPending}
                className="group flex w-full items-center gap-2.5 rounded-lg border bg-muted p-3 transition-all hover:border-blue-500/50 hover:bg-muted/80 disabled:cursor-not-allowed disabled:opacity-50 sm:gap-3 sm:p-3.5"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-blue-500/20 bg-blue-500/10 sm:h-10 sm:w-10">
                  {createConversationMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin text-blue-400 sm:h-5 sm:w-5" />
                  ) : (
                    <MessageSquare className="h-4 w-4 text-blue-400 sm:h-5 sm:w-5" />
                  )}
                </div>
                <div className="min-w-0 flex-1 text-left">
                  <p className="mb-0.5 text-sm font-semibold text-foreground sm:text-base">
                    Send Message
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {createConversationMutation.isPending
                      ? "Starting conversation..."
                      : "Chat with seller through AztecList"}
                  </p>
                </div>
              </button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
