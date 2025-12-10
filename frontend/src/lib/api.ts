import { ListingsParams } from "@/types/listing/listingParams";
import { UserListingsParams } from "@/types/listing/userListingsParams";
import { ListingSearchResponse, ListingPublic, ImagePublic } from "@/types/listing/listing";
import { UserPublic } from "@/types/user";
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
): Promise<ListingPublic> => {
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

  const responseData = await res.json();

  // Validate response structure
  if (!responseData || typeof responseData !== "object") {
    throw new Error("Invalid response format from API");
  }

  return responseData as ListingPublic;
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

export const toggleListingActive = async (
  listingId: string,
  isActive: boolean
): Promise<ListingPublic> => {
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
    let errorMessage = `Failed to create listing: ${res.status}`;
    try {
      const errorData = await res.json();
      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // If JSON parsing fails, use the status-based message
    }
    throw new Error(errorMessage);
  }

  const responseData = await res.json();

  // Validate response structure
  if (!responseData || typeof responseData !== "object") {
    throw new Error("Invalid response format from API");
  }

  return responseData as ListingPublic;
};

export const uploadListingImage = async (listingId: string, file: File): Promise<ImagePublic> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/listings/${listingId}/images/upload`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`Failed to upload image: ${res.status} ${errorText}`);
  }

  return res.json();
};

export const deleteListingImage = async (listingId: string, imageId: string): Promise<void> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const res = await fetch(`${API_BASE_URL}/listings/${listingId}/images/${imageId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`Failed to delete image: ${res.status} ${errorText}`);
  }
};

// User API functions

export const getUser = async (userId: string): Promise<UserPublic> => {
  const url = new URL(`${API_BASE_URL}/users/${userId}`);

  const res = await fetch(url.toString());
  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`Failed to fetch user: ${res.status} ${errorText}`);
  }

  const data = await res.json();

  if (!data || typeof data !== "object") {
    throw new Error("Invalid response format from API");
  }

  return data as UserPublic;
};

// Support Ticket API functions

export interface SupportTicket {
  id: string;
  user_id: string | null;
  email: string;
  subject: string;
  message: string;
  status: "open" | "in_progress" | "resolved" | "closed";
  created_at: string;
  updated_at: string;
}

export interface CreateSupportTicketData {
  email: string;
  subject: string;
  message: string;
}

export interface CreateSupportTicketResponse extends SupportTicket {
  email_sent: boolean;
}

export const createSupportTicket = async (
  data: CreateSupportTicketData
): Promise<CreateSupportTicketResponse> => {
  const token = getAuthToken();

  const res = await fetch(`${API_BASE_URL}/support`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to submit ticket" }));
    throw new Error(error.detail || "Failed to submit ticket");
  }

  return res.json();
};

export const getSupportTickets = async (): Promise<SupportTicket[]> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const res = await fetch(`${API_BASE_URL}/support`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`Failed to fetch support tickets: ${res.status} ${errorText}`);
  }

  const data = await res.json();

  if (!Array.isArray(data)) {
    throw new Error("Invalid response format from API");
  }

  return data as SupportTicket[];
};

export const updateSupportTicketStatus = async (
  ticketId: string,
  status: string
): Promise<SupportTicket> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const res = await fetch(`${API_BASE_URL}/support/${ticketId}/status`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ status }),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`Failed to update ticket status: ${res.status} ${errorText}`);
  }

  return res.json();
};

export const deleteSupportTicket = async (ticketId: string): Promise<void> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const res = await fetch(`${API_BASE_URL}/support/${ticketId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`Failed to delete ticket: ${res.status} ${errorText}`);
  }
};

// Profile API functions
export const getMyProfile = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const response = await fetch(`${API_BASE_URL}/users/profile`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  // Profile doesn't exist yet (404 is expected for users without profiles)
  if (response.status === 404) {
    throw new Error("Profile not found");
  }

  // Unauthorized - token might be expired or invalid
  if (response.status === 401) {
    throw new Error("Authentication failed. Please log in again.");
  }

  // Other errors should be thrown for proper error handling
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Failed to fetch profile" }));
    console.error("getMyProfile error:", response.status, errorData);
    throw new Error(errorData.detail || `Failed to fetch profile: ${response.status}`);
  }

  return response.json();
};

export const createProfile = async (data: {
  name?: string | null;
  campus?: string | null;
  contact_info?: { email?: string; phone?: string };
  profile_picture_url?: string | null;
}) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const profileResponse = await fetch(`${API_BASE_URL}/users/profile`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!profileResponse.ok) {
    const error = await profileResponse.json();
    throw new Error(error.detail || "Failed to create profile");
  }

  return profileResponse.json();
};

export const updateProfile = async (data: {
  name?: string | null;
  campus?: string | null;
  contact_info?: { email?: string; phone?: string };
  profile_picture_url?: string | null;
}) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const response = await fetch(`${API_BASE_URL}/users/profile`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update profile");
  }

  return response.json();
};

export const deleteProfile = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const response = await fetch(`${API_BASE_URL}/users/profile`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to delete profile");
  }
};

export const updateProfilePicture = async (file: File) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/users/profile/picture`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to upload profile picture");
  }

  return response.json();
};

export const removeProfilePicture = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const response = await fetch(`${API_BASE_URL}/users/profile`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ profile_picture_url: null }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to remove profile picture");
  }

  return response.json();
};
