'use client';

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Input } from "../ui/input";

export function Search() {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const { replace } = useRouter();

  function handleSearch(item: string) {
    const params = new URLSearchParams();
    item ? params.set('q', item) : params.delete('q', item);
    replace(`${pathname}?${params.toString()}`);
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