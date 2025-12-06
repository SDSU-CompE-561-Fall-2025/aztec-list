"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
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
import { ImageUploadPlaceholder } from "@/components/listings/ImageUploadPlaceholder";
import { getListing, updateListing } from "@/lib/api";
import { CATEGORIES, Category } from "@/types/listing/filters/category";
import { CONDITIONS, Condition } from "@/types/listing/filters/condition";
import { formatCategoryLabel, formatConditionLabel } from "@/lib/utils";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

export default function EditListingPage() {
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

  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [category, setCategory] = useState<Category | "">("");
  const [condition, setCondition] = useState<Condition | "">("");
  const [isActive, setIsActive] = useState(true);

  // Validation errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Track if form is dirty
  const [isDirty, setIsDirty] = useState(false);
  const [showDiscardDialog, setShowDiscardDialog] = useState(false);

  // Initialize form with listing data
  useEffect(() => {
    if (listing) {
      setTitle(listing.title);
      setDescription(listing.description || "");
      setPrice(listing.price.toString());
      setCategory(listing.category);
      setCondition(listing.condition);
      setIsActive(listing.is_active);
    }
  }, [listing]);

  // Track dirty state
  useEffect(() => {
    if (!listing) return;

    const hasChanged =
      title !== listing.title ||
      description !== (listing.description || "") ||
      price !== listing.price.toString() ||
      category !== listing.category ||
      condition !== listing.condition ||
      isActive !== listing.is_active;

    setIsDirty(hasChanged);
  }, [title, description, price, category, condition, isActive, listing]);

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

  // Validate field
  const validateField = (field: string, value: string): string => {
    switch (field) {
      case "title":
        if (!value.trim()) return "Title is required";
        if (value.length > 100) return "Title must be 100 characters or less";
        return "";
      case "description":
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

  // Handle blur validation
  const handleBlur = (field: string, value: string) => {
    const error = validateField(field, value);
    setErrors((prev) => ({
      ...prev,
      [field]: error,
    }));
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

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: () =>
      updateListing(listingId, {
        title,
        description: description || undefined,
        price: parseFloat(price),
        category,
        condition,
        is_active: isActive,
      }),
    onSuccess: () => {
      setIsDirty(false);
      toast.success("Listing updated successfully");
      router.push("/profile");
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

  const handleCancel = () => {
    if (isDirty) {
      setShowDiscardDialog(true);
    } else {
      router.push("/profile");
    }
  };

  // Error state
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
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Edit Listing</h1>
          <p className="text-gray-400">Update your listing details</p>
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
              Description
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
              onBlur={(e) => handleBlur("price", e.target.value)}
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
            <Label className="text-gray-200 block mb-2">
              Condition <span className="text-red-500">*</span>
            </Label>
            <div className="space-y-2">
              {CONDITIONS.map((cond) => (
                <label key={cond} className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="condition"
                    value={cond}
                    checked={condition === cond}
                    onChange={(e) => setCondition(e.target.value as Condition)}
                    onBlur={(e) => handleBlur("condition", e.target.value)}
                    className="w-4 h-4 text-purple-600 focus:ring-purple-500 focus:ring-2"
                  />
                  <span className="text-gray-200">{formatConditionLabel(cond)}</span>
                </label>
              ))}
            </div>
            {errors.condition && <p className="text-red-500 text-sm mt-1">{errors.condition}</p>}
          </div>

          {/* Active Toggle */}
          <div>
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="w-4 h-4 text-purple-600 focus:ring-purple-500 focus:ring-2 rounded"
              />
              <span className="text-gray-200">List is active and visible to buyers</span>
            </label>
          </div>

          {/* Image Placeholder */}
          <div>
            <Label className="text-gray-200 block mb-2">Images</Label>
            <ImageUploadPlaceholder />
          </div>

          {/* Actions */}
          <div className="flex gap-4 pt-4">
            <Button
              type="submit"
              disabled={updateMutation.isPending}
              className="bg-purple-600 hover:bg-purple-700"
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
            <Button type="button" variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
          </div>
        </form>

        {/* Discard changes dialog */}
        <AlertDialog open={showDiscardDialog} onOpenChange={setShowDiscardDialog}>
          <AlertDialogContent className="bg-gray-900 border-gray-800">
            <AlertDialogHeader>
              <AlertDialogTitle className="text-white">Discard unsaved changes?</AlertDialogTitle>
              <AlertDialogDescription className="text-gray-400">
                You have unsaved changes. Are you sure you want to leave? Your changes will be lost.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel className="bg-gray-800 text-gray-100 hover:bg-gray-700">
                Keep Editing
              </AlertDialogCancel>
              <AlertDialogAction
                className="bg-red-600 text-white hover:bg-red-700"
                onClick={() => router.push("/profile")}
              >
                Discard Changes
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
}
