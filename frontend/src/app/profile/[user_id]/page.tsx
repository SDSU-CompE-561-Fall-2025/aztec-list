"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { PaginationControls } from "@/components/listings/PaginationControls";
import { API_BASE_URL, DEFAULT_LIMIT } from "@/lib/constants";
import { ChevronLeft, User, Building2, Calendar } from "lucide-react";
import { createUserQueryOptions } from "@/queryOptions/createUserQueryOptions";
import { createUserListingsQueryOptions } from "@/queryOptions/createUserListingsQueryOptions";
import { getProfilePictureUrl } from "@/lib/profile-picture";
import type { ListingSummary } from "@/types/listing/listing";
import { Suspense } from "react";
import { UserListingCard } from "@/components/listings/UserListingCard";

function UserProfileContent() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const userId = params.user_id as string;

  const offset = parseInt(searchParams.get("offset") ?? "0", 10) || 0;

  const {
    data: user,
    isLoading: isUserLoading,
    isError: isUserError,
  } = useQuery(createUserQueryOptions(userId));

  // Fetch user's profile data
  const { data: profileData, isLoading: isProfileDataLoading } = useQuery({
    queryKey: ["profile", userId],
    queryFn: async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/profile`);
        if (!response.ok) return null;
        return response.json();
      } catch {
        return null;
      }
    },
    enabled: !!userId,
  });

  const { data: listingsData, isLoading: isListingsLoading } = useQuery(
    createUserListingsQueryOptions(userId, {
      limit: DEFAULT_LIMIT,
      offset,
      sort: "recent",
    }),
  );

  const isLoading = isUserLoading || isListingsLoading;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="border-b bg-background/95 backdrop-blur-sm">
          <div className="mx-auto max-w-7xl px-6 py-4">
            <div className="h-10 w-40 animate-pulse rounded bg-muted" />
          </div>
        </div>
        <div className="mx-auto max-w-7xl px-6 py-8">
          <div className="space-y-6">
            <div className="h-32 animate-pulse rounded-xl border bg-card p-6 backdrop-blur-sm" />
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="h-80 animate-pulse rounded-xl border bg-card backdrop-blur-sm"
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isUserError || !user) {
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
            <h1 className="mb-3 text-2xl font-bold text-foreground">User Not Found</h1>
            <p className="mb-8 leading-relaxed text-muted-foreground">
              This user could not be found or may have been removed.
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

  const listings = listingsData?.items ?? [];
  const totalCount = listingsData?.count ?? 0;

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
            Back
          </Button>
        </div>
      </div>

      <div className="mx-auto max-w-7xl space-y-8 px-6 py-8">
        {/* User Profile Header */}
        <div className="rounded-xl border bg-card p-8 backdrop-blur-sm">
          <div className="flex items-start gap-6">
            <div className="relative flex h-24 w-24 flex-shrink-0 items-center justify-center overflow-hidden rounded-full border border-purple-500/20 bg-gradient-to-br from-purple-500/20 to-purple-600/20">
              {isProfileDataLoading ? (
                <div className="h-full w-full animate-pulse bg-muted" />
              ) : profileData?.profile_picture_url ? (
                <Image
                  src={
                    getProfilePictureUrl(profileData.profile_picture_url, profileData.updated_at) ||
                    ""
                  }
                  alt={user.username}
                  fill
                  sizes="96px"
                  className="object-cover"
                />
              ) : (
                <User className="h-12 w-12 text-purple-300" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <h1 className="mb-2 text-2xl font-bold text-foreground">
                {isProfileDataLoading ? (
                  <div className="h-8 w-48 animate-pulse rounded bg-muted" />
                ) : profileData?.name ? (
                  <>
                    {profileData.name}
                    <span className="ml-2 text-lg font-normal text-muted-foreground">
                      (@{user.username})
                    </span>
                  </>
                ) : (
                  user.username
                )}
              </h1>
              <div className="space-y-2 text-sm">
                {profileData?.campus && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Building2 className="h-4 w-4 flex-shrink-0" />
                    <span className="truncate">{profileData.campus}</span>
                  </div>
                )}
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="h-4 w-4 flex-shrink-0" />
                  <span>
                    Joined{" "}
                    {new Date(user.created_at).toLocaleDateString("en-US", {
                      month: "long",
                      year: "numeric",
                    })}
                  </span>
                </div>
                {user.is_verified && (
                  <span className="inline-flex items-center rounded-full border border-green-500/30 bg-green-500/10 px-3 py-1 text-sm font-semibold text-green-300">
                    Verified
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Listings Section */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-foreground">
              Listings
              <span className="ml-3 text-base font-normal text-muted-foreground">
                ({totalCount})
              </span>
            </h2>
          </div>

          {listings.length === 0 ? (
            <div className="rounded-xl border bg-card p-12 text-center backdrop-blur-sm">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                <User className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="mb-2 text-xl font-semibold text-foreground">No Listings Yet</h3>
              <p className="text-muted-foreground">This user hasn&apos;t posted any listings.</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
                {listings.map((listing: ListingSummary) => (
                  <UserListingCard key={listing.id} listing={listing} />
                ))}
              </div>

              {totalCount > DEFAULT_LIMIT && (
                <div className="flex justify-center pt-4">
                  <PaginationControls count={totalCount} />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function UserProfilePage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <UserProfileContent />
    </Suspense>
  );
}
