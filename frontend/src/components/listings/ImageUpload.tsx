/**
 * ImageUpload component for listing images.
 *
 * Handles file selection, upload, preview, and management of listing images.
 * Supports multiple files, thumbnail designation, and deletion.
 */

"use client";

import { useState, useEffect, useRef } from "react";
import { Trash2, Star, Loader2, Upload, Undo2 } from "lucide-react";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { getAuthToken } from "@/lib/auth";
import type { ImagePublic } from "@/types/listing/listing";
import { API_BASE_URL, STATIC_BASE_URL } from "@/lib/constants";

interface ImageUploadProps {
  listingId: string;
  existingImages?: ImagePublic[];
  onImagesChange?: (images: ImagePublic[]) => void;
  onPendingDeletions?: (imageIds: string[]) => void;
  onNewUploads?: (imageIds: string[]) => void;
  clearPendingDeletions?: boolean;
  clearNewUploads?: boolean;
  className?: string;
}

// Client-side validation constants
const ALLOWED_MIME_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"];
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

interface UploadingFile {
  id: string;
  name: string;
  progress: number;
}

/**
 * Validates a file before upload
 */
function validateFile(file: File): { valid: boolean; error?: string } {
  // Check file type
  if (!ALLOWED_MIME_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: `Invalid file type: ${file.type}. Allowed types: JPEG, PNG, WebP, GIF`,
    };
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    return {
      valid: false,
      error: `File too large: ${sizeMB}MB. Maximum size: 5MB`,
    };
  }

  return { valid: true };
}

export function ImageUpload({
  listingId,
  existingImages = [],
  onImagesChange,
  onPendingDeletions,
  onNewUploads,
  clearPendingDeletions = false,
  clearNewUploads = false,
  className = "",
}: ImageUploadProps) {
  const [images, setImages] = useState<ImagePublic[]>(() => existingImages);
  const [uploadingFiles, setUploadingFiles] = useState<Map<string, UploadingFile>>(new Map());
  const [pendingDeletions, setPendingDeletions] = useState<Set<string>>(new Set());
  const [newUploads, setNewUploads] = useState<Set<string>>(new Set());
  const [uploadedThisSession, setUploadedThisSession] = useState<Set<string>>(new Set());
  const isInitializedRef = useRef(false);

  useEffect(() => {
    if (!isInitializedRef.current) {
      isInitializedRef.current = true;
      return;
    }

    const existingIds = existingImages
      .map((img) => img.id)
      .sort()
      .join(",");
    const currentIds = images
      .map((img) => img.id)
      .sort()
      .join(",");

    if (existingIds !== currentIds) {
      setImages(existingImages);
      setNewUploads(new Set());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [existingImages]);

  useEffect(() => {
    onPendingDeletions?.(Array.from(pendingDeletions));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingDeletions]);

  useEffect(() => {
    onNewUploads?.(Array.from(newUploads));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [newUploads]);

  useEffect(() => {
    if (clearPendingDeletions && pendingDeletions.size > 0) {
      setPendingDeletions(new Set());
    }
  }, [clearPendingDeletions, pendingDeletions.size]);

  useEffect(() => {
    if (clearNewUploads && newUploads.size > 0) {
      setNewUploads(new Set());
      setUploadedThisSession(new Set());
    }
  }, [clearNewUploads, newUploads.size]);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const maxImages = 10;
    const remainingSlots = maxImages - images.length;

    if (files.length > remainingSlots) {
      toast.error(`Maximum ${maxImages} images allowed. You can upload ${remainingSlots} more.`);
      return;
    }

    const validFiles: File[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const validation = validateFile(file);

      if (!validation.valid) {
        toast.error(`${file.name}: ${validation.error}`);
        continue;
      }

      validFiles.push(file);
    }

    if (validFiles.length === 0) {
      event.target.value = "";
      return;
    }

    for (let i = 0; i < validFiles.length; i++) {
      const file = validFiles[i];
      const fileId = `${file.name}-${Date.now()}-${i}`;

      setUploadingFiles((prev) => {
        const next = new Map(prev);
        next.set(fileId, { id: fileId, name: file.name, progress: 0 });
        return next;
      });

      try {
        await uploadWithProgress(file, fileId);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Upload failed";
        toast.error(`${file.name}: ${errorMessage}`);
      } finally {
        setUploadingFiles((prev) => {
          const next = new Map(prev);
          next.delete(fileId);
          return next;
        });
      }
    }

    event.target.value = "";
  };

  const uploadWithProgress = async (file: File, fileId: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      formData.append("file", file);

      const token = getAuthToken();
      if (!token) {
        reject(new Error("Not authenticated. Please sign in."));
        return;
      }

      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          const progress = Math.round((e.loaded / e.total) * 100);
          setUploadingFiles((prev) => {
            const next = new Map(prev);
            const current = next.get(fileId);
            if (current) {
              next.set(fileId, { ...current, progress });
            }
            return next;
          });
        }
      });

      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const newImage = JSON.parse(xhr.responseText) as ImagePublic;
            const updatedImages = [...images, newImage];
            setImages(updatedImages);
            onImagesChange?.(updatedImages);

            // uploadedThisSession: permanent record, needed to restore "new" status on undo
            setUploadedThisSession((prev) => {
              const next = new Set(prev);
              next.add(newImage.id);
              return next;
            });

            // newUploads: display state for visual styling
            setNewUploads((prev) => {
              const next = new Set(prev);
              next.add(newImage.id);
              return next;
            });

            toast.success("Image uploaded successfully");
            resolve();
          } catch {
            reject(new Error("Failed to parse response"));
          }
        } else if (xhr.status === 401) {
          reject(new Error("Session expired. Please sign in again."));
        } else if (xhr.status === 404) {
          reject(new Error("Upload endpoint not found. Please check if the listing exists."));
        } else {
          try {
            const errorData = JSON.parse(xhr.responseText);
            reject(new Error(errorData.detail || `Upload failed with status ${xhr.status}`));
          } catch {
            reject(new Error(`Upload failed with status ${xhr.status}`));
          }
        }
      });

      xhr.addEventListener("error", () => {
        reject(new Error("Network error during upload"));
      });

      xhr.addEventListener("abort", () => {
        reject(new Error("Upload cancelled"));
      });

      const uploadUrl = `${API_BASE_URL}/listings/${listingId}/images/upload`;
      xhr.open("POST", uploadUrl);
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      xhr.send(formData);
    });
  };

  const handleMarkForDeletion = (imageId: string) => {
    setPendingDeletions((prev) => {
      const next = new Set(prev);
      next.add(imageId);
      return next;
    });

    setNewUploads((prev) => {
      const next = new Set(prev);
      next.delete(imageId);
      return next;
    });
  };

  const handleUnmarkForDeletion = (imageId: string) => {
    setPendingDeletions((prev) => {
      const next = new Set(prev);
      next.delete(imageId);
      return next;
    });

    if (uploadedThisSession.has(imageId)) {
      setNewUploads((prev) => {
        const next = new Set(prev);
        next.add(imageId);
        return next;
      });
    }
  };

  const isUploading = uploadingFiles.size > 0;
  const hasImages = images.length > 0;
  const activeImagesCount = images.length - pendingDeletions.size;

  return (
    <div className={className}>
      <Label className="text-gray-200 mb-2 block">
        Images {hasImages && `(${activeImagesCount}/10)`}
        {newUploads.size > 0 && (
          <span className="text-green-400 ml-2 text-sm font-bold">
            ✨ {newUploads.size} new {newUploads.size === 1 ? "upload" : "uploads"} (unsaved)
          </span>
        )}
        {pendingDeletions.size > 0 && (
          <span className="text-red-400 ml-2 text-sm font-bold">
            ⚠️ {pendingDeletions.size} pending deletion
          </span>
        )}
      </Label>

      {/* Image Grid */}
      {hasImages && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          {images.map((image) => {
            const isMarkedForDeletion = pendingDeletions.has(image.id);
            const isNewUpload = newUploads.has(image.id);
            return (
              <div key={image.id} className="relative group aspect-square">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={`${STATIC_BASE_URL}${image.url}`}
                  alt={image.alt_text || "Listing image"}
                  className={`w-full h-full object-cover rounded-md border ${
                    isMarkedForDeletion
                      ? "border-red-500 opacity-40 grayscale"
                      : isNewUpload
                        ? "border-green-500 opacity-70"
                        : "border-gray-700"
                  }`}
                  loading="lazy"
                />
                {isMarkedForDeletion && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-md">
                    <div className="text-center">
                      <Trash2 className="w-8 h-8 text-red-500 mx-auto mb-2" />
                      <p className="text-white text-sm font-medium">Marked for deletion</p>
                    </div>
                  </div>
                )}
                {isNewUpload && !isMarkedForDeletion && (
                  <div className="absolute top-2 left-2 bg-green-600 text-white px-2 py-1 rounded text-xs flex items-center gap-1">
                    <span className="font-bold">NEW</span>
                  </div>
                )}
                {image.is_thumbnail && !isMarkedForDeletion && !isNewUpload && (
                  <div className="absolute top-2 left-2 bg-purple-600 text-white px-2 py-1 rounded text-xs flex items-center gap-1">
                    <Star className="w-3 h-3 fill-current" />
                    Thumbnail
                  </div>
                )}
                {isMarkedForDeletion ? (
                  <button
                    type="button"
                    onClick={() => handleUnmarkForDeletion(image.id)}
                    className="absolute top-2 right-2 bg-green-600 hover:bg-green-700 text-white p-1.5 rounded-md transition-opacity"
                    aria-label="Undo deletion"
                    title="Undo deletion"
                  >
                    <Undo2 className="w-4 h-4" />
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => handleMarkForDeletion(image.id)}
                    className="absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white p-1.5 rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
                    aria-label="Mark for deletion"
                    title="Mark for deletion"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Uploading Files Progress */}
      {uploadingFiles.size > 0 && (
        <div className="space-y-2 mb-4">
          {Array.from(uploadingFiles.values()).map((file) => (
            <div key={file.id} className="bg-gray-800 rounded-md p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-300 truncate flex-1 mr-2">{file.name}</span>
                <span className="text-xs text-gray-500">{file.progress}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-1.5">
                <div
                  className="bg-purple-600 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${file.progress}%` }}
                />
              </div>
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
              bg-gray-800 rounded-md flex flex-col items-center justify-center
              text-center p-6 cursor-pointer border-2 border-dashed border-gray-700
              hover:border-purple-500 hover:bg-gray-750 transition-colors
              ${isUploading ? "opacity-50 cursor-not-allowed" : ""}
            `}
          >
            {isUploading ? (
              <>
                <Loader2 className="h-8 w-8 text-purple-500 mb-2 animate-spin" />
                <p className="text-gray-400 text-sm">Uploading...</p>
              </>
            ) : (
              <>
                <Upload className="h-8 w-8 text-gray-600 mb-2" />
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
