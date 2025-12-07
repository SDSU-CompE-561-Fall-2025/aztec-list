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
      className={`aspect-square bg-gray-800 rounded-md flex flex-col items-center justify-center text-center p-8 ${className}`}
      data-image-upload-placeholder="true"
    >
      <ImageIcon className="h-12 w-12 text-gray-600 mb-3" />
      <p className="text-gray-400 text-sm">Image upload coming soon</p>
    </div>
  );
}
