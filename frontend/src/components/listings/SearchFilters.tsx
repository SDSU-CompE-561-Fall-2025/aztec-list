"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useState, useEffect } from "react";
import { Category } from "@/types/listing/filters/category";
import { Condition } from "@/types/listing/filters/condition";
import { Sort } from "@/types/listing/filters/sort";
import { formatCategoryLabel, formatConditionLabel, formatSortLabel } from "@/lib/utils";
import { LISTINGS_BASE_URL, DEFAULT_SORT } from "@/lib/constants";

const categories: Category[] = [
  "electronics",
  "textbooks",
  "furniture",
  "dorm",
  "appliances",
  "clothing",
  "shoes",
  "accessories",
  "bikes",
  "sports_equipment",
  "tools",
  "office_supplies",
  "music",
  "musical_instruments",
  "video_games",
  "collectibles",
  "art",
  "baby_kids",
  "pet_supplies",
  "tickets",
  "services",
  "other",
];

const conditions: Condition[] = ["new", "like_new", "good", "fair", "poor"];

const sortOptions: Sort[] = ["recent", "price_asc", "price_desc"];

export function SearchFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Local state for price inputs
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [priceError, setPriceError] = useState(false);

  // Local state for condition checkboxes
  const [selectedConditions, setSelectedConditions] = useState<Condition[]>([]);

  // Initialize condition state from URL
  useEffect(() => {
    const conditionParam = searchParams.get("condition");
    if (conditionParam) {
      setSelectedConditions([conditionParam as Condition]);
    } else {
      setSelectedConditions([]);
    }
  }, [searchParams]);

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

  const handleCategoryChange = (value: string) => {
    updateURL({ category: value || undefined });
  };

  const handleSortChange = (value: string) => {
    updateURL({ sort: value });
  };

  const handleApplyFilters = () => {
    // Validate price range
    const min = minPrice ? parseInt(minPrice) : undefined;
    const max = maxPrice ? parseInt(maxPrice) : undefined;

    if (min !== undefined && max !== undefined && min > max) {
      setPriceError(true);
      return;
    }

    setPriceError(false);

    // Build condition param (only single value for now)
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
    setSelectedConditions(prev => {
      if (prev.includes(condition)) {
        return prev.filter(c => c !== condition);
      } else {
        return [condition]; // Only allow one selection
      }
    });
  };

  const currentCategory = searchParams.get("category") || "";
  const currentSort = searchParams.get("sort") || DEFAULT_SORT;

  return (
    <aside className="w-80 bg-gray-900 p-6 rounded-lg space-y-6">
      {/* Category Section */}
      <div>
        <h3 className="text-sm font-semibold text-gray-100 mb-3">Category</h3>
        <select
          value={currentCategory}
          onChange={(e) => handleCategoryChange(e.target.value)}
          className="w-full bg-gray-800 text-gray-100 border border-gray-700 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option value="">All Categories</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {formatCategoryLabel(cat)}
            </option>
          ))}
        </select>
      </div>

      {/* Price Range Section */}
      <div>
        <h3 className="text-sm font-semibold text-gray-100 mb-3">Price Range</h3>
        <div className="space-y-2">
          <input
            type="number"
            min="0"
            placeholder="Min"
            value={minPrice}
            onChange={(e) => {
              const value = e.target.value;
              if (value === "" || parseInt(value) >= 0) {
                setMinPrice(value);
              }
            }}
            onKeyDown={(e) => {
              if (e.key === "-" || e.key === "e" || e.key === "E") {
                e.preventDefault();
              }
            }}
            className={`w-full bg-gray-800 text-gray-100 border ${
              priceError ? "border-red-500" : "border-gray-700"
            } rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500`}
          />
          <input
            type="number"
            min="0"
            placeholder="Max"
            value={maxPrice}
            onChange={(e) => {
              const value = e.target.value;
              if (value === "" || parseInt(value) >= 0) {
                setMaxPrice(value);
              }
            }}
            onKeyDown={(e) => {
              if (e.key === "-" || e.key === "e" || e.key === "E") {
                e.preventDefault();
              }
            }}
            className={`w-full bg-gray-800 text-gray-100 border ${
              priceError ? "border-red-500" : "border-gray-700"
            } rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500`}
          />
          {priceError && (
            <p className="text-xs text-red-500">Min price must be less than max price</p>
          )}
        </div>
      </div>

      {/* Condition Section */}
      <div>
        <h3 className="text-sm font-semibold text-gray-100 mb-3">Condition</h3>
        <div className="space-y-2">
          {conditions.map((condition) => (
            <label key={condition} className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedConditions.includes(condition)}
                onChange={() => handleConditionToggle(condition)}
                className="rounded border-gray-700 bg-gray-800 text-purple-500 focus:ring-2 focus:ring-purple-500"
              />
              {formatConditionLabel(condition)}
            </label>
          ))}
        </div>
      </div>

      {/* Sort By Section */}
      <div>
        <h3 className="text-sm font-semibold text-gray-100 mb-3">Sort By</h3>
        <select
          value={currentSort}
          onChange={(e) => handleSortChange(e.target.value)}
          className="w-full bg-gray-800 text-gray-100 border border-gray-700 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          {sortOptions.map((sort) => (
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
        className="w-full bg-gray-800 hover:bg-gray-700 text-gray-300 font-medium py-2 px-4 rounded-md text-sm transition-colors"
      >
        Clear Filters
      </button>
    </aside>
  );
}
