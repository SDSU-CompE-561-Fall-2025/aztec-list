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

  const offsetParam = searchParams.get("offset");
  const parsedOffset = offsetParam ? parseInt(offsetParam, 10) : 0;
  const offset = isNaN(parsedOffset) || parsedOffset < 0 ? 0 : parsedOffset;

  const totalPages = Math.max(1, Math.ceil(count / DEFAULT_LIMIT));
  const currentPage = Math.min(Math.max(1, Math.floor(offset / DEFAULT_LIMIT) + 1), totalPages);

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
        className="px-4 py-2 bg-muted text-foreground rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-muted/80 transition-colors"
      >
        Previous
      </button>

      <span className="text-sm text-muted-foreground">
        Page {currentPage} of {totalPages}
      </span>

      <button
        onClick={() => handlePageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-4 py-2 bg-muted text-foreground rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-muted/80 transition-colors"
      >
        Next
      </button>
    </div>
  );
}
