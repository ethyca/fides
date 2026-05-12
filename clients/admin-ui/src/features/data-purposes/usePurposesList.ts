import { parseAsString, useQueryStates } from "nuqs";
import { useMemo } from "react";

import {
  type DataPurpose,
  type DataPurposeFilterOptions,
  useGetAllDataPurposesQuery,
} from "./data-purpose.slice";

const EMPTY_FILTER_OPTIONS: DataPurposeFilterOptions = {
  consumers: [],
  data_uses: [],
  categories: [],
  statuses: [],
};

const FILTER_PARSERS = {
  search: parseAsString.withOptions({ throttleMs: 300 }),
  data_use: parseAsString,
  consumer: parseAsString,
  category: parseAsString,
  status: parseAsString,
};

const usePurposesList = () => {
  const [filters, setFilters] = useQueryStates(FILTER_PARSERS);

  const filterParams = useMemo(
    () => ({
      search: filters.search ?? undefined,
      data_use: filters.data_use ?? undefined,
      consumer: filters.consumer ?? undefined,
      category: filters.category ?? undefined,
      status: filters.status ?? undefined,
    }),
    [filters],
  );

  const { data, error, isLoading, isFetching } =
    useGetAllDataPurposesQuery(filterParams);

  const items: DataPurpose[] = useMemo(() => data?.items ?? [], [data?.items]);
  const total = data?.total ?? 0;
  const filterOptions = data?.filter_options ?? EMPTY_FILTER_OPTIONS;

  return {
    items,
    total,
    filterOptions,
    isLoading,
    isFetching,
    error,
    searchQuery: filters.search ?? "",
    setSearchQuery: (v: string) => setFilters({ search: v || null }),
    dataUseFilter: filters.data_use,
    setDataUseFilter: (v: string | null) => setFilters({ data_use: v }),
    consumerFilter: filters.consumer,
    setConsumerFilter: (v: string | null) => setFilters({ consumer: v }),
    categoryFilter: filters.category,
    setCategoryFilter: (v: string | null) => setFilters({ category: v }),
    statusFilter: filters.status,
    setStatusFilter: (v: string | null) => setFilters({ status: v }),
    clearFilters: () =>
      setFilters({
        search: null,
        data_use: null,
        consumer: null,
        category: null,
        status: null,
      }),
    filterParams,
  };
};

export default usePurposesList;
