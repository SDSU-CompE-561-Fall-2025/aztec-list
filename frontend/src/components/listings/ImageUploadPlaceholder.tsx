/**
 * TODO: Replace this component with actual image upload functionality
 *
 * Placeholder component for image upload feature.
 * When implementing image upload, replace this entire component
 * with proper file upload, preview, and management functionality.
 */

import { ImageIcon } from "lucide-react";

interface ImageUploadPlaceholderProps {
  className?: string;
}

export function ImageUploadPlaceholder({ className = "" }: ImageUploadPlaceholderProps) {
  return (
    <div
      className={`flex aspect-square flex-col items-center justify-center rounded-md bg-gray-800 p-8 text-center ${className}`}
      data-image-upload-placeholder="true"
    >
      <ImageIcon className="mb-3 h-12 w-12 text-gray-600" />
      <p className="text-sm text-gray-400">Image upload coming soon</p>
    </div>
  );
}
