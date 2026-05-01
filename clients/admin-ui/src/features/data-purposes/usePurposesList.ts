import { useCallback, useMemo, useState } from "react";

import {
  type DataPurpose,
  type DataPurposeFilterOptions,
  useGetAllDataPurposesQuery,
} from "./data-purpose.slice";

const EMPTY_FILTER_OPTIONS: DataPurposeFilterOptions = {
  consumers: [],
  data_uses: [],
  categories: [],
};

const usePurposesList = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [dataUseFilter, setDataUseFilter] = useState<string | null>(null);
  const [consumerFilter, setConsumerFilter] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);

  const filterParams = useMemo(
    () => ({
      search: searchQuery || undefined,
      data_use: dataUseFilter ?? undefined,
      consumer: consumerFilter ?? undefined,
      category: categoryFilter ?? undefined,
      status: statusFilter ?? undefined,
    }),
    [searchQuery, dataUseFilter, consumerFilter, categoryFilter, statusFilter],
  );

  const { data, error, isLoading, isFetching } =
    useGetAllDataPurposesQuery(filterParams);

  const items: DataPurpose[] = useMemo(() => data?.items ?? [], [data?.items]);
  const total = data?.total ?? 0;
  const filterOptions = data?.filter_options ?? EMPTY_FILTER_OPTIONS;

  const clearFilters = useCallback(() => {
    setSearchQuery("");
    setDataUseFilter(null);
    setConsumerFilter(null);
    setCategoryFilter(null);
    setStatusFilter(null);
  }, []);

  return {
    items,
    total,
    filterOptions,
    isLoading,
    isFetching,
    error,
    searchQuery,
    setSearchQuery,
    dataUseFilter,
    setDataUseFilter,
    consumerFilter,
    setConsumerFilter,
    categoryFilter,
    setCategoryFilter,
    statusFilter,
    setStatusFilter,
    clearFilters,
    filterParams,
  };
};

export default usePurposesList;
