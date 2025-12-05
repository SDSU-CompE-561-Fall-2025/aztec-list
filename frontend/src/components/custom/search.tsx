"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Input } from "../ui/input";
import { LISTINGS_BASE_URL, DEFAULT_SORT, MAX_SEARCH_LENGTH } from "@/lib/constants";

export function Search() {
  const searchParams = useSearchParams();
  const { replace } = useRouter();

  function handleSearch(item: string) {
    // Sanitize and limit search input
    const sanitized = item.trim().slice(0, MAX_SEARCH_LENGTH);

    if (sanitized) {
      replace(`${LISTINGS_BASE_URL}?q=${encodeURIComponent(sanitized)}&sort=${DEFAULT_SORT}`);
    } else {
      replace(`${LISTINGS_BASE_URL}?sort=${DEFAULT_SORT}`);
    }
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        const item = String(formData.get("q") ?? "");
        handleSearch(item);
      }}
    >
      <Input
        name="q"
        defaultValue={searchParams.get("q") ?? ""}
        placeholder="Search..."
        maxLength={MAX_SEARCH_LENGTH}
      />
    </form>
  );
}
