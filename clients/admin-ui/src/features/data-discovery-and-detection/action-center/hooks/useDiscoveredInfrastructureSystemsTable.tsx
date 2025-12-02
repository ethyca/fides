import { useCallback, useEffect, useMemo } from "react";

import { useSearch } from "~/features/common/hooks";
import {
  ACTION_CENTER_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import {
  StagedResourceAPIResponse,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";
import { DiffStatus } from "~/types/api/models/DiffStatus";

import { useGetIdentityProviderMonitorResultsQuery } from "../../discovery-detection.slice";
import {
  InfrastructureSystemFilterLabel,
  mapStatusFilterToDiffStatus,
  mapStatusFilterToMetadataStatus,
} from "../constants/InfrastructureSystemsFilters.const";
import { MONITOR_TYPES } from "../utils/getMonitorType";
import useActionCenterTabs, {
  ActionCenterTabHash,
} from "./useActionCenterTabs";

interface UseDiscoveredInfrastructureSystemsTableConfig {
  monitorId: string;
  statusFilters?: InfrastructureSystemFilterLabel[] | null;
  vendorFilters?: string[] | null;
}

// Extended type to include diff_status for list items
type InfrastructureSystemListItem = SystemStagedResourcesAggregateRecord & {
  diff_status?: string | null;
  urn?: string;
};

export const useDiscoveredInfrastructureSystemsTable = ({
  monitorId,
  statusFilters,
  vendorFilters,
}: UseDiscoveredInfrastructureSystemsTableConfig) => {
  const { paginationProps, pageIndex, pageSize, resetPagination } =
    useAntPagination({
      defaultPageSize: 50,
    });
  const search = useSearch();

  const tabs = useActionCenterTabs();
  const { activeTab, filterTabs, activeParams, onTabChange } = tabs;

  // Map status filters to diff_status and status parameters
  const diffStatusFilters = useMemo(() => {
    if (!statusFilters || statusFilters.length === 0) {
      return activeParams.diff_status;
    }

    const diffStatuses: DiffStatus[] = [];
    statusFilters.forEach((filter) => {
      const diffStatus = mapStatusFilterToDiffStatus(filter);
      if (diffStatus) {
        diffStatuses.push(diffStatus);
      }
    });

    // If we have filters from statusFilters, use them; otherwise fall back to activeParams
    // Convert single-element array to string for API compatibility
    if (diffStatuses.length === 1) {
      return diffStatuses[0];
    }
    return diffStatuses.length > 0 ? diffStatuses : activeParams.diff_status;
  }, [statusFilters, activeParams.diff_status]);

  // Map status filters to metadata status
  const metadataStatusFilters = useMemo(() => {
    if (!statusFilters || statusFilters.length === 0) {
      return undefined;
    }

    const statuses: string[] = [];
    statusFilters.forEach((filter) => {
      const status = mapStatusFilterToMetadataStatus(filter);
      if (status) {
        statuses.push(status);
      }
    });

    return statuses.length > 0 ? statuses : undefined;
  }, [statusFilters]);

  // Map vendor filters to vendor_id parameter
  // "known" = has vendor_id, "unknown" = no vendor_id
  // The backend API uses "null" to filter for items without vendor_id
  const vendorIdFilters = useMemo(() => {
    if (!vendorFilters || vendorFilters.length === 0) {
      return undefined;
    }

    const vendorIds: string[] = [];
    if (vendorFilters.includes("unknown")) {
      vendorIds.push("null");
    }
    // Note: "known" filter would require getting all possible vendor IDs,
    // which isn't practical. If both filters are selected or only "known" is selected,
    // we don't apply any vendor filter (show all).
    if (vendorFilters.includes("known") && !vendorFilters.includes("unknown")) {
      // Backend should support filtering for items WITH vendor_id
      // Using "not_null" as a special indicator (backend implementation required)
      return "not_null";
    }

    return vendorIds.length > 0 ? vendorIds : undefined;
  }, [vendorFilters]);

  // Reset pagination when filters change
  useEffect(() => {
    resetPagination();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilters, vendorFilters]);

  const oktaDataQuery = useGetIdentityProviderMonitorResultsQuery(
    {
      monitor_config_key: monitorId,
      page: pageIndex,
      size: pageSize,
      search: search.searchQuery,
      diff_status: diffStatusFilters,
      status: metadataStatusFilters,
      vendor_id: vendorIdFilters,
    },
    {
      refetchOnMountOrArgChange: true,
    },
  );

  const {
    data: oktaData,
    isLoading: oktaIsLoading,
    isFetching: oktaIsFetching,
    refetch: refetchOktaData,
  } = oktaDataQuery;

  // Force refetch when activeTab changes to ensure fresh data
  useEffect(() => {
    refetchOktaData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  // Transform API data to table format
  // Vendor filters are now applied server-side via the vendor_id query parameter
  const transformedData = useMemo((): {
    items: InfrastructureSystemListItem[];
    total: number;
  } => {
    if (!oktaData?.items) {
      return { items: [], total: 0 };
    }

    const items: InfrastructureSystemListItem[] = oktaData.items.map(
      (item: StagedResourceAPIResponse): InfrastructureSystemListItem => {
        return {
          id: item.urn,
          urn: item.urn,
          name: item.name ?? null,
          system_key: item.system_key ?? null,
          data_uses: item.data_uses ?? [],
          vendor_id: item.vendor_id ?? null,
          total_updates: 1,
          locations: item.locations ?? [],
          domains: item.domain ? [item.domain] : [],
          consent_status: null,
          metadata: item.metadata ?? null,
          diff_status: item.diff_status ?? null,
        };
      },
    );

    return {
      items,
      total: oktaData.total ?? 0,
    };
  }, [oktaData]);

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
    (record: InfrastructureSystemListItem) => {
      const recordId = record.urn ?? record.id ?? UNCATEGORIZED_SEGMENT;
      const activeTabHash = activeTab ? `#${activeTab}` : "";
      return `${ACTION_CENTER_ROUTE}/${MONITOR_TYPES.INFRASTRUCTURE}/${monitorId}/${recordId}${activeTabHash}`;
    },
    [monitorId, activeTab],
  );

  return {
    // Data
    data: transformedData,
    isLoading: oktaIsLoading,
    isFetching: oktaIsFetching,
    refetch: refetchOktaData,

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
      (record: InfrastructureSystemListItem) =>
        record.urn ??
        record.id ??
        record.vendor_id ??
        record.name ??
        UNCATEGORIZED_SEGMENT,
      [],
    ),
  };
};
