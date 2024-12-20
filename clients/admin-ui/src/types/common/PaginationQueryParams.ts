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
