import { useMemo, useState } from "react";

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

interface UsePurposesListOptions {
  dataUseFilter?: string | null;
  consumerFilter?: string | null;
  categoryFilter?: string | null;
  statusFilter?: string | null;
}

const usePurposesList = ({
  dataUseFilter = null,
  consumerFilter = null,
  categoryFilter = null,
  statusFilter = null,
}: UsePurposesListOptions = {}) => {
  const [searchQuery, setSearchQuery] = useState("");

  const { data, error, isLoading, isFetching } = useGetAllDataPurposesQuery({
    search: searchQuery || undefined,
    data_use: dataUseFilter ?? undefined,
    consumer: consumerFilter ?? undefined,
    category: categoryFilter ?? undefined,
    status: statusFilter ?? undefined,
  });

  const items: DataPurpose[] = useMemo(() => data?.items ?? [], [data?.items]);
  const total = data?.total ?? 0;
  const filterOptions = data?.filter_options ?? EMPTY_FILTER_OPTIONS;

  return {
    items,
    total,
    filterOptions,
    searchQuery,
    updateSearch: setSearchQuery,
    isLoading,
    isFetching,
    error,
  };
};

export default usePurposesList;
