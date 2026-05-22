"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useState, useEffect } from "react";
import { CATEGORIES, Category } from "@/types/listing/filters/category";
import { CONDITIONS, Condition } from "@/types/listing/filters/condition";
import { SORT_OPTIONS, Sort } from "@/types/listing/filters/sort";
import { formatCategoryLabel, formatConditionLabel, formatSortLabel } from "@/lib/utils";
import { LISTINGS_BASE_URL, DEFAULT_SORT } from "@/lib/constants";
import { Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";

const PRICE_ERROR_MESSAGE = "Min price must be less than max price";

export function SearchFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Local state for price inputs
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [priceError, setPriceError] = useState(false);

  // Get current values from URL
  const urlCategoryParam = searchParams.get("category");
  const urlCategory =
    urlCategoryParam && CATEGORIES.includes(urlCategoryParam as Category) ? urlCategoryParam : "";

  const urlSortParam = searchParams.get("sort");
  const urlSort =
    urlSortParam && SORT_OPTIONS.includes(urlSortParam as Sort) ? urlSortParam : DEFAULT_SORT;

  // Local state for pending category and sort changes (before "Apply Filters" is clicked)
  const [selectedCategory, setSelectedCategory] = useState<string>(() => urlCategory);
  const [selectedSort, setSelectedSort] = useState<string>(() => urlSort);

  // Derive condition from URL - this is the source of truth
  const urlConditionParam = searchParams.get("condition");
  const urlCondition =
    urlConditionParam && CONDITIONS.includes(urlConditionParam as Condition)
      ? (urlConditionParam as Condition)
      : null;

  // Local state for pending condition changes (before "Apply Filters" is clicked)
  // Initialize from URL, but allow temporary changes before applying
  const [selectedConditions, setSelectedConditions] = useState<Condition[]>(() =>
    urlCondition ? [urlCondition] : [],
  );

  // Sync local state with URL changes (e.g., browser back/forward, or after applying filters)
  useEffect(() => {
    setSelectedConditions(urlCondition ? [urlCondition] : []);
  }, [urlCondition]);

  useEffect(() => {
    setSelectedCategory(urlCategory);
  }, [urlCategory]);

  useEffect(() => {
    setSelectedSort(urlSort);
  }, [urlSort]);

  const updateURL = (updates: Record<string, string | undefined>) => {
    const params = new URLSearchParams(searchParams.toString());

    Object.entries(updates).forEach(([key, value]) => {
      if (value && value !== "") {
        params.set(key, value);
      } else {
        params.delete(key);
      }
    });

    router.replace(`${pathname}?${params.toString()}`);
  };

  const validatePriceRange = (min?: number, max?: number): boolean => {
    if ((min !== undefined && isNaN(min)) || (max !== undefined && isNaN(max))) {
      return false;
    }
    if (min !== undefined && max !== undefined && min > max) {
      return false;
    }
    return true;
  };

  const handleCategoryChange = (value: string) => {
    setSelectedCategory(value);
  };

  const handleSortChange = (value: string) => {
    setSelectedSort(value);
  };

  const handleApplyFilters = () => {
    const min = minPrice ? parseInt(minPrice, 10) : undefined;
    const max = maxPrice ? parseInt(maxPrice, 10) : undefined;

    if (!validatePriceRange(min, max)) {
      setPriceError(true);
      return;
    }

    setPriceError(false);

    const conditionValue = selectedConditions.length > 0 ? selectedConditions[0] : undefined;

    updateURL({
      minPrice: min?.toString(),
      maxPrice: max?.toString(),
      condition: conditionValue,
      category: selectedCategory || undefined,
      sort: selectedSort,
      offset: undefined, // Reset to first page when filters change
    });
  };

  const handleClearFilters = () => {
    setMinPrice("");
    setMaxPrice("");
    setSelectedConditions([]);
    setSelectedCategory("");
    setSelectedSort(DEFAULT_SORT);
    setPriceError(false);
    router.replace(`${LISTINGS_BASE_URL}?sort=${DEFAULT_SORT}`);
  };

  const handleConditionToggle = (condition: Condition) => {
    setSelectedConditions((prev) => {
      if (prev.includes(condition)) {
        return prev.filter((c) => c !== condition);
      } else {
        return [condition]; // Only allow one selection
      }
    });
  };

  const handlePriceChange = (value: string, setter: (val: string) => void) => {
    if (value === "" || parseInt(value, 10) >= 0) {
      setter(value);
    }
  };

  const handlePriceKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "-" || e.key === "e" || e.key === "E") {
      e.preventDefault();
    }
  };

  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

  const filtersContent = (
    <div className="space-y-6">
      {/* Category Section */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-foreground">Category</h3>
        <select
          value={selectedCategory}
          onChange={(e) => handleCategoryChange(e.target.value)}
          className="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 dark:bg-input/30"
        >
          <option value="">All Categories</option>
          {CATEGORIES.map((cat) => (
            <option key={cat} value={cat}>
              {formatCategoryLabel(cat)}
            </option>
          ))}
        </select>
      </div>

      {/* Price Range Section */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-foreground">Price Range</h3>
        <div className="space-y-2">
          <input
            type="number"
            min="0"
            placeholder="Min"
            value={minPrice}
            onChange={(e) => handlePriceChange(e.target.value, setMinPrice)}
            onKeyDown={handlePriceKeyDown}
            className={`h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 dark:bg-input/30 ${
              priceError ? "border-red-500 ring-destructive/20" : ""
            }`}
          />
          <input
            type="number"
            min="0"
            placeholder="Max"
            value={maxPrice}
            onChange={(e) => handlePriceChange(e.target.value, setMaxPrice)}
            onKeyDown={handlePriceKeyDown}
            className={`h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 dark:bg-input/30 ${
              priceError ? "border-red-500 ring-destructive/20" : ""
            }`}
          />
          {priceError && <p className="text-xs text-red-500">{PRICE_ERROR_MESSAGE}</p>}
        </div>
      </div>

      {/* Condition Section */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-foreground">Condition</h3>
        <div className="space-y-2">
          {CONDITIONS.map((condition) => (
            <label
              key={condition}
              className="flex cursor-pointer items-center gap-2 text-sm text-foreground"
            >
              <input
                type="checkbox"
                checked={selectedConditions.includes(condition)}
                onChange={() => handleConditionToggle(condition)}
                className="rounded border bg-background text-purple-500 focus:ring-2 focus:ring-purple-500"
              />
              {formatConditionLabel(condition)}
            </label>
          ))}
        </div>
      </div>

      {/* Sort By Section */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-foreground">Sort By</h3>
        <select
          value={selectedSort}
          onChange={(e) => handleSortChange(e.target.value)}
          className="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 dark:bg-input/30"
        >
          {SORT_OPTIONS.map((sort) => (
            <option key={sort} value={sort}>
              {formatSortLabel(sort)}
            </option>
          ))}
        </select>
      </div>

      {/* Apply Filters Button */}
      <button
        onClick={handleApplyFilters}
        className="w-full rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-700"
      >
        Apply Filters
      </button>

      {/* Clear Filters Button */}
      <button
        onClick={handleClearFilters}
        className="w-full rounded-md bg-muted px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted/80"
      >
        Clear Filters
      </button>
    </div>
  );

  return (
    <>
      {/* Mobile Filter Button */}
      <div className="mb-4 lg:hidden">
        <Sheet open={mobileFiltersOpen} onOpenChange={setMobileFiltersOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" className="w-full">
              <Filter className="mr-2 h-4 w-4" />
              Filters
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-80">
            <SheetHeader>
              <SheetTitle>Filters</SheetTitle>
            </SheetHeader>
            <div className="mt-6">{filtersContent}</div>
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop Sidebar */}
      <aside className="hidden w-80 rounded-lg border bg-card p-6 lg:block">{filtersContent}</aside>
    </>
  );
}
