"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ImageUpload } from "@/components/listings/ImageUpload";
import { createListing, generateListingDescription } from "@/lib/api";
import { CATEGORIES, Category } from "@/types/listing/filters/category";
import { CONDITIONS, Condition } from "@/types/listing/filters/condition";
import { formatCategoryLabel, formatConditionLabel } from "@/lib/utils";
import { toast } from "sonner";
import { showErrorToast } from "@/lib/errorHandling";
import { ProtectedRoute } from "@/components/custom/ProtectedRoute";
import { Loader2, ChevronLeft, Sparkles } from "lucide-react";
import type { ImagePublic } from "@/types/listing/listing";

export default function CreateListingPage() {
  return (
    <ProtectedRoute>
      <CreateListingContent />
    </ProtectedRoute>
  );
}

function CreateListingContent() {
  const router = useRouter();

  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [category, setCategory] = useState<Category | "">("");
  const [condition, setCondition] = useState<Condition | "">("");
  const [isActive, setIsActive] = useState(true);
  const [createdListingId, setCreatedListingId] = useState<string | null>(null);
  const [images, setImages] = useState<ImagePublic[]>([]);

  // Validation errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Validate field
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

  // Handle blur validation
  const handleBlur = (field: string, value: string) => {
    const error = validateField(field, value);
    setErrors((prev) => ({
      ...prev,
      [field]: error,
    }));
  };

  // Format price display
  const handlePriceBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const value = e.target.value;
    handleBlur("price", value);

    // Format to 2 decimal places
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

  // Create mutation
  const createMutation = useMutation({
    mutationFn: () =>
      createListing({
        title,
        description,
        price: parseFloat(price),
        category,
        condition,
        is_active: isActive,
      }),
    onSuccess: (data) => {
      setCreatedListingId(data.id);
      toast.success("Listing created successfully! You can now add images.", {
        style: {
          background: "rgb(20, 83, 45)",
          color: "white",
          border: "1px solid rgb(34, 197, 94)",
        },
      });
    },
    onError: (error) => {
      // Check if it's a verification error
      if (error instanceof Error && error.message.includes("verify your email")) {
        toast.error(
          "Please verify your email to create listings. Check your inbox for the verification link or resend from your account settings.",
          {
            duration: 6000,
          },
        );
      } else {
        showErrorToast(error, "Failed to create listing");
      }
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
      createMutation.mutate();
    }
  };

  const handleDone = () => {
    router.push("/profile");
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-3xl">
        {/* Breadcrumb Navigation */}
        <button
          onClick={() => router.back()}
          className="group mb-6 flex cursor-pointer items-center gap-2 text-gray-400 transition-colors hover:text-white"
        >
          <ChevronLeft className="h-4 w-4 transition-transform group-hover:-translate-x-1" />
          <span className="text-sm font-medium">Back</span>
        </button>

        {/* Header */}
        <div className="mb-8">
          <h1 className="mb-2 text-2xl font-bold text-foreground">Create New Listing</h1>
          <p className="text-sm text-muted-foreground">
            Fill in the details to create your listing
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Show info about creating listing first if not created yet */}
          {!createdListingId && (
            <div className="rounded-lg border border-blue-500/30 bg-blue-500/10 p-4">
              <p className="text-sm text-blue-600 dark:text-blue-300">
                💡 Create your listing first, then you&apos;ll be able to upload images
              </p>
            </div>
          )}

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
              placeholder="e.g., iPhone 13 Pro Max"
              disabled={!!createdListingId}
              maxLength={100}
              className={`mt-1 ${errors.title ? "border-red-500" : ""}`}
            />
            {errors.title && <p className="mt-1 text-sm text-red-500">{errors.title}</p>}
            <p className="mt-1 text-xs text-muted-foreground">{title.length}/100 characters</p>
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
              disabled={!!createdListingId}
              className={`mt-1 h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm text-foreground shadow-xs transition-[color,box-shadow] outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 ${
                errors.category ? "border-red-500" : ""
              }`}
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
              disabled={!!createdListingId}
              className={`mt-1 h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm text-foreground shadow-xs transition-[color,box-shadow] outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 ${
                errors.condition ? "border-red-500" : ""
              }`}
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
                disabled={
                  !title.trim() ||
                  !category ||
                  !condition ||
                  !!createdListingId ||
                  generateDescriptionMutation.isPending
                }
                title={
                  !category || !condition ? "Add a title, category, and condition first" : undefined
                }
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
              placeholder="Describe your item..."
              rows={4}
              maxLength={500}
              disabled={!!createdListingId}
              className={`mt-1 resize-none ${errors.description ? "border-red-500" : ""}`}
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
                placeholder="0.00"
                disabled={!!createdListingId}
                className={`h-12 pl-8 text-lg ${errors.price ? "border-red-500" : ""}`}
              />
            </div>
            {errors.price && <p className="mt-1 text-sm text-red-500">{errors.price}</p>}
          </div>

          {/* Active Status */}
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
                  disabled={!!createdListingId}
                  className="peer sr-only"
                />
                <div className="peer h-6 w-11 rounded-full bg-gray-700 peer-checked:bg-purple-600 peer-focus:ring-4 peer-focus:ring-purple-800 peer-focus:outline-none after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white rtl:peer-checked:after:-translate-x-full"></div>
              </label>
            </div>
          </div>

          {/* Image Upload - shown after listing is created */}
          {createdListingId && (
            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="mb-4 text-lg font-semibold text-foreground">Add Images</h3>
              <ImageUpload
                listingId={createdListingId}
                existingImages={images}
                onImagesChange={setImages}
              />
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-4 pt-4">
            {!createdListingId ? (
              <>
                <Button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="bg-purple-600 text-white hover:bg-purple-700"
                >
                  {createMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    "Create Listing"
                  )}
                </Button>
                <Button type="button" variant="outline" asChild>
                  <Link href="/profile">Cancel</Link>
                </Button>
              </>
            ) : (
              <Button
                type="button"
                onClick={handleDone}
                className="bg-purple-600 text-white hover:bg-purple-700"
              >
                Done
              </Button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
