"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
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
import { ImageUpload } from "@/components/listings/ImageUpload";
import {
  getListing,
  updateListing,
  deleteListingImage,
  generateListingDescription,
} from "@/lib/api";
import { CATEGORIES, Category } from "@/types/listing/filters/category";
import { CONDITIONS, Condition } from "@/types/listing/filters/condition";
import { formatCategoryLabel, formatConditionLabel } from "@/lib/utils";
import { toast } from "sonner";
import { showErrorToast } from "@/lib/errorHandling";
import { ProtectedRoute } from "@/components/custom/ProtectedRoute";
import { Loader2, ChevronLeft, Check, Sparkles } from "lucide-react";
import type { ImagePublic, ListingPublic } from "@/types/listing/listing";

export default function EditListingPage() {
  return (
    <ProtectedRoute>
      <EditListingContent />
    </ProtectedRoute>
  );
}

function EditListingContent() {
  const params = useParams();
  const router = useRouter();
  const listingId = params.listing_id as string;

  // Fetch existing listing
  const {
    data: listing,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["listing", listingId],
    queryFn: () => getListing(listingId),
  });

  // Render loading/error states first
  if (isError) {
    return <ErrorView error={error} />;
  }

  if (isLoading || !listing) {
    return <LoadingView />;
  }

  // Once we have listing data, render the form with key based on listing ID
  // This ensures component remounts only when navigating between different listings
  return <EditForm key={listing.id} listing={listing} listingId={listingId} router={router} />;
}

// Separate component that gets remounted when listing changes (via key prop)
function EditForm({
  listing,
  listingId,
  router,
}: {
  listing: ListingPublic;
  listingId: string;
  router: ReturnType<typeof useRouter>;
}) {
  const queryClient = useQueryClient();

  // Form state initialized from listing
  const [title, setTitle] = useState(listing.title);
  const [description, setDescription] = useState(listing.description || "");
  const [price, setPrice] = useState(listing.price.toString());
  const [category, setCategory] = useState<Category | "">(listing.category);
  const [condition, setCondition] = useState<Condition | "">(listing.condition);
  const [isActive, setIsActive] = useState(listing.is_active);
  const [images, setImages] = useState<ImagePublic[]>(listing.images || []);
  const [pendingImageDeletions, setPendingImageDeletions] = useState<string[]>([]);
  const [newImageUploads, setNewImageUploads] = useState<string[]>([]);
  const [clearImageStates, setClearImageStates] = useState(false);

  // Use useCallback to prevent function recreation causing infinite loops
  const handlePendingDeletionsChange = useCallback((deletions: string[]) => {
    setPendingImageDeletions(deletions);
  }, []);

  const handleNewUploadsChange = useCallback((uploads: string[]) => {
    setNewImageUploads(uploads);
  }, []);

  // Validation errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Track if form is dirty
  const [showDiscardDialog, setShowDiscardDialog] = useState(false);
  const [showSavedIndicator, setShowSavedIndicator] = useState(false);

  // Calculate dirty state - derived from form state
  const isDirty = useMemo(() => {
    return (
      title !== listing.title ||
      description !== (listing.description || "") ||
      price !== listing.price.toString() ||
      category !== listing.category ||
      condition !== listing.condition ||
      isActive !== listing.is_active ||
      pendingImageDeletions.length > 0 ||
      newImageUploads.length > 0
    );
  }, [
    listing,
    title,
    description,
    price,
    category,
    condition,
    isActive,
    pendingImageDeletions.length,
    newImageUploads.length,
  ]);

  // Warn before leaving with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [isDirty]);

  // Auto-hide saved indicator after 2 seconds
  useEffect(() => {
    if (showSavedIndicator) {
      const timer = setTimeout(() => setShowSavedIndicator(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [showSavedIndicator]);

  const validateField = (field: string, value: string): string => {
    switch (field) {
      case "title":
        if (!value.trim()) return "Title is required";
        if (value.length > 100) return "Title must be 100 characters or less";
        return "";
      case "description":
        if (!value.trim()) return "Description is required";
        if (value.length > 500) return "Description must be 500 characters or less";
        return "";
      case "price":
        if (!value || !value.trim()) return "Price is required";
        const priceNum = parseFloat(value);
        if (isNaN(priceNum)) return "Price must be a valid number";
        if (priceNum < 0.01) return "Price must be at least $0.01";
        if (priceNum > 99999999.99) return "Price must be less than $100,000,000";
        if (!/^\d+(\.\d{1,2})?$/.test(value)) return "Price must have at most 2 decimal places";
        return "";
      case "category":
        if (!value) return "Category is required";
        return "";
      case "condition":
        if (!value) return "Condition is required";
        return "";
      default:
        return "";
    }
  };

  const handleBlur = (field: string, value: string) => {
    const error = validateField(field, value);
    setErrors((prev) => ({
      ...prev,
      [field]: error,
    }));
  };

  const handlePriceBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const value = e.target.value;
    handleBlur("price", value);

    if (value && !isNaN(parseFloat(value))) {
      setPrice(parseFloat(value).toFixed(2));
    }
  };

  // Validate all fields
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {
      title: validateField("title", title),
      description: validateField("description", description),
      price: validateField("price", price),
      category: validateField("category", category),
      condition: validateField("condition", condition),
    };

    setErrors(newErrors);
    return !Object.values(newErrors).some((error) => error !== "");
  };

  const updateMutation = useMutation({
    mutationFn: async () => {
      if (pendingImageDeletions.length > 0) {
        await Promise.all(
          pendingImageDeletions.map((imageId) => deleteListingImage(listingId, imageId)),
        );
      }

      return await updateListing(listingId, {
        title,
        description: description || undefined,
        price: parseFloat(price),
        category,
        condition,
        is_active: isActive,
      });
    },
    onSuccess: async (updatedListing) => {
      // Update local images state with server response
      if (updatedListing?.images) {
        setImages(updatedListing.images);
      }

      // Reset pending changes
      setPendingImageDeletions([]);
      setNewImageUploads([]);
      setClearImageStates(true);

      // Refetch listing data to ensure consistency
      await queryClient.invalidateQueries({ queryKey: ["listing", listingId] });

      // Reset clear flag after state propagates
      setClearImageStates(false);

      toast.success("Changes saved successfully", {
        style: {
          background: "rgb(20, 83, 45)",
          color: "white",
          border: "1px solid rgb(34, 197, 94)",
        },
      });
      setShowSavedIndicator(true);
    },
    onError: (error) => {
      showErrorToast(error, "Failed to update listing");
    },
  });

  const generateDescriptionMutation = useMutation({
    mutationFn: () =>
      generateListingDescription({
        title,
        category: category || undefined,
        condition: condition || undefined,
      }),
    onSuccess: (data) => {
      setDescription(data.description.slice(0, 500));
      setErrors((prev) => ({ ...prev, description: "" }));
      toast.success("Description generated. Feel free to edit it.");
    },
    onError: (error) => showErrorToast(error, "Failed to generate description"),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      updateMutation.mutate();
    }
  };

  const handleNavigateBack = useCallback(() => {
    if (isDirty) {
      setShowDiscardDialog(true);
    } else {
      router.back();
    }
  }, [isDirty, router]);

  const handleDiscardChanges = async () => {
    if (newImageUploads.length > 0) {
      try {
        await Promise.all(newImageUploads.map((imageId) => deleteListingImage(listingId, imageId)));
      } catch (error) {
        console.error("Failed to delete new images:", error);
      }
    }
    router.back();
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-3xl">
        {/* Breadcrumb Navigation */}
        <button
          onClick={handleNavigateBack}
          className="group mb-6 flex cursor-pointer items-center gap-2 text-gray-400 transition-colors hover:text-white"
        >
          <ChevronLeft className="h-4 w-4 transition-transform group-hover:-translate-x-1" />
          <span className="text-sm font-medium">Back</span>
        </button>

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="mb-2 text-2xl font-bold text-foreground">Edit Listing</h1>
              <p className="text-sm text-muted-foreground">Update your listing details</p>
            </div>
            {showSavedIndicator && (
              <div className="flex animate-in items-center gap-2 rounded-md border border-green-800 bg-green-950/50 px-4 py-2 text-green-400 slide-in-from-right-5 fade-in">
                <Check className="h-5 w-5" />
                <span className="font-medium">Saved</span>
              </div>
            )}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Title */}
          <div>
            <Label htmlFor="title" className="text-foreground">
              Title <span className="text-red-500">*</span>
            </Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={(e) => handleBlur("title", e.target.value)}
              maxLength={100}
              className="mt-1"
              placeholder="e.g., MacBook Pro 2020"
            />
            {errors.title && <p className="mt-1 text-sm text-red-500">{errors.title}</p>}
            <p className="mt-1 text-xs text-muted-foreground">{title.length}/100 characters</p>
          </div>

          {/* Description */}
          <div>
            <div className="flex items-center justify-between">
              <Label htmlFor="description" className="text-foreground">
                Description <span className="text-red-500">*</span>
              </Label>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={() => generateDescriptionMutation.mutate()}
                disabled={!title.trim() || generateDescriptionMutation.isPending}
                className="h-7 gap-1 px-2 text-xs text-purple-600 hover:text-purple-700 dark:text-purple-300"
              >
                {generateDescriptionMutation.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Sparkles className="h-3.5 w-3.5" />
                )}
                Generate
              </Button>
            </div>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onBlur={(e) => handleBlur("description", e.target.value)}
              maxLength={500}
              rows={4}
              className="mt-1 resize-none"
              placeholder="Describe your item..."
            />
            {errors.description && (
              <p className="mt-1 text-sm text-red-500">{errors.description}</p>
            )}
            <p className="mt-1 text-xs text-muted-foreground">
              {description.length}/500 characters
            </p>
          </div>

          {/* Price */}
          <div>
            <Label htmlFor="price" className="text-foreground">
              Price <span className="text-red-500">*</span>
            </Label>
            <div className="relative mt-1">
              <span className="absolute top-1/2 left-3 -translate-y-1/2 text-lg text-muted-foreground">
                $
              </span>
              <Input
                id="price"
                type="number"
                step="0.01"
                min="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                onBlur={handlePriceBlur}
                className="h-12 pl-8 text-lg"
                placeholder="0.00"
              />
            </div>
            {errors.price && <p className="mt-1 text-sm text-red-500">{errors.price}</p>}
          </div>

          {/* Category */}
          <div>
            <Label htmlFor="category" className="text-foreground">
              Category <span className="text-red-500">*</span>
            </Label>
            <select
              id="category"
              value={category}
              onChange={(e) => setCategory(e.target.value as Category)}
              onBlur={(e) => handleBlur("category", e.target.value)}
              className="mt-1 h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 dark:bg-input/30"
            >
              <option value="">Select a category</option>
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {formatCategoryLabel(cat)}
                </option>
              ))}
            </select>
            {errors.category && <p className="mt-1 text-sm text-red-500">{errors.category}</p>}
          </div>

          {/* Condition */}
          <div>
            <Label htmlFor="condition" className="text-foreground">
              Condition <span className="text-red-500">*</span>
            </Label>
            <select
              id="condition"
              value={condition}
              onChange={(e) => setCondition(e.target.value as Condition)}
              onBlur={(e) => handleBlur("condition", e.target.value)}
              className="mt-1 h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 dark:bg-input/30"
            >
              <option value="">Select a condition</option>
              {CONDITIONS.map((cond) => (
                <option key={cond} value={cond}>
                  {formatConditionLabel(cond)}
                </option>
              ))}
            </select>
            {errors.condition && <p className="mt-1 text-sm text-red-500">{errors.condition}</p>}
          </div>

          {/* Active Toggle */}
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="flex items-center justify-between">
              <div>
                <Label className="font-medium text-foreground">Listing Status</Label>
                <p className="mt-1 text-sm text-muted-foreground">
                  {isActive ? "Visible to buyers" : "Hidden from buyers"}
                </p>
              </div>
              <label className="relative inline-flex cursor-pointer items-center">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="peer sr-only"
                />
                <div className="peer h-6 w-11 rounded-full bg-gray-700 peer-checked:bg-purple-600 peer-focus:ring-4 peer-focus:ring-purple-800 peer-focus:outline-none after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white rtl:peer-checked:after:-translate-x-full"></div>
              </label>
            </div>
          </div>

          {/* Image Upload */}
          <div className="rounded-lg border border-border bg-card p-6">
            <ImageUpload
              listingId={listingId}
              existingImages={images}
              onImagesChange={setImages}
              onPendingDeletions={handlePendingDeletionsChange}
              onNewUploads={handleNewUploadsChange}
              clearPendingDeletions={clearImageStates}
              clearNewUploads={clearImageStates}
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-4">
            <div className="flex gap-3">
              <Button
                type="submit"
                disabled={!isDirty || updateMutation.isPending}
                className="bg-purple-600 text-white hover:bg-purple-700 disabled:cursor-not-allowed disabled:bg-gray-800 disabled:text-gray-500"
              >
                {updateMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  "Save Changes"
                )}
              </Button>
              {isDirty && !updateMutation.isPending && (
                <span className="flex items-center text-sm text-blue-600 dark:text-blue-300">
                  <span className="mr-2 inline-block h-2 w-2 animate-pulse rounded-full bg-blue-600 dark:bg-blue-300" />
                  Unsaved changes
                </span>
              )}
            </div>
            {!isDirty ? (
              <Button
                type="button"
                variant="ghost"
                onClick={() => router.push("/profile")}
                className="text-muted-foreground hover:text-foreground"
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Done
              </Button>
            ) : (
              <Button
                type="button"
                variant="ghost"
                onClick={handleNavigateBack}
                className="text-red-400 hover:bg-red-950/30 hover:text-red-300"
              >
                Cancel
              </Button>
            )}
          </div>
        </form>

        {/* Discard changes dialog */}
        <AlertDialog open={showDiscardDialog} onOpenChange={setShowDiscardDialog}>
          <AlertDialogContent className="border-border bg-card">
            <AlertDialogHeader>
              <AlertDialogTitle className="text-foreground">Leave without saving?</AlertDialogTitle>
              <AlertDialogDescription className="text-muted-foreground">
                You have unsaved changes that will be lost if you leave now.
                {newImageUploads.length > 0 && (
                  <>
                    <br />
                    <br />
                    <strong className="text-yellow-400">
                      {newImageUploads.length} newly uploaded image
                      {newImageUploads.length > 1 ? "s" : ""} will be deleted.
                    </strong>
                  </>
                )}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel className="bg-muted text-foreground hover:bg-muted/80">
                Stay and Save
              </AlertDialogCancel>
              <AlertDialogAction
                className="bg-red-600 text-white hover:bg-red-700"
                onClick={handleDiscardChanges}
              >
                Leave Without Saving
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
}

// Error view component
function ErrorView({ error }: { error: Error }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-8">
      <div className="max-w-md text-center">
        <h1 className="mb-2 text-2xl font-bold text-foreground">Error Loading Listing</h1>
        <p className="mb-6 text-muted-foreground">
          {error.message || "Listing not found or you don't have permission to edit it."}
        </p>
        <Button asChild variant="outline">
          <Link href="/profile">Back to Profile</Link>
        </Button>
      </div>
    </div>
  );
}

// Loading skeleton component
function LoadingView() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-3xl space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-6 w-96" />
        <div className="space-y-6">
          <Skeleton className="h-20" />
          <Skeleton className="h-32" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="aspect-square w-full max-w-md" />
        </div>
      </div>
    </div>
  );
}
