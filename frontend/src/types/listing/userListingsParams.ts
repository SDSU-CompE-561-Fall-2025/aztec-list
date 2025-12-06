import { Sort } from "./filters/sort";

export interface UserListingsParams {
  limit?: number;
  offset?: number;
  sort?: Sort;
  include_inactive?: boolean;
}
