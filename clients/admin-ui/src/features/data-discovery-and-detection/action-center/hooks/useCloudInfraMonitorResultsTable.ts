import { useCallback, useEffect, useMemo, useState } from "react";

import { useSearch } from "~/features/common/hooks";
import { UNCATEGORIZED_SEGMENT } from "~/features/common/nav/routes";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { CloudInfraStagedResource } from "~/types/api/models/CloudInfraStagedResource";
import { DiffStatus } from "~/types/api/models/DiffStatus";

import { useGetCloudInfraMonitorResultsQuery } from "../../discovery-detection.slice";

interface UseCloudInfraMonitorResultsTableConfig {
  monitorId?: string;
  statusFilters?: string[] | null;
  locationFilters?: string[] | null;
  serviceFilters?: string[] | null;
  accountFilters?: string[] | null;
}

export const useCloudInfraMonitorResultsTable = ({
  monitorId,
  statusFilters,
  locationFilters,
  serviceFilters,
  accountFilters,
}: UseCloudInfraMonitorResultsTableConfig) => {
  const { paginationProps, pageIndex, pageSize, resetPagination } =
    useAntPagination({
      defaultPageSize: 50,
    });
  const search = useSearch();
  const [searchRegex, setSearchRegex] = useState<boolean>(false);

  // Reset pagination when filters change
  useEffect(() => {
    resetPagination();
  }, [
    statusFilters,
    locationFilters,
    serviceFilters,
    accountFilters,
    resetPagination,
  ]);

  const cloudInfraDataQuery = useGetCloudInfraMonitorResultsQuery(
    {
      monitor_config_id: monitorId ?? "",
      page: pageIndex,
      size: pageSize,
      search: search.searchQuery,
      search_regex: searchRegex || undefined,
      diff_status: statusFilters?.length
        ? (statusFilters as DiffStatus[])
        : undefined,
      location: locationFilters?.length ? locationFilters : undefined,
      cloud_account_id: accountFilters?.length ? accountFilters : undefined,
      service: serviceFilters?.length ? serviceFilters : undefined,
    },
    {
      refetchOnMountOrArgChange: true,
      skip: !monitorId,
    },
  );

  const {
    data: cloudInfraData,
    isLoading,
    isFetching,
    refetch,
  } = cloudInfraDataQuery;

  const data = useMemo(
    () => ({
      items: cloudInfraData?.items ?? [],
      total: cloudInfraData?.total ?? 0,
    }),
    [cloudInfraData],
  );

  return {
    // Data
    data,
    isLoading,
    isFetching,
    refetch,
    // Filters
    diffStatusFilters: statusFilters?.length
      ? (statusFilters as DiffStatus[])
      : undefined,
    locationFilters,
    serviceFilters,
    accountFilters,

    // Errors
    error: cloudInfraDataQuery.error,

    // Search
    searchQuery: search.searchQuery,
    updateSearch: search.updateSearch,
    searchRegex,
    setSearchRegex,

    // Pagination
    paginationProps,

    // Selection helpers
    getRecordKey: useCallback(
      (record: CloudInfraStagedResource) =>
        record.urn ?? record.source_id ?? record.name ?? UNCATEGORIZED_SEGMENT,
      [],
    ),
  };
};
