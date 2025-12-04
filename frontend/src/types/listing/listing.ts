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
