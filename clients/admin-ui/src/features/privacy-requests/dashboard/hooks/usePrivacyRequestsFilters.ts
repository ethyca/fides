import { parseAsString, useQueryState } from "nuqs";
import { useEffect, useMemo } from "react";

import { useAntPagination } from "~/features/common/pagination/useAntPagination";

interface UsePrivacyRequestsFiltersProps {
  pagination: ReturnType<typeof useAntPagination>;
}

const usePrivacyRequestsFilters = ({
  pagination,
}: UsePrivacyRequestsFiltersProps) => {
  const [fuzzySearchTerm, setFuzzySearchTerm] = useQueryState(
    "search",
    parseAsString.withDefault("").withOptions({ throttleMs: 100 }),
  );

  const filterQueryParams = useMemo(() => {
    return {
      fuzzy_search_str: fuzzySearchTerm,
    };
  }, [fuzzySearchTerm]);

  // Reset pagination whenever filters change
  useEffect(() => {
    pagination.resetPagination();
  }, [filterQueryParams, pagination]);

  return {
    fuzzySearchTerm,
    setFuzzySearchTerm,
    filterQueryParams,
  };
};
export default usePrivacyRequestsFilters;
