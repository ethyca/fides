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

  // Map status filters to diff_status parameter
  const diffStatusFilters = useMemo((): DiffStatus[] | undefined => {
    if (!statusFilters || statusFilters.length === 0) {
      return undefined;
    }
    return statusFilters as DiffStatus[];
  }, [statusFilters]);

  // Map location filters
  const locationFilterParams = useMemo(() => {
    if (!locationFilters || locationFilters.length === 0) {
      return undefined;
    }
    return locationFilters;
  }, [locationFilters]);

  // Map service filters
  const serviceFilterParams = useMemo(() => {
    if (!serviceFilters || serviceFilters.length === 0) {
      return undefined;
    }
    return serviceFilters;
  }, [serviceFilters]);

  // Map account filters
  const accountFilterParams = useMemo(() => {
    if (!accountFilters || accountFilters.length === 0) {
      return undefined;
    }
    return accountFilters;
  }, [accountFilters]);

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
      // @ts-expect-error - will skip query if monitorId is not defined
      monitor_config_id: monitorId,
      page: pageIndex,
      size: pageSize,
      search: search.searchQuery,
      search_regex: searchRegex || undefined,
      diff_status: diffStatusFilters,
      location: locationFilterParams,
      cloud_account_id: accountFilterParams,
      service: serviceFilterParams,
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
    diffStatusFilters,
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
