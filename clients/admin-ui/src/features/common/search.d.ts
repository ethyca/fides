/**
 * Search state interface
 */
export interface SearchState {
  searchQuery?: string;
}

/**
 * Configuration for search (standalone or table)
 */
export interface SearchConfig {
  defaultSearchQuery?: string;
  onSearchChange?: (state: SearchState) => void;
  disableUrlState?: boolean;
}

/**
 * Updates for search URL state
 */
export interface SearchQueryParams {
  search?: string | null;
}
