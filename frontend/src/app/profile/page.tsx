"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ProfileListingCard } from "@/components/listings/ProfileListingCard";
import { PaginationControls } from "@/components/listings/PaginationControls";
import { DEFAULT_LIMIT } from "@/lib/constants";
import { Plus } from "lucide-react";
import { deleteListing, toggleListingActive } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { createUserListingsQueryOptions } from "@/queryOptions/createUserListingsQueryOptions";
import { toast } from "sonner";

export default function ProfilePage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  // Redirect to login if not authenticated
  if (!authLoading && !isAuthenticated) {
    router.push("/login");
    return null;
  }

  // Show loading while checking auth
  if (authLoading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }

  const offset = parseInt(searchParams.get("offset") ?? "0", 10) || 0;

  const { data, isLoading, isError, error } = useQuery(
    createUserListingsQueryOptions(user.id, {
      limit: DEFAULT_LIMIT,
      offset,
      sort: "recent",
      include_inactive: true,
    })
  );

  // Optimistic toggle mutation
  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      toggleListingActive(id, isActive),
    onMutate: async ({ id, isActive }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: ["user-listings", user.id],
      });

      // Snapshot previous value
      const previousData = queryClient.getQueryData([
        "user-listings",
        user.id,
        { limit: DEFAULT_LIMIT, offset, sort: "recent", include_inactive: true },
      ]);

      // Optimistically update
      queryClient.setQueryData(
        ["user-listings", user.id, { limit: DEFAULT_LIMIT, offset, sort: "recent", include_inactive: true }],
        (old: any) => {
          if (!old) return old;
          return {
            ...old,
            items: old.items.map((item: any) =>
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
          ["user-listings", user.id, { limit: DEFAULT_LIMIT, offset, sort: "recent", include_inactive: true }],
          context.previousData
        );
      }
      toast.error("Failed to update listing visibility");
    },
    onSuccess: (_, { isActive }) => {
      toast.success(isActive ? "Listing is now visible" : "Listing is now hidden");
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["user-listings", user.id],
      });
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteListing,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["user-listings", user.id],
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
        {/* Profile Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">My Profile</h1>
            <p className="text-gray-400">Manage your listings and account settings</p>
          </div>
          <Button asChild className="bg-purple-600 hover:bg-purple-700">
            <Link href="/listings/create">
              <Plus className="w-4 h-4 mr-2" />
              Create Listing
            </Link>
          </Button>
        </div>

        {/* User Stats */}
        {data && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-gray-900 rounded-lg p-6">
              <h3 className="text-gray-400 text-sm font-medium mb-1">Total Listings</h3>
              <p className="text-3xl font-bold text-white">{data.count}</p>
            </div>
            <div className="bg-gray-900 rounded-lg p-6">
              <h3 className="text-gray-400 text-sm font-medium mb-1">Active</h3>
              <p className="text-3xl font-bold text-green-500">
                {data.items.filter((item) => item.is_active).length}
              </p>
            </div>
            <div className="bg-gray-900 rounded-lg p-6">
              <h3 className="text-gray-400 text-sm font-medium mb-1">Inactive</h3>
              <p className="text-3xl font-bold text-gray-500">
                {data.items.filter((item) => !item.is_active).length}
              </p>
            </div>
          </div>
        )}

        {/* Listings Section */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold text-gray-100">Your Listings</h2>
          </div>

          {/* Empty state with CTA */}
          {data && data.count === 0 ? (
            <div className="bg-gray-900 rounded-lg p-12 text-center">
              <div className="max-w-md mx-auto">
                <h3 className="text-xl font-semibold text-white mb-2">No listings yet</h3>
                <p className="text-gray-400 mb-6">
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
                  {data?.items.map((listing) => (
                    <ProfileListingCard
                      key={listing.id}
                      listing={listing}
                      onToggleActive={(id, isActive) =>
                        toggleMutation.mutate({ id, isActive })
                      }
                      onDelete={(id) => deleteMutation.mutate(id)}
                      isTogglingActive={toggleMutation.isPending}
                      isDeleting={deleteMutation.isPending}
                    />
                  ))}
                </div>
              )}

              {/* Pagination controls */}
              {data && data.count > 0 && <PaginationControls count={data.count} />}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
