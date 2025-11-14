import {
  createParser,
  parseAsArrayOf,
  parseAsString,
  parseAsStringEnum,
  useQueryStates,
} from "nuqs";
import { useEffect, useMemo } from "react";

import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { ActionType, ColumnSort, PrivacyRequestStatus } from "~/types/api";

// Custom parser for custom_privacy_request_fields
// Serializes as JSON string in URL query params
const parseAsCustomFields = createParser({
  parse: (value: string) => {
    try {
      return JSON.parse(value) as Record<string, string | null>;
    } catch {
      return null;
    }
  },
  serialize: (value: Record<string, string | null>) => JSON.stringify(value),
});

export interface FilterQueryParams {
  fuzzy_search_str: string | null;
  from: string | null;
  to: string | null;
  status: PrivacyRequestStatus[] | null;
  action_type: ActionType[] | null;
  custom_privacy_request_fields: Record<string, string | null> | null;
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
      custom_privacy_request_fields: parseAsCustomFields,
    },
    {
      history: "push",
    },
  );

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
      custom_privacy_request_fields: filters.custom_privacy_request_fields,
      sort_field: sortState.sort_field,
      sort_direction: sortState.sort_direction,
    }),
    [
      filters.search,
      filters.from,
      filters.to,
      filters.status,
      filters.action_type,
      filters.custom_privacy_request_fields,
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
    sortState,
    setSortState,
    filterQueryParams,
  };
};
export default usePrivacyRequestsFilters;
