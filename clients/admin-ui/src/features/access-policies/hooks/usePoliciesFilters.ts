import { parseAsString, parseAsStringEnum, useQueryStates } from "nuqs";

import { ViewMode } from "../types";

/**
 * Manages all list-page filter state, synced to query params.
 * Search is throttled (300ms); all other params sync immediately.
 */
export const usePoliciesFilters = () => {
  const [filters, setFilters] = useQueryStates({
    search: parseAsString.withOptions({ throttleMs: 300 }),
    control: parseAsString,
    status: parseAsString,
    view: parseAsStringEnum<ViewMode>([ViewMode.CARDS, ViewMode.TABLE]),
  });

  return {
    searchQuery: filters.search ?? "",
    setSearchQuery: (v: string) => setFilters({ search: v || null }),
    controlFilter: filters.control ?? undefined,
    setControlFilter: (v: string | undefined) =>
      setFilters({ control: v ?? null }),
    enabledFilter: filters.status ?? undefined,
    setEnabledFilter: (v: string | undefined) =>
      setFilters({ status: v ?? null }),
    viewMode: filters.view ?? ViewMode.CARDS,
    setViewMode: (v: ViewMode) => setFilters({ view: v }),
  };
};
