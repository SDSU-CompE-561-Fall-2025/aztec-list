/**
 * ImageUpload component for listing images.
 *
 * Handles file selection, upload, preview, and management of listing images.
 * Supports multiple files, thumbnail designation, and deletion.
 */

"use client";

import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ImageIcon, X, Star, Loader2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { uploadListingImage, deleteListingImage } from "@/lib/api";
import type { ImagePublic } from "@/types/listing/listing";
import { API_BASE_URL } from "@/lib/constants";

interface ImageUploadProps {
  listingId: string;
  existingImages?: ImagePublic[];
  onImagesChange?: (images: ImagePublic[]) => void;
  className?: string;
}

export function ImageUpload({
  listingId,
  existingImages = [],
  onImagesChange,
  className = "",
}: ImageUploadProps) {
  const [images, setImages] = useState<ImagePublic[]>(existingImages);
  const [uploadingFiles, setUploadingFiles] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();

  // Sync images state when existingImages prop changes
  useEffect(() => {
    setImages(existingImages);
  }, [existingImages]);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadListingImage(listingId, file),
    onSuccess: (newImage) => {
      const updatedImages = [...images, newImage];
      setImages(updatedImages);
      onImagesChange?.(updatedImages);
      toast.success("Image uploaded successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to upload image");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (imageId: string) => deleteListingImage(listingId, imageId),
    onSuccess: (_, imageId) => {
      const updatedImages = images.filter((img) => img.id !== imageId);
      setImages(updatedImages);
      onImagesChange?.(updatedImages);
      toast.success("Image deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["listing", listingId] });
    },
    onError: () => {
      toast.error("Failed to delete image");
    },
  });

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const maxImages = 10;
    const remainingSlots = maxImages - images.length;

    if (files.length > remainingSlots) {
      toast.error(`Maximum ${maxImages} images allowed. You can upload ${remainingSlots} more.`);
      return;
    }

    // Upload files sequentially
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const fileId = `${file.name}-${Date.now()}-${i}`;

      setUploadingFiles((prev) => new Set(prev).add(fileId));

      try {
        await uploadMutation.mutateAsync(file);
      } finally {
        setUploadingFiles((prev) => {
          const next = new Set(prev);
          next.delete(fileId);
          return next;
        });
      }
    }

    // Reset file input
    event.target.value = "";
  };

  const handleDelete = (imageId: string) => {
    deleteMutation.mutate(imageId);
  };

  const isUploading = uploadingFiles.size > 0 || uploadMutation.isPending;
  const hasImages = images.length > 0;

  return (
    <div className={className}>
      <Label className="text-gray-200 mb-2 block">
        Images {hasImages && `(${images.length}/10)`}
      </Label>

      {/* Image Grid */}
      {hasImages && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          {images.map((image) => (
            <div key={image.id} className="relative group aspect-square">
              <img
                src={`${API_BASE_URL.replace("/api/v1", "")}${image.url}`}
                alt={image.alt_text || "Listing image"}
                className="w-full h-full object-cover rounded-md border border-gray-700"
              />
              {image.is_thumbnail && (
                <div className="absolute top-2 left-2 bg-purple-600 text-white px-2 py-1 rounded text-xs flex items-center gap-1">
                  <Star className="w-3 h-3 fill-current" />
                  Thumbnail
                </div>
              )}
              <button
                onClick={() => handleDelete(image.id)}
                disabled={deleteMutation.isPending}
                className="absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white p-1.5 rounded-md opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-50"
                aria-label="Delete image"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Upload Area */}
      {images.length < 10 && (
        <div className="relative">
          <input
            type="file"
            id="image-upload"
            accept="image/jpeg,image/png,image/webp,image/gif"
            multiple
            onChange={handleFileSelect}
            disabled={isUploading}
            className="hidden"
          />
          <label
            htmlFor="image-upload"
            className={`
              aspect-square bg-gray-800 rounded-md flex flex-col items-center justify-center
              text-center p-8 cursor-pointer border-2 border-dashed border-gray-700
              hover:border-purple-500 hover:bg-gray-750 transition-colors
              ${isUploading ? "opacity-50 cursor-not-allowed" : ""}
            `}
          >
            {isUploading ? (
              <>
                <Loader2 className="h-12 w-12 text-purple-500 mb-3 animate-spin" />
                <p className="text-gray-400 text-sm">Uploading...</p>
              </>
            ) : (
              <>
                <Upload className="h-12 w-12 text-gray-600 mb-3" />
                <p className="text-gray-300 text-sm font-medium mb-1">Click to upload images</p>
                <p className="text-gray-500 text-xs">JPG, PNG, WebP, GIF (max 5MB each)</p>
                <p className="text-gray-500 text-xs mt-1">{10 - images.length} slots remaining</p>
              </>
            )}
          </label>
        </div>
      )}

      {!hasImages && !isUploading && (
        <p className="text-gray-500 text-sm mt-2">
          First image uploaded will be set as the thumbnail
        </p>
      )}
    </div>
  );
}
