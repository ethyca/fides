import { Dayjs } from "dayjs";

export interface PaginationQueryParams {
  page: number;
  size: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  size: number;
  total: number;
  pages: number;
}

export interface SearchQueryParams {
  search?: string;
}

export interface SortQueryParams<T = string> {
  sort_by?: T | T[];
  sort_asc?: boolean;
}

export type DateRangeParams = {
  startDate?: Dayjs | null;
  endDate?: Dayjs | null;
};
