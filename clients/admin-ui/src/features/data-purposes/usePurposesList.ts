import { useMemo } from "react";

import { useTableState } from "~/features/common/table/hooks";

import {
  type DataPurpose,
  useGetAllDataPurposesQuery,
} from "./data-purpose.slice";

interface UsePurposesListOptions {
  enabled?: boolean;
  dataUseFilter?: string | null;
}

/**
 * Fetches the paginated list of data purposes with server-side search.
 *
 * Table state is kept in-memory (URL sync disabled) because this view
 * fetches everything in a single page and does client-side filtering —
 * surfacing `?page=1&size=200` in the address bar would be misleading.
 * Revisit once server-side filters land and real pagination is wired up.
 * The `data_use` filter is controlled by the caller so it can be lifted
 * into a parent component for cross-component coordination.
 */
const usePurposesList = ({
  enabled = true,
  dataUseFilter = null,
}: UsePurposesListOptions = {}) => {
  const tableState = useTableState({
    disableUrlState: true,
    pagination: {
      // Large page size keeps all purposes client-side so `usePurposeCardFilters`
      // can apply the `consumer` / `status` / `category` filters without a
      // round-trip. Drop this once the list endpoint accepts those params —
      // see the note in `usePurposeCardFilters.ts`.
      defaultPageSize: 200,
      pageSizeOptions: [50, 100, 200],
    },
    search: { defaultSearchQuery: "" },
  });

  const { pageIndex, pageSize, searchQuery, updateSearch } = tableState;

  const { data, error, isLoading, isFetching } = useGetAllDataPurposesQuery(
    {
      page: pageIndex,
      size: pageSize,
      search: searchQuery || undefined,
      data_use: dataUseFilter ?? undefined,
    },
    { skip: !enabled },
  );

  const items: DataPurpose[] = useMemo(() => data?.items ?? [], [data?.items]);
  const total = data?.total ?? 0;

  return {
    items,
    total,
    searchQuery: searchQuery ?? "",
    updateSearch,
    isLoading,
    isFetching,
    error,
  };
};

export default usePurposesList;
