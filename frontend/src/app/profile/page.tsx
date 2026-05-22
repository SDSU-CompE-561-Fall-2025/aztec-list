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
import { Plus, Mail, Phone, Eye } from "lucide-react";
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
    createProfileQueryOptions(user?.id),
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
    }),
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
              item.id === id ? { ...item, is_active: isActive } : item,
            ),
          };
        },
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
          context.previousData,
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
                : item,
            ),
          };
        },
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
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="mb-2 font-semibold text-red-500">Error loading your listings</p>
          <p className="text-sm text-gray-400">{error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-7xl">
        {/* Profile Banner */}
        <div className="mb-6 rounded-xl border bg-card/50 p-8 backdrop-blur-sm sm:mb-8">
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start sm:gap-6">
            {/* Profile Picture */}
            <div className="flex-shrink-0">
              <div className="relative flex h-24 w-24 items-center justify-center overflow-hidden rounded-full border border-purple-500/20 bg-gradient-to-br from-purple-500/20 to-purple-600/20">
                {isProfileLoading ? (
                  <div className="h-full w-full animate-pulse bg-muted" />
                ) : profileData?.profile_picture_url ? (
                  <Image
                    src={
                      getProfilePictureUrl(
                        profileData.profile_picture_url,
                        profileData.updated_at,
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
            <div className="w-full min-w-0 flex-1">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0 flex-1">
                  <h2 className="mb-2 text-center text-2xl font-bold text-foreground sm:text-left">
                    {isProfileLoading ? (
                      <div className="mx-auto h-8 w-48 animate-pulse rounded bg-muted sm:mx-0" />
                    ) : profileData?.name ? (
                      <>
                        {profileData.name}
                        <span className="mt-1 block text-lg font-normal text-muted-foreground sm:mt-0 sm:ml-2 sm:inline">
                          (@{user?.username})
                        </span>
                      </>
                    ) : (
                      user?.username || "User"
                    )}
                  </h2>
                  <div className="space-y-2 text-sm">
                    {profileData?.campus && (
                      <div className="flex items-center justify-center gap-2 text-muted-foreground sm:justify-start">
                        <svg
                          className="h-4 w-4 flex-shrink-0"
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

                    {user?.email && (
                      <div className="flex items-center justify-center gap-2 text-muted-foreground sm:justify-start">
                        <Mail className="h-4 w-4 flex-shrink-0" />
                        <span className="truncate">{user.email}</span>
                      </div>
                    )}

                    {profileData?.contact_info?.phone && (
                      <div className="flex items-center justify-center gap-2 text-muted-foreground sm:justify-start">
                        <Phone className="h-4 w-4 flex-shrink-0" />
                        <span className="truncate">{profileData.contact_info.phone}</span>
                      </div>
                    )}

                    <div className="flex items-center justify-center gap-2 text-muted-foreground sm:justify-start">
                      <svg
                        className="h-4 w-4 flex-shrink-0"
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
                <div className="flex w-full shrink-0 flex-col gap-2 sm:w-auto sm:gap-3">
                  <div className="flex gap-2">
                    <Button asChild variant="outline" className="flex-1 justify-center">
                      <Link href="/settings" className="flex w-full items-center justify-center">
                        Edit Profile
                      </Link>
                    </Button>

                    {user?.id && (
                      <Button asChild variant="outline" className="justify-center px-3">
                        <Link
                          href={`/profile/${user.id}`}
                          className="flex items-center justify-center"
                          title="View Public Profile"
                        >
                          <Eye className="h-4 w-4" />
                        </Link>
                      </Button>
                    )}
                  </div>

                  {totalCount > 0 && (
                    <Button
                      asChild
                      className="w-full justify-center bg-purple-600 text-white hover:bg-purple-700"
                    >
                      <Link
                        href="/listings/create"
                        className="flex w-full items-center justify-center gap-2"
                      >
                        <Plus className="h-4 w-4" />
                        <span>Add Listing</span>
                      </Link>
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
            <div className="flex flex-col items-start gap-3 rounded-lg border border-purple-200 bg-purple-50 p-3 sm:flex-row sm:p-4 dark:border-purple-500/30 dark:bg-purple-900/20">
              <div className="mt-0.5 flex-shrink-0">
                <svg
                  className="h-5 w-5 text-purple-600 dark:text-purple-400"
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
                <h3 className="mb-1.5 text-sm font-semibold text-purple-900 dark:text-purple-300">
                  Please verify your email to create listings.
                </h3>
                <p className="text-xs text-purple-800 sm:text-sm dark:text-purple-200/70">
                  Check your inbox for the verification link or resend from your account settings.
                </p>
              </div>
              <div className="flex w-full items-center gap-2 sm:w-auto">
                <Button
                  asChild
                  variant="outline"
                  size="sm"
                  className="flex-1 shrink-0 border-purple-300 text-purple-700 hover:bg-purple-100 hover:text-purple-800 sm:flex-initial dark:border-purple-500/50 dark:text-purple-300 dark:hover:bg-purple-900/30 dark:hover:text-purple-200"
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
            <div className="flex flex-col items-start gap-3 rounded-lg border border-blue-200 bg-blue-50 p-3 sm:flex-row sm:p-4 dark:border-blue-500/30 dark:bg-blue-900/20">
              <div className="mt-0.5 flex-shrink-0">
                <svg
                  className="h-5 w-5 text-blue-600 dark:text-blue-400"
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
                <h3 className="mb-1 text-sm font-semibold text-blue-900 dark:text-blue-300">
                  Complete Your Profile
                </h3>
                <p className="text-xs text-blue-700 sm:text-sm dark:text-blue-200/80">
                  Add your name, campus, and contact information to help buyers connect with you.
                </p>
              </div>
              <div className="flex w-full items-center gap-2 sm:w-auto">
                <Button
                  asChild
                  variant="outline"
                  size="sm"
                  className="flex-1 shrink-0 border-blue-300 text-blue-700 hover:bg-blue-100 hover:text-blue-800 sm:flex-initial dark:border-blue-500/50 dark:text-blue-300 dark:hover:bg-blue-900/30 dark:hover:text-blue-200"
                >
                  <Link href="/settings">Complete Profile</Link>
                </Button>
                <button
                  onClick={() => setShowIncompleteBanner(false)}
                  className="shrink-0 cursor-pointer text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                  aria-label="Dismiss"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
          <div className="mb-4 flex items-center justify-between sm:mb-6">
            <h2 className="text-xl font-semibold text-foreground sm:text-2xl">Your Listings</h2>
          </div>

          {/* Status Filter Tabs */}
          <div className="mb-6 flex gap-2 overflow-x-auto border border-b sm:gap-3">
            <button
              onClick={() => router.push("/profile?status=all")}
              className={`px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors sm:px-6 sm:py-3 sm:text-base ${
                status === "all"
                  ? "border-b-2 border-purple-500 text-purple-500"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              All ({totalCount})
            </button>
            <button
              onClick={() => router.push("/profile?status=active")}
              className={`px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors sm:px-6 sm:py-3 sm:text-base ${
                status === "active"
                  ? "border-b-2 border-green-500 text-green-500"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Active ({activeCount})
            </button>
            <button
              onClick={() => router.push("/profile?status=inactive")}
              className={`px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors sm:px-6 sm:py-3 sm:text-base ${
                status === "inactive"
                  ? "border-b-2 border-muted-foreground/50 text-muted-foreground/70"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Inactive ({inactiveCount})
            </button>
          </div>

          {/* Empty state with CTA */}
          {data && totalCount === 0 ? (
            <div className="rounded-lg border bg-card/50 p-12 text-center backdrop-blur-sm">
              <div className="mx-auto max-w-md">
                <h3 className="mb-2 text-xl font-semibold text-foreground">No listings yet</h3>
                <p className="mb-6 text-base text-muted-foreground">
                  Start selling by creating your first listing. It only takes a minute!
                </p>
                <Button asChild className="bg-purple-600 text-white hover:bg-purple-700" size="lg">
                  <Link href="/listings/create">
                    <Plus className="mr-2 h-5 w-5" />
                    Create Your First Listing
                  </Link>
                </Button>
              </div>
            </div>
          ) : filteredListings.length === 0 ? (
            <div className="rounded-lg bg-muted p-12 text-center">
              <div className="mx-auto max-w-md">
                {status === "active" && (
                  <>
                    <h3 className="mb-2 text-lg font-semibold text-foreground">
                      No active listings
                    </h3>
                    <p className="mb-6 text-sm text-muted-foreground">
                      All your listings are currently hidden. Click &ldquo;Inactive&rdquo; to view
                      them.
                    </p>
                  </>
                )}
                {status === "inactive" && (
                  <>
                    <h3 className="mb-2 text-lg font-semibold text-foreground">
                      No hidden listings
                    </h3>
                    <p className="mb-6 text-sm text-muted-foreground">
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
                <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
                  {Array.from({ length: DEFAULT_LIMIT }).map((_, i) => (
                    <div key={i} className="flex flex-col gap-2">
                      <div className="aspect-square animate-pulse rounded-md bg-muted" />
                      <div className="h-4 animate-pulse rounded bg-muted" />
                      <div className="h-6 w-1/2 animate-pulse rounded bg-muted" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
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
          <div className="flex min-h-screen items-center justify-center">
            <p className="text-muted-foreground">Loading...</p>
          </div>
        }
      >
        <ProfileContent />
      </Suspense>
    </ProtectedRoute>
  );
}
