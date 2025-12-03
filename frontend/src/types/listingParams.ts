export type listingsParams = {
  q?: string;           // search text from ?q=
  minPrice?: number;
  maxPrice?: number;
  category?: string;    // change to enum
  limit?: number;
  offset?: number;
  sort?: "recent" | "PRICE_ASC" | "PRICE_DESC"; 
};

