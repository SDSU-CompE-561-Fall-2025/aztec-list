import { Category } from "./filters/category";
import { Condition } from "./filters/condition";

export interface ListingSummary {
  id: string;
  seller_id: string;
  title: string;
  description: string;
  price: number;
  category: Category;
  condition: Condition;
  thumbnail_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ListingSearchResponse {
  items: ListingSummary[];
  next_cursor: string | null;
  count: number;
}

export interface ImagePublic {
  id: string;
  listing_id: string;
  url: string;
  is_thumbnail: boolean;
  alt_text: string | null;
  created_at: string;
}

export interface ListingPublic {
  id: string;
  seller_id: string;
  title: string;
  description: string;
  price: number;
  category: Category;
  condition: Condition;
  thumbnail_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  images?: ImagePublic[];
}
