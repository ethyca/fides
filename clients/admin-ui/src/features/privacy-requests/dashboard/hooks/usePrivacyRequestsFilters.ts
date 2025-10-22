import {
  parseAsArrayOf,
  parseAsString,
  parseAsStringEnum,
  useQueryState,
  useQueryStates,
} from "nuqs";
import { useEffect, useMemo } from "react";

import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { ActionType, PrivacyRequestStatus } from "~/types/api";

export interface FilterQueryParams {
  fuzzy_search_str?: string;
  id?: string;
  from?: string;
  to?: string;
  status?: PrivacyRequestStatus[];
  action_type?: ActionType[];
  sort_field?: string;
  sort_direction?: string;
}

interface UsePrivacyRequestsFiltersProps {
  pagination: ReturnType<typeof useAntPagination>;
}

/**
 * Hook for managing privacy request filters with URL query parameter synchronization.
 * Provides separate state groups for fuzzy search (throttled), modal filters
 * (id, from, to, status, action_type), and sort state (sort_field, sort_direction).
 * Automatically resets pagination when filters change.
 */
const usePrivacyRequestsFilters = ({
  pagination,
}: UsePrivacyRequestsFiltersProps) => {
  const [fuzzySearchTerm, setFuzzySearchTerm] = useQueryState(
    "search",
    parseAsString.withDefault("").withOptions({ throttleMs: 300 }),
  );

  const [modalFilters, setModalFilters] = useQueryStates(
    {
      id: parseAsString.withDefault(""),
      from: parseAsString.withDefault(""),
      to: parseAsString.withDefault(""),
      status: parseAsArrayOf(
        parseAsStringEnum(Object.values(PrivacyRequestStatus)),
      ).withDefault([]),
      action_type: parseAsArrayOf(
        parseAsStringEnum(Object.values(ActionType)),
      ).withDefault([]),
    },
    {
      history: "push",
    },
  );

  const [sortState, setSortState] = useQueryStates(
    {
      sort_field: parseAsString.withDefault(""),
      sort_direction: parseAsString.withDefault(""),
    },
    {
      history: "push",
    },
  );

  const filterQueryParams: FilterQueryParams = useMemo(() => {
    return {
      fuzzy_search_str: fuzzySearchTerm,
      id: modalFilters.id,
      from: modalFilters.from,
      to: modalFilters.to,
      status: modalFilters.status,
      action_type: modalFilters.action_type,
      sort_field: sortState.sort_field,
      sort_direction: sortState.sort_direction,
    };
  }, [fuzzySearchTerm, modalFilters, sortState]);

  // Reset pagination whenever filters change
  useEffect(() => {
    pagination.resetPagination();
  }, [filterQueryParams, pagination]);

  return {
    fuzzySearchTerm,
    setFuzzySearchTerm,
    modalFilters,
    setModalFilters,
    sortState,
    setSortState,
    filterQueryParams,
  };
};
export default usePrivacyRequestsFilters;
