import { listingsParams } from "@/types/listingParams";

export const getListings = async (
  params: listingsParams = {}
): Promise<any> => {
  const {
    q,
    minPrice,
    maxPrice,
    category,
    limit = 20,
    offset = 0,
    sort = "recent",
  } = params;

  const url = new URL("http://127.0.0.1:8000/api/v1/listings");

  // base params that are always sent
  url.searchParams.set("limit", String(limit));
  url.searchParams.set("offset", String(offset));
  url.searchParams.set("sort", sort);

  // optional filters
  if (q) {
    url.searchParams.set("search_text", q);      
  }
  if (minPrice != null) {
    url.searchParams.set("min_price", String(minPrice));
  }
  if (maxPrice != null) {
    url.searchParams.set("max_price", String(maxPrice));
  }
  if (category) {
    url.searchParams.set("category", category);
  }

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Failed to fetch listings");
  return res.json();
};
