import { ListingsParams } from "@/types/listing/listingParams";
import { ListingSearchResponse } from "@/types/listing/listing";
import { API_BASE_URL } from "@/lib/constants";

export const getListings = async (params: ListingsParams = {}): Promise<ListingSearchResponse> => {
  const { q, category, minPrice, maxPrice, condition, sellerId, limit, offset, sort } = params;

  const url = new URL(`${API_BASE_URL}/listings`);

  // Match FastAPI parameter names 1:1
  if (q) url.searchParams.set("search_text", q);
  if (category) url.searchParams.set("category", category);
  if (minPrice !== undefined) url.searchParams.set("min_price", String(minPrice));
  if (maxPrice !== undefined) url.searchParams.set("max_price", String(maxPrice));
  if (condition) url.searchParams.set("condition", condition);
  if (sellerId) url.searchParams.set("seller_id", sellerId);
  if (limit !== undefined) url.searchParams.set("limit", String(limit));
  if (offset !== undefined) url.searchParams.set("offset", String(offset));
  if (sort) url.searchParams.set("sort", sort);

  const res = await fetch(url.toString());
  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`Failed to fetch listings: ${res.status} ${errorText}`);
  }

  const data = await res.json();

  // Validate response structure
  if (!data || typeof data !== "object" || !Array.isArray(data.items)) {
    throw new Error("Invalid response format from API");
  }

  return data as ListingSearchResponse;
};
