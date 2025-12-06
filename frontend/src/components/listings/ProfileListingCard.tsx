"use client";

import { useState } from "react";
import { ListingSummary } from "@/types/listing/listing";
import { formatPrice } from "@/lib/utils";
import { Edit, Eye, EyeOff, Trash2 } from "lucide-react";
import Link from "next/link";
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
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  return (
    <>
      <div className="flex flex-col gap-2 relative group">
        {/* Image with inactive overlay */}
        <div className="relative aspect-square bg-gray-800 rounded-md overflow-hidden">
          {!listing.is_active && (
            <div className="absolute inset-0 bg-gray-950/60 flex items-center justify-center z-10">
              <span className="bg-gray-700 text-gray-300 px-3 py-1 rounded-md text-sm font-medium">
                Hidden
              </span>
            </div>
          )}
        </div>

        {/* Action buttons - show on hover */}
        <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity z-20">
          <Button
            size="icon"
            variant="secondary"
            className="h-8 w-8 bg-gray-900/90 hover:bg-gray-800"
            asChild
          >
            <Link href={`/listings/${listing.id}/edit`}>
              <Edit className="h-4 w-4" />
            </Link>
          </Button>
          <Button
            size="icon"
            variant="secondary"
            className="h-8 w-8 bg-gray-900/90 hover:bg-gray-800"
            onClick={() => onToggleActive(listing.id, !listing.is_active)}
            disabled={isTogglingActive}
          >
            {listing.is_active ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </Button>
          <Button
            size="icon"
            variant="secondary"
            className="h-8 w-8 bg-gray-900/90 hover:bg-red-900"
            onClick={() => setShowDeleteDialog(true)}
            disabled={isDeleting}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>

        {/* Title */}
        <h3 className="text-sm font-medium text-gray-100 line-clamp-2">{listing.title}</h3>

        {/* Price */}
        <p className="text-lg font-semibold text-gray-100">{formatPrice(listing.price)}</p>
      </div>

      {/* Delete confirmation dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent className="bg-gray-900 border-gray-800">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-white">Delete listing?</AlertDialogTitle>
            <AlertDialogDescription className="text-gray-400">
              This action cannot be undone. This will permanently delete your listing.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-gray-800 text-gray-100 hover:bg-gray-700">
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
