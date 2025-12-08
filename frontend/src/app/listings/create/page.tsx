"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ImageUpload } from "@/components/listings/ImageUpload";
import { createListing } from "@/lib/api";
import { CATEGORIES, Category } from "@/types/listing/filters/category";
import { CONDITIONS, Condition } from "@/types/listing/filters/condition";
import { formatCategoryLabel, formatConditionLabel } from "@/lib/utils";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import type { ImagePublic } from "@/types/listing/listing";

export default function CreateListingPage() {
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
      toast.error(error.message || "Failed to create listing", {
        style: {
          background: "rgb(153, 27, 27)",
          color: "white",
          border: "1px solid rgb(220, 38, 38)",
        },
      });
    },
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
    <div className="min-h-screen bg-gray-950 p-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">Create New Listing</h1>
          <p className="text-gray-400 text-sm">Fill in the details to create your listing</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Show info about creating listing first if not created yet */}
          {!createdListingId && (
            <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
              <p className="text-blue-300 text-sm">
                💡 Create your listing first, then you&apos;ll be able to upload images
              </p>
            </div>
          )}

          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title" className="text-gray-200">
              Title <span className="text-red-500">*</span>
            </Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={(e) => handleBlur("title", e.target.value)}
              placeholder="e.g., iPhone 13 Pro Max"
              disabled={!!createdListingId}
              className={`bg-gray-900 border-gray-700 text-white ${
                errors.title ? "border-red-500" : ""
              }`}
            />
            {errors.title && <p className="text-red-500 text-sm">{errors.title}</p>}
            <p className="text-gray-400 text-xs">{title.length}/100 characters</p>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description" className="text-gray-200">
              Description <span className="text-red-500">*</span>
            </Label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onBlur={(e) => handleBlur("description", e.target.value)}
              placeholder="Describe your item..."
              rows={5}
              disabled={!!createdListingId}
              className={`w-full bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none ${
                errors.description ? "border-red-500" : ""
              }`}
            />
            {errors.description && <p className="text-red-500 text-sm">{errors.description}</p>}
            <p className="text-gray-400 text-xs">{description.length}/500 characters</p>
          </div>

          {/* Price */}
          <div className="space-y-2">
            <Label htmlFor="price" className="text-gray-200">
              Price <span className="text-red-500">*</span>
            </Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
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
                className={`bg-gray-900 border-gray-700 text-white text-base pl-7 ${
                  errors.price ? "border-red-500" : ""
                }`}
              />
            </div>
            {errors.price && <p className="text-red-500 text-sm">{errors.price}</p>}
          </div>

          {/* Category */}
          <div className="space-y-2">
            <Label htmlFor="category" className="text-gray-200">
              Category <span className="text-red-500">*</span>
            </Label>
            <select
              id="category"
              value={category}
              onChange={(e) => setCategory(e.target.value as Category)}
              onBlur={(e) => handleBlur("category", e.target.value)}
              disabled={!!createdListingId}
              className={`w-full bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-white text-base focus:outline-none focus:ring-2 focus:ring-purple-500 ${
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
            {errors.category && <p className="text-red-500 text-sm">{errors.category}</p>}
          </div>

          {/* Condition */}
          <div className="space-y-2">
            <Label htmlFor="condition" className="text-gray-200">
              Condition <span className="text-red-500">*</span>
            </Label>
            <select
              id="condition"
              value={condition}
              onChange={(e) => setCondition(e.target.value as Condition)}
              onBlur={(e) => handleBlur("condition", e.target.value)}
              disabled={!!createdListingId}
              className={`w-full bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-white text-base focus:outline-none focus:ring-2 focus:ring-purple-500 ${
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
            {errors.condition && <p className="text-red-500 text-sm">{errors.condition}</p>}
          </div>

          {/* Active Status */}
          <div className="bg-gray-900 rounded-lg p-3 border border-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-gray-200 font-medium text-sm">Listing Status</Label>
                <p className="text-gray-500 text-sm mt-0.5">
                  {isActive ? "Visible to buyers" : "Hidden from buyers"}
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  disabled={!!createdListingId}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-800 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>
          </div>

          {/* Image Upload - shown after listing is created */}
          {createdListingId && (
            <div className="bg-gray-900 border border-purple-500/30 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Add Images</h3>
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
                  className="bg-purple-600 hover:bg-purple-700 text-white"
                >
                  {createMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
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
                className="bg-purple-600 hover:bg-purple-700 text-white"
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
