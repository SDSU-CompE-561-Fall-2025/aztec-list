"use client";

import { Suspense, useState, useEffect, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ProfileListingCard } from "@/components/listings/ProfileListingCard";
import { PaginationControls } from "@/components/listings/PaginationControls";
import { DEFAULT_LIMIT } from "@/lib/constants";
import { Plus } from "lucide-react";
import { deleteListing, toggleListingActive } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { refreshCurrentUser } from "@/lib/auth";
import { createOwnListingsQueryOptions } from "@/queryOptions/createOwnListingsQueryOptions";
import { createProfileQueryOptions } from "@/queryOptions/createProfileQueryOptions";
import { getProfilePictureUrl } from "@/lib/profile-picture";
import { toast } from "sonner";
import { showErrorToast } from "@/lib/errorHandling";
import { ProtectedRoute } from "@/components/custom/ProtectedRoute";
import type { ListingSummary, ListingSearchResponse } from "@/types/listing/listing";

function ProfileContent() {
  const { user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const hasRefreshedRef = useRef(false);

  const offset = parseInt(searchParams.get("offset") ?? "0", 10) || 0;
  const status = (searchParams.get("status") ?? "all") as "all" | "active" | "inactive";

  // Refresh user data on mount to ensure we have latest verification status
  useEffect(() => {
    if (!user || hasRefreshedRef.current) return;

    hasRefreshedRef.current = true;

    const refreshUser = async () => {
      try {
        await refreshCurrentUser();
      } catch (error) {
        console.error("Failed to refresh user data:", error);
      }
    };

    refreshUser();
  }, [user]);

  // Fetch profile data
  const { data: profileData, isLoading: isProfileLoading } = useQuery(
    createProfileQueryOptions(user?.id)
  );

  // Check if profile is incomplete - only after data has loaded
  const [showIncompleteBanner, setShowIncompleteBanner] = useState(true);
  const isProfileIncomplete =
    !isProfileLoading && (!profileData || !profileData.name || !profileData.campus);

  const { data, isLoading, isError, error } = useQuery(
    createOwnListingsQueryOptions(user?.id ?? "", {
      limit: DEFAULT_LIMIT,
      offset,
      sort: "recent",
      include_inactive: true,
    })
  );

  // Filter listings based on status
  const filteredListings =
    data?.items.filter((listing: ListingSummary) => {
      if (status === "active") return listing.is_active;
      if (status === "inactive") return !listing.is_active;
      return true;
    }) ?? [];

  // Calculate counts
  const totalCount = data?.count ?? 0;
  const activeCount = data?.items.filter((item: ListingSummary) => item.is_active).length ?? 0;
  const inactiveCount = data?.items.filter((item: ListingSummary) => !item.is_active).length ?? 0;

  // Optimistic toggle mutation
  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      toggleListingActive(id, isActive),
    onMutate: async ({ id, isActive }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: ["own-listings", user?.id],
      });

      // Snapshot previous value
      const previousData = queryClient.getQueryData([
        "own-listings",
        user?.id,
        { limit: DEFAULT_LIMIT, offset, sort: "recent", include_inactive: true },
      ]);

      // Optimistically update
      queryClient.setQueryData(
        [
          "own-listings",
          user?.id,
          { limit: DEFAULT_LIMIT, offset, sort: "recent", include_inactive: true },
        ],
        (old: ListingSearchResponse | undefined) => {
          if (!old) return old;
          return {
            ...old,
            items: old.items.map((item: ListingSummary) =>
              item.id === id ? { ...item, is_active: isActive } : item
            ),
          };
        }
      );

      return { previousData };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousData) {
        queryClient.setQueryData(
          [
            "own-listings",
            user?.id,
            { limit: DEFAULT_LIMIT, offset, sort: "recent", include_inactive: true },
          ],
          context.previousData
        );
      }
      showErrorToast(err, "Failed to update listing visibility");
    },
    onSuccess: (updatedListing, { isActive }) => {
      // Update the cache with the actual server response
      queryClient.setQueryData(
        [
          "own-listings",
          user?.id,
          { limit: DEFAULT_LIMIT, offset, sort: "recent", include_inactive: true },
        ],
        (old: ListingSearchResponse | undefined) => {
          if (!old) return old;
          return {
            ...old,
            items: old.items.map((item: ListingSummary) =>
              item.id === updatedListing.id
                ? { ...item, is_active: updatedListing.is_active }
                : item
            ),
          };
        }
      );
      toast.success(isActive ? "Listing is now visible" : "Listing is now hidden", {
        style: {
          background: "rgb(20, 83, 45)",
          color: "white",
          border: "1px solid rgb(34, 197, 94)",
        },
      });
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteListing,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["own-listings", user?.id],
      });
      toast.success("Listing deleted successfully", {
        style: {
          background: "rgb(20, 83, 45)",
          color: "white",
          border: "1px solid rgb(34, 197, 94)",
        },
      });
    },
    onError: (error) => {
      showErrorToast(error, "Failed to delete listing");
    },
  });

  if (isError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-500 font-semibold mb-2">Error loading your listings</p>
          <p className="text-gray-400 text-sm">{error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto">
        {/* Profile Banner */}
        <div className="mb-6 sm:mb-8 bg-card/50 backdrop-blur-sm border rounded-xl p-8">
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4 sm:gap-6">
            {/* Profile Picture */}
            <div className="flex-shrink-0">
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-500/20 to-purple-600/20 border border-purple-500/20 flex items-center justify-center overflow-hidden relative">
                {isProfileLoading ? (
                  <div className="w-full h-full bg-muted animate-pulse" />
                ) : profileData?.profile_picture_url ? (
                  <Image
                    src={
                      getProfilePictureUrl(
                        profileData.profile_picture_url,
                        profileData.updated_at
                      ) || ""
                    }
                    alt={user?.username || "Profile"}
                    fill
                    sizes="96px"
                    className="object-cover"
                  />
                ) : (
                  <span className="text-3xl font-bold text-purple-300">
                    {user?.username?.substring(0, 2).toUpperCase() || "??"}
                  </span>
                )}
              </div>
            </div>

            {/* Profile Info */}
            <div className="flex-1 min-w-0 w-full">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h2 className="text-2xl font-bold text-foreground mb-2 text-center sm:text-left">
                    {isProfileLoading ? (
                      <div className="h-8 bg-muted animate-pulse rounded w-48 mx-auto sm:mx-0" />
                    ) : profileData?.name ? (
                      <>
                        {profileData.name}
                        <span className="text-lg text-muted-foreground font-normal sm:ml-2 block sm:inline mt-1 sm:mt-0">
                          (@{user?.username})
                        </span>
                      </>
                    ) : (
                      user?.username || "User"
                    )}
                  </h2>
                  <div className="space-y-2 text-sm">
                    {profileData?.campus && (
                      <div className="flex items-center gap-2 text-muted-foreground justify-center sm:justify-start">
                        <svg
                          className="w-4 h-4 flex-shrink-0"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                          />
                        </svg>
                        <span className="truncate">{profileData.campus}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-muted-foreground justify-center sm:justify-start">
                      <svg
                        className="w-4 h-4 flex-shrink-0"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                      </svg>
                      <span>
                        Joined{" "}
                        {new Date(user?.created_at || "").toLocaleDateString("en-US", {
                          month: "long",
                          year: "numeric",
                        })}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col gap-2 sm:gap-5 w-full sm:w-30 shrink-0">
                  <Button asChild variant="outline">
                    <Link href="/settings">Edit Profile</Link>
                  </Button>

                  {totalCount > 0 && (
                    <Button asChild className="bg-purple-600 hover:bg-purple-700 text-white">
                      <Link href="/listings/create">Add Listing</Link>
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Email Verification Banner - Only show if email is not verified */}
        {!user?.is_verified && (
          <div className="mb-4 sm:mb-6">
            <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-500/30 rounded-lg p-3 sm:p-4 flex flex-col sm:flex-row items-start gap-3">
              <div className="flex-shrink-0 mt-0.5">
                <svg
                  className="w-5 h-5 text-purple-600 dark:text-purple-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-purple-900 dark:text-purple-300 font-semibold text-sm mb-1.5">
                  Please verify your email to create listings.
                </h3>
                <p className="text-purple-800 dark:text-purple-200/70 text-xs sm:text-sm">
                  Check your inbox for the verification link or resend from your account settings.
                </p>
              </div>
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <Button
                  asChild
                  variant="outline"
                  size="sm"
                  className="border-purple-300 dark:border-purple-500/50 text-purple-700 dark:text-purple-300 hover:bg-purple-100 dark:hover:bg-purple-900/30 hover:text-purple-800 dark:hover:text-purple-200 flex-1 sm:flex-initial shrink-0"
                >
                  <Link href="/settings">Verify Email</Link>
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Incomplete Profile Banner - Only show if profile is incomplete */}
        {isProfileIncomplete && showIncompleteBanner && (
          <div className="mb-4 sm:mb-6">
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-500/30 rounded-lg p-3 sm:p-4 flex flex-col sm:flex-row items-start gap-3">
              <div className="flex-shrink-0 mt-0.5">
                <svg
                  className="w-5 h-5 text-blue-600 dark:text-blue-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-blue-900 dark:text-blue-300 font-semibold text-sm mb-1">
                  Complete Your Profile
                </h3>
                <p className="text-blue-700 dark:text-blue-200/80 text-xs sm:text-sm">
                  Add your name, campus, and contact information to help buyers connect with you.
                </p>
              </div>
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <Button
                  asChild
                  variant="outline"
                  size="sm"
                  className="border-blue-300 dark:border-blue-500/50 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/30 hover:text-blue-800 dark:hover:text-blue-200 flex-1 sm:flex-initial shrink-0"
                >
                  <Link href="/settings">Complete Profile</Link>
                </Button>
                <button
                  onClick={() => setShowIncompleteBanner(false)}
                  className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 shrink-0 cursor-pointer"
                  aria-label="Dismiss"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Listings Section */}
        <div>
          <div className="flex items-center justify-between mb-4 sm:mb-6">
            <h2 className="text-xl sm:text-2xl font-semibold text-foreground">Your Listings</h2>
          </div>

          {/* Status Filter Tabs */}
          <div className="flex gap-2 sm:gap-3 mb-6 border-b border overflow-x-auto">
            <button
              onClick={() => router.push("/profile?status=all")}
              className={`px-4 sm:px-6 py-2 sm:py-3 text-sm sm:text-base font-medium transition-colors whitespace-nowrap ${
                status === "all"
                  ? "text-purple-500 border-b-2 border-purple-500"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              All ({totalCount})
            </button>
            <button
              onClick={() => router.push("/profile?status=active")}
              className={`px-4 sm:px-6 py-2 sm:py-3 text-sm sm:text-base font-medium transition-colors whitespace-nowrap ${
                status === "active"
                  ? "text-green-500 border-b-2 border-green-500"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Active ({activeCount})
            </button>
            <button
              onClick={() => router.push("/profile?status=inactive")}
              className={`px-4 sm:px-6 py-2 sm:py-3 text-sm sm:text-base font-medium transition-colors whitespace-nowrap ${
                status === "inactive"
                  ? "text-muted-foreground/70 border-b-2 border-muted-foreground/50"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Inactive ({inactiveCount})
            </button>
          </div>

          {/* Empty state with CTA */}
          {data && totalCount === 0 ? (
            <div className="bg-card/50 backdrop-blur-sm border rounded-lg p-12 text-center">
              <div className="max-w-md mx-auto">
                <h3 className="text-xl font-semibold text-foreground mb-2">No listings yet</h3>
                <p className="text-muted-foreground mb-6 text-base">
                  Start selling by creating your first listing. It only takes a minute!
                </p>
                <Button asChild className="bg-purple-600 hover:bg-purple-700 text-white" size="lg">
                  <Link href="/listings/create">
                    <Plus className="w-5 h-5 mr-2" />
                    Create Your First Listing
                  </Link>
                </Button>
              </div>
            </div>
          ) : filteredListings.length === 0 ? (
            <div className="bg-muted rounded-lg p-12 text-center">
              <div className="max-w-md mx-auto">
                {status === "active" && (
                  <>
                    <h3 className="text-lg font-semibold text-foreground mb-2">
                      No active listings
                    </h3>
                    <p className="text-muted-foreground mb-6 text-sm">
                      All your listings are currently hidden. Click &ldquo;Inactive&rdquo; to view
                      them.
                    </p>
                  </>
                )}
                {status === "inactive" && (
                  <>
                    <h3 className="text-lg font-semibold text-foreground mb-2">
                      No hidden listings
                    </h3>
                    <p className="text-muted-foreground mb-6 text-sm">
                      All your listings are currently visible. Great job!
                    </p>
                  </>
                )}
              </div>
            </div>
          ) : (
            <>
              {/* Results grid */}
              {isLoading ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {Array.from({ length: DEFAULT_LIMIT }).map((_, i) => (
                    <div key={i} className="flex flex-col gap-2">
                      <div className="aspect-square bg-muted rounded-md animate-pulse" />
                      <div className="h-4 bg-muted rounded animate-pulse" />
                      <div className="h-6 bg-muted rounded animate-pulse w-1/2" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {filteredListings.map((listing) => (
                    <ProfileListingCard
                      key={listing.id}
                      listing={listing}
                      onToggleActive={(id, isActive) => toggleMutation.mutate({ id, isActive })}
                      onDelete={(id) => deleteMutation.mutate(id)}
                      isTogglingActive={toggleMutation.isPending}
                      isDeleting={deleteMutation.isPending}
                    />
                  ))}
                </div>
              )}

              {/* Pagination controls */}
              {data && filteredListings.length > 0 && <PaginationControls count={totalCount} />}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <Suspense
        fallback={
          <div className="flex items-center justify-center min-h-screen">
            <p className="text-muted-foreground">Loading...</p>
          </div>
        }
      >
        <ProfileContent />
      </Suspense>
    </ProtectedRoute>
  );
}
