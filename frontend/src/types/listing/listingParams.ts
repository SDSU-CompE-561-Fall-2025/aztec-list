import { Category } from "./filters/category";
import { Condition } from "./filters/condition";
import { Sort } from "./filters/sort";

export type ListingsParams = {
  q?: string;
  category?: Category;
  minPrice?: number;
  maxPrice?: number;
  condition?: Condition;
  sellerId?: string;
  limit?: number;
  offset?: number;
  sort?: Sort;
};
