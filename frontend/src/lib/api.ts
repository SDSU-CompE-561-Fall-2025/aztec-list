import { listingsParams } from "@/types/listing/listingParams";
import { ListingSearchResponse } from "@/types/listing/listing";

export const getListings = async (
  params: listingsParams = {}
): Promise<ListingSearchResponse> => {
  const {
    q,
    category,
    minPrice,
    maxPrice,
    condition,
    sellerId,
    limit,
    offset,
    sort,
  } = params;

  const url = new URL("http://127.0.0.1:8000/api/v1/listings");

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
  if (!res.ok) throw new Error("Failed to fetch listings");

  return res.json();
};
