'use client';

import { useRouter, useSearchParams } from "next/navigation";
import { Input } from "../ui/input";
import { LISTINGS_BASE_URL, DEFAULT_SORT } from "@/lib/constants";

export function Search() {
  const searchParams = useSearchParams();
  const { replace } = useRouter();

  function handleSearch(item: string) {
    if (item) {
      replace(`${LISTINGS_BASE_URL}?q=${encodeURIComponent(item)}&sort=${DEFAULT_SORT}`);
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
      />
    </form>
  );
}