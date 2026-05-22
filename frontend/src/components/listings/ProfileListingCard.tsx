"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ListingSummary } from "@/types/listing/listing";
import { formatPrice, getConditionColor } from "@/lib/utils";
import { STATIC_BASE_URL, LISTINGS_BASE_URL } from "@/lib/constants";
import { Edit, Eye, EyeOff, Trash2, ImageIcon } from "lucide-react";
import Link from "next/link";
import Image from "next/image";
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
} from "@/components/ui/alert-dialog";

interface ProfileListingCardProps {
  listing: ListingSummary;
  onToggleActive: (id: string, isActive: boolean) => void;
  onDelete: (id: string) => void;
  isTogglingActive?: boolean;
  isDeleting?: boolean;
}

export function ProfileListingCard({
  listing,
  onToggleActive,
  onDelete,
  isTogglingActive = false,
  isDeleting = false,
}: ProfileListingCardProps) {
  const router = useRouter();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const hasImage = listing.thumbnail_url;

  const handleCardClick = (e: React.MouseEvent) => {
    // Don't navigate if clicking on action buttons
    if ((e.target as HTMLElement).closest("button") || (e.target as HTMLElement).closest("a")) {
      return;
    }
    router.push(`${LISTINGS_BASE_URL}/${listing.id}`);
  };

  return (
    <>
      <div
        onClick={handleCardClick}
        className="group relative cursor-pointer overflow-hidden rounded-xl border bg-card backdrop-blur-sm transition-all hover:border-purple-500/50 hover:shadow-lg hover:shadow-purple-500/10"
      >
        {/* Image Section */}
        <div className="relative aspect-square w-full overflow-hidden bg-muted">
          {hasImage ? (
            <>
              <Image
                src={`${STATIC_BASE_URL}${listing.thumbnail_url}`}
                alt={listing.title}
                fill
                sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 25vw"
                className="object-cover"
              />
              <div className="absolute inset-0 bg-black/0 transition-colors group-hover:bg-black/20" />
            </>
          ) : (
            <div className="flex h-full w-full items-center justify-center">
              <ImageIcon className="h-16 w-16 text-muted-foreground" />
            </div>
          )}

          {!listing.is_active && (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/60">
              <span className="rounded-md bg-muted px-3 py-1 text-sm font-medium text-muted-foreground">
                Hidden
              </span>
            </div>
          )}

          {/* Action buttons - show on hover */}
          <div className="absolute top-2 right-2 z-20 flex gap-2 opacity-0 transition-opacity group-hover:opacity-100">
            <Button
              size="icon"
              variant="secondary"
              className="h-9 w-9 border border-purple-400 bg-background/90 text-foreground hover:border-purple-300 hover:bg-muted hover:shadow-lg hover:shadow-purple-500/20"
              asChild
            >
              <Link href={`/listings/${listing.id}/edit`}>
                <Edit className="h-4 w-4" />
              </Link>
            </Button>
            <Button
              size="icon"
              variant="secondary"
              className="h-9 w-9 border border-blue-400 bg-background/90 text-foreground hover:border-blue-300 hover:bg-muted hover:shadow-lg hover:shadow-blue-500/20"
              onClick={() => onToggleActive(listing.id, !listing.is_active)}
              disabled={isTogglingActive}
            >
              {listing.is_active ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
            <Button
              size="icon"
              variant="secondary"
              className="h-9 w-9 border border-red-400 bg-background/90 text-foreground hover:border-red-300 hover:bg-muted hover:shadow-lg hover:shadow-red-500/20"
              onClick={() => setShowDeleteDialog(true)}
              disabled={isDeleting}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Content Section */}
        <div className="space-y-2 p-4">
          <h3 className="line-clamp-1 text-xl font-bold text-foreground transition-colors group-hover:text-purple-300">
            {listing.title}
          </h3>

          <p className="text-lg font-semibold text-foreground">
            {formatPrice(Number(listing.price))}
          </p>

          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className={`font-medium capitalize ${getConditionColor(listing.condition)}`}>
              {listing.condition.replace("_", " ")}
            </span>
            <span>•</span>
            <span className="capitalize">{listing.category.replace("_", " ")}</span>
          </div>

          <p className="text-sm text-muted-foreground">
            Posted {new Date(listing.created_at).toLocaleDateString()}
          </p>
        </div>
      </div>

      {/* Delete confirmation dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent className="border bg-card">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-foreground">Delete listing?</AlertDialogTitle>
            <AlertDialogDescription className="text-muted-foreground">
              This action cannot be undone. This will permanently delete your listing.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-muted text-foreground hover:bg-muted/80">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 text-white hover:bg-red-700"
              onClick={() => {
                onDelete(listing.id);
                setShowDeleteDialog(false);
              }}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
