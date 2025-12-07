"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { getListing, updateListing, deleteListingImage } from "@/lib/api";
import { CATEGORIES, Category } from "@/types/listing/filters/category";
import { CONDITIONS, Condition } from "@/types/listing/filters/condition";
import { formatCategoryLabel, formatConditionLabel } from "@/lib/utils";
import { toast } from "sonner";
import { Loader2, ChevronLeft, Check } from "lucide-react";
import type { ImagePublic } from "@/types/listing/listing";

export default function EditListingPage() {
  const params = useParams();
  const router = useRouter();
  const listingId = params.listing_id as string;
  const queryClient = useQueryClient();

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

  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [category, setCategory] = useState<Category | "">("");
  const [condition, setCondition] = useState<Condition | "">("");
  const [isActive, setIsActive] = useState(true);
  const [images, setImages] = useState<ImagePublic[]>([]);
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
  const [isDirty, setIsDirty] = useState(false);
  const [showDiscardDialog, setShowDiscardDialog] = useState(false);
  const [showSavedIndicator, setShowSavedIndicator] = useState(false);
  const justSavedRef = useRef(false);

  // Initialize form with listing data
  useEffect(() => {
    if (listing) {
      setTitle(listing.title);
      setDescription(listing.description || "");
      setPrice(listing.price.toString());
      setCategory(listing.category);
      setCondition(listing.condition);
      setIsActive(listing.is_active);
      setImages(listing.images || []);

      if (justSavedRef.current) {
        justSavedRef.current = false;
      }
    }
  }, [listing]);

  useEffect(() => {
    if (!listing) return;

    if (justSavedRef.current) return;

    const hasChanged =
      title !== listing.title ||
      description !== (listing.description || "") ||
      price !== listing.price.toString() ||
      category !== listing.category ||
      condition !== listing.condition ||
      isActive !== listing.is_active ||
      pendingImageDeletions.length > 0 ||
      newImageUploads.length > 0;

    setIsDirty(hasChanged);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    title,
    description,
    price,
    category,
    condition,
    isActive,
    pendingImageDeletions,
    newImageUploads,
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
        const priceNum = parseFloat(value);
        if (!value) return "Price is required";
        if (isNaN(priceNum)) return "Price must be a valid number";
        if (priceNum < 0.01) return "Price must be at least $0.01";
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
          pendingImageDeletions.map((imageId) => deleteListingImage(listingId, imageId))
        );
      }

      await updateListing(listingId, {
        title,
        description: description || undefined,
        price: parseFloat(price),
        category,
        condition,
        is_active: isActive,
      });
    },
    onSuccess: async () => {
      // Prevents dirty state recalculation during refetch
      justSavedRef.current = true;

      setIsDirty(false);
      setPendingImageDeletions([]);
      setNewImageUploads([]);

      setClearImageStates(true);
      setTimeout(() => setClearImageStates(false), 100);

      await queryClient.invalidateQueries({ queryKey: ["listing", listingId] });

      toast.success("Changes saved successfully");

      setShowSavedIndicator(true);
      setTimeout(() => setShowSavedIndicator(false), 2000);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to update listing");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      updateMutation.mutate();
    }
  };

  const handleBack = () => {
    if (isDirty) {
      setShowDiscardDialog(true);
    } else {
      router.push("/profile");
    }
  };

  const handleCancel = () => {
    if (isDirty) {
      setShowDiscardDialog(true);
    } else {
      router.push("/profile");
    }
  };

  const handleDiscardChanges = async () => {
    if (newImageUploads.length > 0) {
      try {
        await Promise.all(newImageUploads.map((imageId) => deleteListingImage(listingId, imageId)));
      } catch (error) {
        console.error("Failed to delete new images:", error);
      }
    }
    router.push("/profile");
  };

  if (isError) {
    return (
      <div className="min-h-screen bg-gray-950 p-8 flex items-center justify-center">
        <div className="text-center max-w-md">
          <h1 className="text-2xl font-bold text-white mb-2">Error Loading Listing</h1>
          <p className="text-gray-400 mb-6">
            {error.message || "Listing not found or you don't have permission to edit it."}
          </p>
          <Button asChild variant="outline">
            <Link href="/profile">Back to Profile</Link>
          </Button>
        </div>
      </div>
    );
  }

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 p-8">
        <div className="max-w-3xl mx-auto space-y-6">
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

  return (
    <div className="min-h-screen bg-gray-950 p-8">
      <div className="max-w-3xl mx-auto">
        {/* Breadcrumb Navigation */}
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-6 group"
        >
          <ChevronLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm font-medium">Back to Profile</span>
        </button>

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Edit Listing</h1>
              <p className="text-gray-400">Update your listing details</p>
            </div>
            {showSavedIndicator && (
              <div className="flex items-center gap-2 text-green-400 bg-green-950/50 px-4 py-2 rounded-md border border-green-800 animate-in fade-in slide-in-from-right-5">
                <Check className="w-5 h-5" />
                <span className="font-medium">Saved</span>
              </div>
            )}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Title */}
          <div>
            <Label htmlFor="title" className="text-gray-200">
              Title <span className="text-red-500">*</span>
            </Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={(e) => handleBlur("title", e.target.value)}
              maxLength={100}
              className="mt-1 bg-gray-900 border-gray-700 text-white"
              placeholder="e.g., MacBook Pro 2020"
            />
            {errors.title && <p className="text-red-500 text-sm mt-1">{errors.title}</p>}
            <p className="text-gray-500 text-sm mt-1">{title.length}/100 characters</p>
          </div>

          {/* Description */}
          <div>
            <Label htmlFor="description" className="text-gray-200">
              Description <span className="text-red-500">*</span>
            </Label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onBlur={(e) => handleBlur("description", e.target.value)}
              maxLength={500}
              rows={4}
              className="mt-1 w-full rounded-md bg-gray-900 border border-gray-700 text-white p-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="Describe your item..."
            />
            {errors.description && (
              <p className="text-red-500 text-sm mt-1">{errors.description}</p>
            )}
            <p className="text-gray-500 text-sm mt-1">{description.length}/500 characters</p>
          </div>

          {/* Price */}
          <div>
            <Label htmlFor="price" className="text-gray-200">
              Price <span className="text-red-500">*</span>
            </Label>
            <Input
              id="price"
              type="number"
              step="0.01"
              min="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              onBlur={handlePriceBlur}
              className="mt-1 bg-gray-900 border-gray-700 text-white"
              placeholder="0.00"
            />
            {errors.price && <p className="text-red-500 text-sm mt-1">{errors.price}</p>}
          </div>

          {/* Category */}
          <div>
            <Label htmlFor="category" className="text-gray-200">
              Category <span className="text-red-500">*</span>
            </Label>
            <select
              id="category"
              value={category}
              onChange={(e) => setCategory(e.target.value as Category)}
              onBlur={(e) => handleBlur("category", e.target.value)}
              className="mt-1 w-full rounded-md bg-gray-900 border border-gray-700 text-white p-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="">Select a category</option>
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {formatCategoryLabel(cat)}
                </option>
              ))}
            </select>
            {errors.category && <p className="text-red-500 text-sm mt-1">{errors.category}</p>}
          </div>

          {/* Condition */}
          <div>
            <Label htmlFor="condition" className="text-gray-200">
              Condition <span className="text-red-500">*</span>
            </Label>
            <select
              id="condition"
              value={condition}
              onChange={(e) => setCondition(e.target.value as Condition)}
              onBlur={(e) => handleBlur("condition", e.target.value)}
              className="mt-1 w-full rounded-md bg-gray-900 border border-gray-700 text-white p-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="">Select a condition</option>
              {CONDITIONS.map((cond) => (
                <option key={cond} value={cond}>
                  {formatConditionLabel(cond)}
                </option>
              ))}
            </select>
            {errors.condition && <p className="text-red-500 text-sm mt-1">{errors.condition}</p>}
          </div>

          {/* Active Toggle */}
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-gray-200 font-medium">Listing Status</Label>
                <p className="text-gray-500 text-sm mt-1">
                  {isActive ? "Visible to buyers" : "Hidden from buyers"}
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-800 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>
          </div>

          {/* Image Upload */}
          <div className="bg-gray-900 rounded-lg p-6">
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
          <div className="flex items-center justify-between pt-4 border-t border-gray-800">
            <div className="flex gap-3">
              <Button
                type="submit"
                disabled={!isDirty || updateMutation.isPending}
                className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-800 disabled:text-gray-500 disabled:cursor-not-allowed"
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
                <span className="flex items-center text-sm text-yellow-500">
                  <span className="inline-block w-2 h-2 bg-yellow-500 rounded-full mr-2 animate-pulse" />
                  Unsaved changes
                </span>
              )}
            </div>
            {!isDirty ? (
              <Button
                type="button"
                variant="ghost"
                onClick={() => router.push("/profile")}
                className="text-gray-400 hover:text-white"
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Done
              </Button>
            ) : (
              <Button
                type="button"
                variant="ghost"
                onClick={handleCancel}
                className="text-red-400 hover:text-red-300 hover:bg-red-950/30"
              >
                Cancel
              </Button>
            )}
          </div>
        </form>

        {/* Discard changes dialog */}
        <AlertDialog open={showDiscardDialog} onOpenChange={setShowDiscardDialog}>
          <AlertDialogContent className="bg-gray-900 border-gray-800">
            <AlertDialogHeader>
              <AlertDialogTitle className="text-white">Leave without saving?</AlertDialogTitle>
              <AlertDialogDescription className="text-gray-400">
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
              <AlertDialogCancel className="bg-gray-800 text-gray-100 hover:bg-gray-700">
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
