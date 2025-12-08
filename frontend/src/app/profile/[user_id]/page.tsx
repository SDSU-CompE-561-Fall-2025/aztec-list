"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { PaginationControls } from "@/components/listings/PaginationControls";
import { API_BASE_URL, DEFAULT_LIMIT, STATIC_BASE_URL } from "@/lib/constants";
import { ChevronLeft, User, Mail, Phone, Building2, Calendar } from "lucide-react";
import { createUserQueryOptions } from "@/queryOptions/createUserQueryOptions";
import { createUserListingsQueryOptions } from "@/queryOptions/createUserListingsQueryOptions";
import type { ListingSummary } from "@/types/listing/listing";
import { Suspense } from "react";
import { UserListingCard } from "@/components/listings/UserListingCard";

// Helper function to build full URL for profile picture
const getProfilePictureUrl = (path: string | null | undefined): string | null => {
  if (!path) return null;
  const timestamp = Date.now();
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return `${path}?t=${timestamp}`;
  }
  return `${STATIC_BASE_URL}${path}?t=${timestamp}`;
};

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
  const { data: profileData } = useQuery({
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
    })
  );

  const isLoading = isUserLoading || isListingsLoading;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950">
        <div className="border-b border-gray-800/50 bg-gray-950/95 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="h-10 w-40 bg-gray-800 rounded animate-pulse" />
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="space-y-6">
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6 h-32 animate-pulse" />
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl h-80 animate-pulse"
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
            <h1 className="text-2xl font-bold text-gray-100 mb-3">User Not Found</h1>
            <p className="text-gray-400 mb-8 leading-relaxed">
              This user could not be found or may have been removed.
            </p>
            <Button onClick={() => router.push("/")} className="bg-purple-600 hover:bg-purple-700">
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
    <div className="min-h-screen bg-gray-950">
      <div className="border-b border-gray-800/50 bg-gray-950/95 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <Button
            variant="ghost"
            className="text-gray-400 hover:text-gray-100 hover:bg-gray-800/50 -ml-3"
            onClick={() => router.back()}
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* User Profile Header */}
        <div className="bg-gray-900/60 backdrop-blur-sm border border-gray-800/60 rounded-xl p-8">
          <div className="flex items-start gap-6">
            <div className="w-24 h-24 bg-gradient-to-br from-purple-500/20 to-purple-600/20 rounded-full flex items-center justify-center border border-purple-500/20 flex-shrink-0 overflow-hidden relative">
              {profileData?.profile_picture_url ? (
                <Image
                  src={getProfilePictureUrl(profileData.profile_picture_url) || ""}
                  alt={user.username}
                  fill
                  sizes="96px"
                  className="object-cover"
                />
              ) : (
                <User className="w-12 h-12 text-purple-300" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold text-white mb-2">
                {profileData?.name ? (
                  <>
                    {profileData.name}
                    <span className="text-lg text-gray-400 font-normal ml-2">
                      (@{user.username})
                    </span>
                  </>
                ) : (
                  user.username
                )}
              </h1>
              <div className="space-y-2 text-sm">
                {profileData?.campus && (
                  <div className="flex items-center gap-2 text-gray-400">
                    <Building2 className="w-4 h-4 flex-shrink-0" />
                    <span className="truncate">{profileData.campus}</span>
                  </div>
                )}
                <div className="flex items-center gap-2 text-gray-400">
                  <Mail className="w-4 h-4 flex-shrink-0" />
                  <span className="truncate">{user.email}</span>
                </div>
                {profileData?.contact_info?.phone && (
                  <div className="flex items-center gap-2 text-gray-400">
                    <Phone className="w-4 h-4 flex-shrink-0" />
                    <span className="truncate">{profileData.contact_info.phone}</span>
                  </div>
                )}
                <div className="flex items-center gap-2 text-gray-400">
                  <Calendar className="w-4 h-4 flex-shrink-0" />
                  <span>
                    Joined{" "}
                    {new Date(user.created_at).toLocaleDateString("en-US", {
                      month: "long",
                      year: "numeric",
                    })}
                  </span>
                </div>
                {user.is_verified && (
                  <span className="inline-flex items-center px-3 py-1 bg-green-500/10 text-green-300 text-sm font-semibold rounded-full border border-green-500/30">
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
            <h2 className="text-xl font-bold text-white">
              Listings
              <span className="ml-3 text-gray-500 font-normal text-base">({totalCount})</span>
            </h2>
          </div>

          {listings.length === 0 ? (
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-12 text-center">
              <div className="w-16 h-16 bg-gray-800/50 rounded-full flex items-center justify-center mx-auto mb-4">
                <User className="w-8 h-8 text-gray-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-300 mb-2">No Listings Yet</h3>
              <p className="text-gray-500">This user hasn&apos;t posted any listings.</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
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
