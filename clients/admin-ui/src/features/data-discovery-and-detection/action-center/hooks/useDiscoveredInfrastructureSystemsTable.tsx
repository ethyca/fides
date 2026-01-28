import { useCallback, useEffect, useMemo } from "react";

import { useSearch } from "~/features/common/hooks";
import {
  ACTION_CENTER_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { StagedResourceAPIResponse } from "~/types/api";
import { DiffStatus } from "~/types/api/models/DiffStatus";

import { useGetIdentityProviderMonitorResultsQuery } from "../../discovery-detection.slice";
import { MONITOR_TYPES } from "../utils/getMonitorType";
import useActionCenterTabs, {
  ActionCenterTabHash,
} from "./useActionCenterTabs";

interface UseDiscoveredInfrastructureSystemsTableConfig {
  monitorId?: string;
  statusFilters?: string[] | null;
  vendorFilters?: string[] | null;
  dataUsesFilters?: string[] | null;
}

export const useDiscoveredInfrastructureSystemsTable = ({
  monitorId,
  statusFilters,
  vendorFilters,
  dataUsesFilters,
}: UseDiscoveredInfrastructureSystemsTableConfig) => {
  const { paginationProps, pageIndex, pageSize, resetPagination } =
    useAntPagination({
      defaultPageSize: 50,
    });
  const search = useSearch();

  const tabs = useActionCenterTabs();
  const { activeTab, filterTabs, activeParams, onTabChange } = tabs;

  // Map status filters to diff_status parameter
  // Status filters now come directly as diff_status values from the API
  const diffStatusFilters = useMemo(() => {
    if (!statusFilters || statusFilters.length === 0) {
      return activeParams.diff_status;
    }

    // Status filters are now diff_status values directly
    const diffStatuses = statusFilters as DiffStatus[];

    // Convert single-element array to string for API compatibility
    if (diffStatuses.length === 1) {
      return diffStatuses[0];
    }
    return diffStatuses.length > 0 ? diffStatuses : activeParams.diff_status;
  }, [statusFilters, activeParams.diff_status]);

  // Map vendor filters to vendor_id parameter
  // Pass "known" and "unknown" directly to the API
  const vendorIdFilters = useMemo(() => {
    if (!vendorFilters || vendorFilters.length === 0) {
      return undefined;
    }
    return vendorFilters;
  }, [vendorFilters]);

  // Map data uses filters
  const dataUsesFilterParams = useMemo(() => {
    if (!dataUsesFilters || dataUsesFilters.length === 0) {
      return undefined;
    }
    return dataUsesFilters;
  }, [dataUsesFilters]);

  // Reset pagination when filters change
  useEffect(() => {
    resetPagination();
  }, [statusFilters, vendorFilters, dataUsesFilters, resetPagination]);

  const oktaDataQuery = useGetIdentityProviderMonitorResultsQuery(
    {
      // @ts-expect-error - will skip query if monitorId is not defined
      monitor_config_key: monitorId,
      page: pageIndex,
      size: pageSize,
      search: search.searchQuery,
      diff_status: diffStatusFilters,
      vendor_id: vendorIdFilters,
      data_uses: dataUsesFilterParams,
    },
    {
      refetchOnMountOrArgChange: true,
      skip: !monitorId,
    },
  );

  const {
    data: oktaData,
    isLoading: oktaIsLoading,
    isFetching: oktaIsFetching,
    refetch: refetchOktaData,
  } = oktaDataQuery;

  const data = useMemo(
    () => ({
      items: oktaData?.items ?? [],
      total: oktaData?.total ?? 0,
    }),
    [oktaData],
  );

  const handleTabChange = useCallback(
    async (tab: string | ActionCenterTabHash) => {
      await onTabChange(tab as ActionCenterTabHash);
      resetPagination();
      // Force refetch when tab changes to ensure fresh data
      refetchOktaData();
    },
    [onTabChange, resetPagination, refetchOktaData],
  );

  const rowClickUrl = useCallback(
    (record: StagedResourceAPIResponse) => {
      const recordId = record.urn ?? UNCATEGORIZED_SEGMENT;
      const activeTabHash = activeTab ? `#${activeTab}` : "";
      return `${ACTION_CENTER_ROUTE}/${MONITOR_TYPES.INFRASTRUCTURE}/${monitorId}/${recordId}${activeTabHash}`;
    },
    [monitorId, activeTab],
  );

  return {
    // Data
    data,
    isLoading: oktaIsLoading,
    isFetching: oktaIsFetching,
    refetch: refetchOktaData,

    // Errors
    error: oktaDataQuery.error,

    // Search
    searchQuery: search.searchQuery,
    updateSearch: search.updateSearch,

    // Pagination
    paginationProps,

    // Tabs
    filterTabs,
    activeTab,
    handleTabChange,
    activeParams,

    // Row click handler
    rowClickUrl,

    // Selection helpers
    getRecordKey: useCallback(
      (record: StagedResourceAPIResponse) =>
        record.urn ?? record.vendor_id ?? record.name ?? UNCATEGORIZED_SEGMENT,
      [],
    ),
  };
};
