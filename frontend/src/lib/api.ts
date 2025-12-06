import { ListingsParams } from "@/types/listing/listingParams";
import { UserListingsParams } from "@/types/listing/userListingsParams";
import { ListingSearchResponse, ListingPublic } from "@/types/listing/listing";
import { API_BASE_URL } from "@/lib/constants";
import { getAuthToken } from "@/lib/auth";

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

export const getUserListings = async (
  userId: string,
  params: UserListingsParams = {}
): Promise<ListingSearchResponse> => {
  // Use the existing getListings function with sellerId filter
  // Note: sellerId is the same as userId (user owns their listings)
  return getListings({
    sellerId: userId,
    limit: params.limit,
    offset: params.offset,
    sort: params.sort,
    // Note: include_inactive is not supported by the main listings endpoint
    // Backend filters by is_active=true by default
  });
};

export const getOwnListings = async (
  userId: string,
  params: UserListingsParams = {}
): Promise<ListingSearchResponse> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const { limit, offset, sort, include_inactive } = params;
  const url = new URL(`${API_BASE_URL}/users/${userId}/listings`);

  if (limit !== undefined) url.searchParams.set("limit", String(limit));
  if (offset !== undefined) url.searchParams.set("offset", String(offset));
  if (sort) url.searchParams.set("sort", sort);
  if (include_inactive !== undefined)
    url.searchParams.set("include_inactive", String(include_inactive));

  const res = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`Failed to fetch own listings: ${res.status} ${errorText}`);
  }

  const data = await res.json();

  // Validate response structure
  if (!data || typeof data !== "object" || !Array.isArray(data.items)) {
    throw new Error("Invalid response format from API");
  }

  return data as ListingSearchResponse;
};

export const updateListing = async (
  listingId: string,
  data: Partial<{
    title: string;
    description: string;
    price: number;
    category: string;
    condition: string;
    is_active: boolean;
  }>
): Promise<void> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const url = new URL(`${API_BASE_URL}/listings/${listingId}`);

  const res = await fetch(url.toString(), {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`Failed to update listing: ${res.status} ${errorText}`);
  }
};

export const deleteListing = async (listingId: string): Promise<void> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const url = new URL(`${API_BASE_URL}/listings/${listingId}`);

  const res = await fetch(url.toString(), {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`Failed to delete listing: ${res.status} ${errorText}`);
  }
};

export const toggleListingActive = async (listingId: string, isActive: boolean): Promise<void> => {
  return updateListing(listingId, { is_active: isActive });
};

export const getListing = async (listingId: string): Promise<ListingPublic> => {
  const url = new URL(`${API_BASE_URL}/listings/${listingId}`);

  const res = await fetch(url.toString());
  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`Failed to fetch listing: ${res.status} ${errorText}`);
  }

  const data = await res.json();

  // Validate response structure
  if (!data || typeof data !== "object") {
    throw new Error("Invalid response format from API");
  }

  return data as ListingPublic;
};

export const createListing = async (data: {
  title: string;
  description: string;
  price: number;
  category: string;
  condition: string;
  is_active?: boolean;
}): Promise<ListingPublic> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const res = await fetch(`${API_BASE_URL}/listings`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`Failed to create listing: ${res.status} ${errorText}`);
  }

  const responseData = await res.json();

  // Validate response structure
  if (!responseData || typeof responseData !== "object") {
    throw new Error("Invalid response format from API");
  }

  return responseData as ListingPublic;
};
