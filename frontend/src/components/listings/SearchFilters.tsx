"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useState, useRef } from "react";
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

  // Derive condition from URL - this is the source of truth
  const urlConditionParam = searchParams.get("condition");
  const urlCondition =
    urlConditionParam && CONDITIONS.includes(urlConditionParam as Condition)
      ? (urlConditionParam as Condition)
      : null;

  // Local state for pending condition changes (before "Apply Filters" is clicked)
  // Initialize from URL, but allow temporary changes before applying
  const [selectedConditions, setSelectedConditions] = useState<Condition[]>(() =>
    urlCondition ? [urlCondition] : []
  );

  // Sync with URL when it changes (e.g., browser back/forward, or after applying filters)
  // Use a ref to track if we need to sync
  const prevUrlConditionRef = useRef(urlCondition);
  if (prevUrlConditionRef.current !== urlCondition) {
    prevUrlConditionRef.current = urlCondition;
    setSelectedConditions(urlCondition ? [urlCondition] : []);
  }

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
    updateURL({ category: value || undefined });
  };

  const handleSortChange = (value: string) => {
    updateURL({ sort: value });
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
      offset: undefined, // Reset to first page when filters change
    });
  };

  const handleClearFilters = () => {
    setMinPrice("");
    setMaxPrice("");
    setSelectedConditions([]);
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

  const currentCategoryParam = searchParams.get("category");
  const currentCategory =
    currentCategoryParam && CATEGORIES.includes(currentCategoryParam as Category)
      ? currentCategoryParam
      : "";

  const currentSortParam = searchParams.get("sort");
  const currentSort =
    currentSortParam && SORT_OPTIONS.includes(currentSortParam as Sort)
      ? currentSortParam
      : DEFAULT_SORT;

  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

  const filtersContent = (
    <div className="space-y-6">
      {/* Category Section */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-3">Category</h3>
        <select
          value={currentCategory}
          onChange={(e) => handleCategoryChange(e.target.value)}
          className="w-full bg-background text-foreground border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
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
        <h3 className="text-sm font-semibold text-foreground mb-3">Price Range</h3>
        <div className="space-y-2">
          <input
            type="number"
            min="0"
            placeholder="Min"
            value={minPrice}
            onChange={(e) => handlePriceChange(e.target.value, setMinPrice)}
            onKeyDown={handlePriceKeyDown}
            className={`w-full bg-background text-foreground border ${
              priceError ? "border-red-500" : "border"
            } rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500`}
          />
          <input
            type="number"
            min="0"
            placeholder="Max"
            value={maxPrice}
            onChange={(e) => handlePriceChange(e.target.value, setMaxPrice)}
            onKeyDown={handlePriceKeyDown}
            className={`w-full bg-background text-foreground border ${
              priceError ? "border-red-500" : "border"
            } rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500`}
          />
          {priceError && <p className="text-xs text-red-500">{PRICE_ERROR_MESSAGE}</p>}
        </div>
      </div>

      {/* Condition Section */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-3">Condition</h3>
        <div className="space-y-2">
          {CONDITIONS.map((condition) => (
            <label
              key={condition}
              className="flex items-center gap-2 text-sm text-foreground cursor-pointer"
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
        <h3 className="text-sm font-semibold text-foreground mb-3">Sort By</h3>
        <select
          value={currentSort}
          onChange={(e) => handleSortChange(e.target.value)}
          className="w-full bg-background text-foreground border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
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
        className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-md text-sm transition-colors"
      >
        Apply Filters
      </button>

      {/* Clear Filters Button */}
      <button
        onClick={handleClearFilters}
        className="w-full bg-muted hover:bg-muted/80 text-muted-foreground font-medium py-2 px-4 rounded-md text-sm transition-colors"
      >
        Clear Filters
      </button>
    </div>
  );

  return (
    <>
      {/* Mobile Filter Button */}
      <div className="lg:hidden mb-4">
        <Sheet open={mobileFiltersOpen} onOpenChange={setMobileFiltersOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" className="w-full">
              <Filter className="w-4 h-4 mr-2" />
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
      <aside className="hidden lg:block w-80 bg-card p-6 rounded-lg border">{filtersContent}</aside>
    </>
  );
}
