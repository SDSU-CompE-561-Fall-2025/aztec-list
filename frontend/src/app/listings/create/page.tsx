"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ImageUploadPlaceholder } from "@/components/listings/ImageUploadPlaceholder";
import { createListing } from "@/lib/api";
import { CATEGORIES, Category } from "@/types/listing/filters/category";
import { CONDITIONS, Condition } from "@/types/listing/filters/condition";
import { formatCategoryLabel, formatConditionLabel } from "@/lib/utils";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

export default function CreateListingPage() {
  const router = useRouter();

  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [category, setCategory] = useState<Category | "">("");
  const [condition, setCondition] = useState<Condition | "">("");
  const [isActive, setIsActive] = useState(true);

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

  // Create mutation
  const createMutation = useMutation({
    mutationFn: () =>
      createListing({
        title,
        description: description || "",
        price: parseFloat(price),
        category,
        condition,
        is_active: isActive,
      }),
    onSuccess: () => {
      toast.success("Listing created successfully");
      router.push("/profile");
    },
    onError: (error) => {
      toast.error(error.message || "Failed to create listing");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      createMutation.mutate();
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 p-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Create New Listing</h1>
          <p className="text-gray-400">Fill in the details to create your listing</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Image Upload */}
          <div className="space-y-2">
            <Label htmlFor="image" className="text-gray-200">
              Images
            </Label>
            <ImageUploadPlaceholder />
          </div>

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
              className={`bg-gray-900 border-gray-700 text-white ${
                errors.title ? "border-red-500" : ""
              }`}
            />
            {errors.title && <p className="text-red-500 text-sm">{errors.title}</p>}
            <p className="text-gray-400 text-sm">{title.length}/100 characters</p>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description" className="text-gray-200">
              Description
            </Label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onBlur={(e) => handleBlur("description", e.target.value)}
              placeholder="Describe your item..."
              rows={5}
              className={`w-full bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none ${
                errors.description ? "border-red-500" : ""
              }`}
            />
            {errors.description && <p className="text-red-500 text-sm">{errors.description}</p>}
            <p className="text-gray-400 text-sm">{description.length}/500 characters</p>
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
                onBlur={(e) => handleBlur("price", e.target.value)}
                placeholder="0.00"
                className={`bg-gray-900 border-gray-700 text-white pl-7 ${
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
              className={`w-full bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 ${
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
              className={`w-full bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 ${
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
          <div className="flex items-center gap-3 p-4 bg-gray-900 rounded-lg">
            <input
              type="checkbox"
              id="isActive"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="w-4 h-4 accent-purple-600"
            />
            <div>
              <Label htmlFor="isActive" className="text-gray-200 cursor-pointer">
                Make listing visible
              </Label>
              <p className="text-gray-400 text-sm">
                {isActive
                  ? "Your listing will be visible to other users immediately"
                  : "Your listing will be hidden from other users"}
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4 pt-4">
            <Button
              type="submit"
              disabled={createMutation.isPending}
              className="bg-purple-600 hover:bg-purple-700"
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
          </div>
        </form>
      </div>
    </div>
  );
}
