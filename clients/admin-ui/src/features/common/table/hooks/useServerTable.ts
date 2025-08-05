import { useMemo } from "react";

import { ServerTableResult } from "./types";
import { useTableState } from "./useTableState";

/**
 * Custom hook for server-side table operations
 *
 * @param additionalParams - Additional parameters to include in query
 * @param tableStateConfig - Table state configuration (passed to useTableState)
 * @returns Table state, server data, and utilities
 *
 * @example
 * ```tsx
 * const {
 *   state,
 *   data,
 *   isLoading,
 *   updatePagination,
 *   updateSorting,
 *   resetState
 * } = useServerTable(
 *   { monitorId, systemId }, // additionalParams
 *   { urlSync: { pagination: true, sorting: true } } // tableStateConfig
 * );
 * ```
 */
export const useServerTable = <TData = any>(
  additionalParams: Record<string, any> = {},
  tableStateConfig = {},
) => {
  // Get table state management
  const tableState = useTableState(tableStateConfig);

  // Prepare query parameters
  const queryParams = useMemo(
    () => ({
      ...tableState.state,
      ...additionalParams,
    }),
    [tableState.state, additionalParams],
  );

  // This is a template hook - in practice, you would use your actual query hook here
  // For example: const queryResult = useGetDiscoveredAssetsQuery(queryParams, { skip: !enabled })
  const queryResult = {
    data: undefined,
    isLoading: false,
    isFetching: false,
    error: undefined,
    refetch: () => {},
  };

  const serverResult: ServerTableResult<TData> = {
    data: queryResult.data,
    isLoading: queryResult.isLoading,
    isFetching: queryResult.isFetching,
    error: queryResult.error,
    refetch: queryResult.refetch,
  };

  return {
    // Table state
    ...tableState,

    // Server data
    ...serverResult,

    // Combined utilities
    isLoadingOrFetching: serverResult.isLoading || serverResult.isFetching,
    hasData: !!serverResult.data?.items?.length,
    totalRows: serverResult.data?.total ?? 0,

    // Pagination helpers
    isPaginationDisabled: serverResult.isLoading,

    // Query parameters for external use
    queryParams,
  };
};

/**
 * Hook specifically for RTK Query integration
 *
 * @param queryHook - RTK Query hook
 * @param tableStateConfig - Table state configuration
 * @returns Table state, query result, and utilities
 *
 * @example
 * ```tsx
 * const result = useServerTableWithRTK(
 *   useGetDiscoveredAssetsQuery,
 *   {
 *     urlSync: { pagination: true, sorting: true },
 *     pagination: { defaultPageSize: 50 }
 *   }
 * );
 * ```
 */
export const useServerTableWithRTK = <TQueryArg = any>(
  queryHook: (arg: TQueryArg, options?: any) => any,
  queryArg: TQueryArg,
  tableStateConfig = {},
  queryOptions = {},
) => {
  const tableState = useTableState(tableStateConfig);
  const queryResult = queryHook(queryArg, queryOptions);

  return {
    ...tableState,
    ...queryResult,
    isLoadingOrFetching: queryResult.isLoading || queryResult.isFetching,
    hasData: !!queryResult.data?.items?.length,
    totalRows: queryResult.data?.total ?? 0,
    queryParams: queryArg,
  };
};
