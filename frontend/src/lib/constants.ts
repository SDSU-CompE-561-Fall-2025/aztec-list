// Route constants
export const LISTINGS_BASE_URL = "/listings";

// API configuration
// Use environment variables with fallback to localhost for development
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

export const STATIC_BASE_URL = process.env.NEXT_PUBLIC_STATIC_BASE_URL || "http://127.0.0.1:8000";

export const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "Aztec List";

// Query and pagination defaults
export const DEFAULT_SORT = "recent";
export const DEFAULT_LIMIT = 16;

// Search configuration
export const MAX_SEARCH_LENGTH = 200;

// React Query configuration
export const QUERY_RETRY_COUNT = 1;

// UI configuration
export const SKELETON_LOADING_COUNT = 15;
