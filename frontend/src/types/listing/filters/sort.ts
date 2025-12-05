export const SORT_OPTIONS = ["recent", "price_asc", "price_desc"] as const;

export type Sort = (typeof SORT_OPTIONS)[number];