import {
  parseAsArrayOf,
  parseAsString,
  parseAsStringEnum,
  useQueryStates,
} from "nuqs";
import { useEffect, useMemo } from "react";

import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { ActionType, ColumnSort, PrivacyRequestStatus } from "~/types/api";

export interface FilterQueryParams {
  fuzzy_search_str: string | null;
  from: string | null;
  to: string | null;
  status: PrivacyRequestStatus[] | null;
  action_type: ActionType[] | null;
  sort_field: string | null;
  sort_direction: ColumnSort | null;
}

interface UsePrivacyRequestsFiltersProps {
  pagination: ReturnType<typeof useAntPagination>;
}

/**
 * Hook for managing privacy request filters with URL query parameter synchronization.
 * Provides state groups for filters (search, from, to, status, action_type with throttled search)
 * and sort state (sort_field, sort_direction).
 * Automatically resets pagination when filters change.
 */
const usePrivacyRequestsFilters = ({
  pagination,
}: UsePrivacyRequestsFiltersProps) => {
  const [filters, setFilters] = useQueryStates(
    {
      search: parseAsString.withOptions({ throttleMs: 300 }),
      from: parseAsString,
      to: parseAsString,
      status: parseAsArrayOf(
        parseAsStringEnum(Object.values(PrivacyRequestStatus)),
      ),
      action_type: parseAsArrayOf(parseAsStringEnum(Object.values(ActionType))),
    },
    {
      history: "push",
    },
  );

  // A user friendly count of the number of filters applied
  // It counts only non-search filters, and counts the range date filter as one
  const filtersCount = useMemo(() => {
    const filtersWithoutSearchAndTo = {
      ...filters,
      search: undefined,
      to: undefined,
    };
    return Object.values(filtersWithoutSearchAndTo).filter(
      (value) => value && value.length > 0,
    ).length;
  }, [filters]);

  const [sortState, setSortState] = useQueryStates(
    {
      sort_field: parseAsString,
      sort_direction: parseAsStringEnum(Object.values(ColumnSort)),
    },
    {
      history: "push",
    },
  );

  const filterQueryParams: FilterQueryParams = useMemo(
    () => ({
      fuzzy_search_str: filters.search,
      from: filters.from,
      to: filters.to,
      status: filters.status,
      action_type: filters.action_type,
      sort_field: sortState.sort_field,
      sort_direction: sortState.sort_direction,
    }),
    [
      filters.search,
      filters.from,
      filters.to,
      filters.status,
      filters.action_type,
      sortState.sort_field,
      sortState.sort_direction,
    ],
  );

  // Reset pagination whenever filters change
  const { resetPagination } = pagination;
  useEffect(() => {
    resetPagination();
  }, [filterQueryParams, resetPagination]);

  return {
    filters,
    setFilters,
    filtersCount,
    sortState,
    setSortState,
    filterQueryParams,
  };
};
export default usePrivacyRequestsFilters;
