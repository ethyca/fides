import {
  parseAsArrayOf,
  parseAsString,
  parseAsStringEnum,
  useQueryState,
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
  location: string | null;
  sort_field: string | null;
  sort_direction: ColumnSort | null;
}

interface UsePrivacyRequestsFiltersProps {
  pagination: ReturnType<typeof useAntPagination>;
}

/**
 * Hook for managing privacy request filters with URL query parameter synchronization.
 * Provides separate state groups for fuzzy search (throttled), modal filters
 * (id, from, to, status, action_type, location), and sort state (sort_field, sort_direction).
 * Automatically resets pagination when filters change.
 */
const usePrivacyRequestsFilters = ({
  pagination,
}: UsePrivacyRequestsFiltersProps) => {
  const [fuzzySearchTerm, setFuzzySearchTerm] = useQueryState(
    "search",
    parseAsString.withOptions({ throttleMs: 300 }),
  );

  const [modalFilters, setModalFilters] = useQueryStates(
    {
      from: parseAsString,
      to: parseAsString,
      status: parseAsArrayOf(
        parseAsStringEnum(Object.values(PrivacyRequestStatus)),
      ),
      action_type: parseAsArrayOf(parseAsStringEnum(Object.values(ActionType))),
      location: parseAsString,
    },
    {
      history: "push",
    },
  );

  // A user friendly count of the number of filters applied in the modal
  // It counts only filters applied in the modal, and counts the range date filter as one
  const modalFiltersCount = useMemo(() => {
    const filtersWithoutTo = { ...modalFilters, to: undefined };
    return Object.values(filtersWithoutTo).filter(
      (value) => value && value.length > 0,
    ).length;
  }, [modalFilters]);

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
      fuzzy_search_str: fuzzySearchTerm,
      from: modalFilters.from,
      to: modalFilters.to,
      status: modalFilters.status,
      action_type: modalFilters.action_type,
      location: modalFilters.location,
      sort_field: sortState.sort_field,
      sort_direction: sortState.sort_direction,
    }),
    [
      fuzzySearchTerm,
      modalFilters.from,
      modalFilters.to,
      modalFilters.status,
      modalFilters.action_type,
      modalFilters.location,
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
    fuzzySearchTerm,
    setFuzzySearchTerm,
    modalFilters,
    modalFiltersCount,
    setModalFilters,
    sortState,
    setSortState,
    filterQueryParams,
  };
};
export default usePrivacyRequestsFilters;
