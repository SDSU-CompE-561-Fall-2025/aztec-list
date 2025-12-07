"use client";

import { Suspense, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ProfileListingCard } from "@/components/listings/ProfileListingCard";
import { PaginationControls } from "@/components/listings/PaginationControls";
import { DEFAULT_LIMIT, API_BASE_URL } from "@/lib/constants";
import { Plus } from "lucide-react";
import { deleteListing, toggleListingActive } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { createOwnListingsQueryOptions } from "@/queryOptions/createOwnListingsQueryOptions";
import { toast } from "sonner";
import { ProtectedRoute } from "@/components/custom/ProtectedRoute";
import type { ListingSummary, ListingSearchResponse } from "@/types/listing/listing";
import { getAuthToken } from "@/lib/auth";

function ProfileContent() {
  const { user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  const offset = parseInt(searchParams.get("offset") ?? "0", 10) || 0;
  const status = (searchParams.get("status") ?? "all") as "all" | "active" | "inactive";

  // Fetch profile data
  const { data: profileData } = useQuery({
    queryKey: ["profile", user?.id],
    queryFn: async () => {
      const token = getAuthToken();
      if (!token) return null;

      try {
        const response = await fetch(`${API_BASE_URL}/users/profile/`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          // Profile doesn't exist yet
          if (response.status === 404) return null;
          throw new Error("Failed to fetch profile");
        }

        return response.json();
      } catch {
        return null;
      }
    },
    enabled: !!user?.id,
  });

  // Check if profile is incomplete
  const [showIncompleteBanner, setShowIncompleteBanner] = useState(true);
  const isProfileIncomplete = !profileData || !profileData.name || !profileData.campus;

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
      toast.error("Failed to update listing visibility");
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
      toast.success(isActive ? "Listing is now visible" : "Listing is now hidden");
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteListing,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["own-listings", user?.id],
      });
      toast.success("Listing deleted successfully");
    },
    onError: () => {
      toast.error("Failed to delete listing");
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
    <div className="min-h-screen bg-gray-950 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Profile Banner */}
        <Card className="mb-8 bg-gray-900 border-gray-800 overflow-hidden">
          <CardContent className="p-0">
            <div className="p-8 flex items-center gap-6">
              {/* Profile Picture */}
              <div className="flex-shrink-0">
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-500/20 to-purple-600/20 border-2 border-purple-500/30 flex items-center justify-center">
                  <span className="text-3xl font-bold text-purple-300">
                    {user?.username?.substring(0, 2).toUpperCase() || "??"}
                  </span>
                </div>
              </div>

              {/* Profile Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h2 className="text-3xl font-bold text-white mb-2">
                      {profileData?.name ? (
                        <>
                          {profileData.name}
                          <span className="text-2xl text-gray-400 font-normal ml-2">
                            (@{user?.username})
                          </span>
                        </>
                      ) : (
                        user?.username || "User"
                      )}
                    </h2>
                    <div className="space-y-2 text-base">
                      {profileData?.campus && (
                        <div className="flex items-center gap-2 text-gray-400">
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
                      <div className="flex items-center gap-2 text-gray-400">
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
                            d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                          />
                        </svg>
                        <span className="truncate">{user?.email}</span>
                      </div>
                      {profileData?.contact_info?.phone && (
                        <div className="flex items-center gap-2 text-gray-400">
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
                              d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                            />
                          </svg>
                          <span className="truncate">{profileData.contact_info.phone}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-2 text-gray-400">
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

                  {/* Edit Profile Button */}
                  <Button
                    asChild
                    className="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-white shrink-0"
                  >
                    <Link href="/settings">Edit Profile</Link>
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Incomplete Profile Banner - Only show if profile is incomplete */}
        {isProfileIncomplete && showIncompleteBanner && (
          <div className="mb-6">
            <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4 flex items-start gap-3">
              <div className="flex-shrink-0 mt-0.5">
                <svg
                  className="w-5 h-5 text-blue-400"
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
                <h3 className="text-blue-300 font-semibold text-base mb-1">
                  Complete Your Profile
                </h3>
                <p className="text-blue-200/80 text-base">
                  Add your name, campus, and contact information to help buyers connect with you.
                </p>
              </div>
              <Button
                asChild
                variant="outline"
                className="border-blue-500/50 text-blue-300 hover:bg-blue-900/30 hover:text-blue-200 shrink-0"
              >
                <Link href="/settings">Complete Profile</Link>
              </Button>
              <button
                onClick={() => setShowIncompleteBanner(false)}
                className="text-blue-400 hover:text-blue-300 shrink-0 cursor-pointer ml-2"
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
        )}

        {/* User Stats */}
        {data && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <button
              onClick={() => router.push("/profile?status=all")}
              className="bg-gray-900 rounded-lg p-6 text-left transition-all hover:bg-gray-800 hover:shadow-lg cursor-pointer"
            >
              <h3 className="text-gray-400 text-base font-medium mb-1">Total Listings</h3>
              <p className="text-4xl font-bold text-white">{totalCount}</p>
            </button>
            <button
              onClick={() => router.push("/profile?status=active")}
              className="bg-gray-900 rounded-lg p-6 text-left transition-all hover:bg-gray-800 hover:shadow-lg hover:shadow-green-500/20 cursor-pointer"
            >
              <h3 className="text-gray-400 text-base font-medium mb-1">Active</h3>
              <p className="text-4xl font-bold text-green-500">{activeCount}</p>
            </button>
            <button
              onClick={() => router.push("/profile?status=inactive")}
              className="bg-gray-900 rounded-lg p-6 text-left transition-all hover:bg-gray-800 hover:shadow-lg hover:shadow-gray-500/20 cursor-pointer"
            >
              <h3 className="text-gray-400 text-base font-medium mb-1">Inactive</h3>
              <p className="text-4xl font-bold text-gray-500">{inactiveCount}</p>
            </button>
          </div>
        )}

        {/* Listings Section */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-3xl font-semibold text-gray-100">Your Listings</h2>
          </div>

          {/* Status Filter Tabs */}
          <div className="flex gap-2 mb-6 border-b border-gray-800">
            <button
              onClick={() => router.push("/profile?status=all")}
              className={`px-4 py-2 text-base font-medium transition-colors ${
                status === "all"
                  ? "text-purple-500 border-b-2 border-purple-500"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              All ({totalCount})
            </button>
            <button
              onClick={() => router.push("/profile?status=active")}
              className={`px-4 py-2 text-base font-medium transition-colors ${
                status === "active"
                  ? "text-green-500 border-b-2 border-green-500"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              Active ({activeCount})
            </button>
            <button
              onClick={() => router.push("/profile?status=inactive")}
              className={`px-4 py-2 text-base font-medium transition-colors ${
                status === "inactive"
                  ? "text-gray-500 border-b-2 border-gray-500"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              Inactive ({inactiveCount})
            </button>
          </div>

          {/* Empty state with CTA */}
          {data && totalCount === 0 ? (
            <div className="bg-gray-900 rounded-lg p-12 text-center">
              <div className="max-w-md mx-auto">
                <h3 className="text-2xl font-semibold text-white mb-2">No listings yet</h3>
                <p className="text-gray-400 mb-6 text-lg">
                  Start selling by creating your first listing. It only takes a minute!
                </p>
                <Button asChild className="bg-purple-600 hover:bg-purple-700" size="lg">
                  <Link href="/listings/create">
                    <Plus className="w-5 h-5 mr-2" />
                    Create Your First Listing
                  </Link>
                </Button>
              </div>
            </div>
          ) : filteredListings.length === 0 ? (
            <div className="bg-gray-900 rounded-lg p-12 text-center">
              <div className="max-w-md mx-auto">
                {status === "active" && (
                  <>
                    <h3 className="text-xl font-semibold text-white mb-2">No active listings</h3>
                    <p className="text-gray-400 mb-6">
                      All your listings are currently hidden. Click &ldquo;Inactive&rdquo; to view
                      them.
                    </p>
                  </>
                )}
                {status === "inactive" && (
                  <>
                    <h3 className="text-xl font-semibold text-white mb-2">No hidden listings</h3>
                    <p className="text-gray-400 mb-6">
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
                <div className="grid grid-cols-3 gap-6">
                  {Array.from({ length: DEFAULT_LIMIT }).map((_, i) => (
                    <div key={i} className="flex flex-col gap-2">
                      <div className="aspect-square bg-gray-800 rounded-md animate-pulse" />
                      <div className="h-4 bg-gray-800 rounded animate-pulse" />
                      <div className="h-6 bg-gray-800 rounded animate-pulse w-1/2" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-6">
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
            <p className="text-gray-400">Loading...</p>
          </div>
        }
      >
        <ProfileContent />
      </Suspense>
    </ProtectedRoute>
  );
}
