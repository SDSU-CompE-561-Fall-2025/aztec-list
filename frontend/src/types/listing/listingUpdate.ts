import { Category } from "./filters/category";
import { Condition } from "./filters/condition";

export interface ListingUpdate {
  title?: string;
  description?: string;
  price?: number;
  category?: Category;
  condition?: Condition;
  is_active?: boolean;
}
