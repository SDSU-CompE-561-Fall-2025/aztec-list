"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Image from "next/image";
import Link from "next/link";
import { ImageIcon, ShieldCheck, ExternalLink } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";
import { showErrorToast } from "@/lib/errorHandling";
import { STATIC_BASE_URL, LISTINGS_BASE_URL } from "@/lib/constants";
import { formatPrice } from "@/lib/utils";
import {
  getFlaggedListings,
  approveFlaggedListing,
  adminRemoveListing,
  type FlaggedListing,
} from "@/lib/api";

const REMOVE_REASON = "Removed via moderation review";

function thumbnailUrl(path: string | null): string | null {
  if (!path) return null;
  return path.startsWith("http") ? path : `${STATIC_BASE_URL}${path}`;
}

export function FlaggedListingsView() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["flaggedListings"],
    queryFn: getFlaggedListings,
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["flaggedListings"] });
    queryClient.invalidateQueries({ queryKey: ["adminActions"] });
  };

  const approveMutation = useMutation({
    mutationFn: approveFlaggedListing,
    onSuccess: () => {
      refresh();
      toast.success("Listing approved and restored.");
    },
    onError: (error) => showErrorToast(error, "Failed to approve listing"),
  });

  const removeMutation = useMutation({
    mutationFn: (listingId: string) => adminRemoveListing(listingId, REMOVE_REASON),
    onSuccess: () => {
      refresh();
      toast.success("Listing removed.");
    },
    onError: (error) => showErrorToast(error, "Failed to remove listing"),
  });

  const items: FlaggedListing[] = data?.items ?? [];
  const pending = approveMutation.isPending || removeMutation.isPending;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="mx-auto mb-3 h-10 w-10 animate-spin rounded-full border-b-2 border-purple-600"></div>
          <p className="text-sm text-muted-foreground">Loading flagged listings...</p>
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <Card className="border bg-card">
        <CardContent className="py-12 text-center">
          <ShieldCheck className="mx-auto mb-3 h-12 w-12 text-muted-foreground" />
          <p className="text-muted-foreground">No flagged listings. The queue is clear.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => {
        const image = thumbnailUrl(item.listing.thumbnail_url);
        return (
          <Card key={item.action_id} className="border bg-card">
            <CardContent className="p-4">
              <div className="flex items-start gap-4">
                {/* Thumbnail */}
                <div className="relative h-20 w-20 flex-shrink-0 overflow-hidden rounded-md bg-muted">
                  {image ? (
                    <Image
                      src={image}
                      alt={item.listing.title}
                      fill
                      sizes="80px"
                      className="object-cover"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center">
                      <ImageIcon className="h-8 w-8 text-muted-foreground" />
                    </div>
                  )}
                </div>

                {/* Details */}
                <div className="min-w-0 flex-1 space-y-1">
                  <Link
                    href={`${LISTINGS_BASE_URL}/${item.listing.id}`}
                    className="inline-flex items-center gap-1 text-base font-semibold text-foreground hover:text-purple-400"
                  >
                    <span className="truncate">{item.listing.title}</span>
                    <ExternalLink className="h-3.5 w-3.5 flex-shrink-0" />
                  </Link>
                  <p className="text-sm font-medium text-foreground">
                    {formatPrice(item.listing.price)}
                  </p>
                  <p className="text-sm text-yellow-500 dark:text-yellow-400">
                    <span className="font-medium">Flagged:</span> {item.reason ?? "Policy review"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(item.flagged_at).toLocaleString()}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex flex-shrink-0 flex-col gap-2">
                  <Button
                    size="sm"
                    onClick={() => approveMutation.mutate(item.listing.id)}
                    disabled={pending}
                    className="bg-green-600 text-white hover:bg-green-700"
                  >
                    Approve
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button size="sm" variant="destructive" disabled={pending}>
                        Remove
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Remove this listing?</AlertDialogTitle>
                        <AlertDialogDescription>
                          This deletes the listing and issues a strike to its owner. This cannot be
                          undone.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={() => removeMutation.mutate(item.listing.id)}
                          className="text-destructive-foreground bg-destructive hover:bg-destructive/90"
                        >
                          Remove
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
