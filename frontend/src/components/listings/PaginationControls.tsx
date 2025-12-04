"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { DEFAULT_LIMIT } from "@/lib/constants";

interface PaginationControlsProps {
  count: number;
}

export function PaginationControls({ count }: PaginationControlsProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const offset = parseInt(searchParams.get("offset") || "0");
  const totalPages = Math.ceil(count / DEFAULT_LIMIT);
  const currentPage = Math.floor(offset / DEFAULT_LIMIT) + 1;

  const handlePageChange = (newPage: number) => {
    const newOffset = (newPage - 1) * DEFAULT_LIMIT;
    const params = new URLSearchParams(searchParams.toString());
    
    if (newOffset > 0) {
      params.set("offset", newOffset.toString());
    } else {
      params.delete("offset");
    }

    router.replace(`${pathname}?${params.toString()}`);
  };

  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className="flex items-center justify-center gap-4 py-8">
      <button
        onClick={() => handlePageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-4 py-2 bg-gray-800 text-gray-100 rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700 transition-colors"
      >
        Previous
      </button>
      
      <span className="text-sm text-gray-300">
        Page {currentPage} of {totalPages}
      </span>
      
      <button
        onClick={() => handlePageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-4 py-2 bg-gray-800 text-gray-100 rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700 transition-colors"
      >
        Next
      </button>
    </div>
  );
}
