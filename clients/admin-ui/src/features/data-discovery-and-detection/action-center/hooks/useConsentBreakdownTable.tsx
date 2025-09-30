import {
  AntColumnsType as ColumnsType,
  AntTypography as Typography,
  formatIsoLocation,
  isoStringToEntry,
} from "fidesui";
import { useMemo } from "react";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { DEFAULT_PAGE_SIZES } from "~/features/common/table/constants";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import {
  ConsentBreakdown,
  PrivacyNoticeRegion,
  StagedResourceAPIResponse,
} from "~/types/api";

import { useGetConsentBreakdownQuery } from "../action-center.slice";
import {
  ConsentBreakdownColumnKeys,
  DiscoveryErrorStatuses,
} from "../constants";

const { Link } = Typography;

interface UseConsentBreakdownTableConfig {
  stagedResource: StagedResourceAPIResponse;
}

export const useConsentBreakdownTable = ({
  stagedResource,
}: UseConsentBreakdownTableConfig) => {
  const tableState = useTableState<ConsentBreakdownColumnKeys>({
    pagination: {
      defaultPageSize: 10,
      pageSizeOptions: [10, ...DEFAULT_PAGE_SIZES],
    },
  });

  const { pageIndex, pageSize } = tableState;

  const { data, isFetching, isError } = useGetConsentBreakdownQuery({
    stagedResourceUrn: stagedResource.urn,
    statuses: DiscoveryErrorStatuses,
    page: pageIndex,
    size: pageSize,
  });

  const { items, total: totalRows } = useMemo(
    () =>
      data || {
        items: [],
        total: 0,
        pages: 0,
        filterOptions: { assigned_users: [], systems: [] },
      },
    [data],
  );

  const antTableConfig = useMemo(
    () => ({
      enableSelection: false,
      getRowKey: (record: ConsentBreakdown) =>
        `${record.location}-${record.page}`,
      isLoading: isFetching,
      dataSource: items,
      totalRows: totalRows ?? 0,
    }),
    [isFetching, items, totalRows],
  );

  const antTable = useAntTable<ConsentBreakdown, ConsentBreakdownColumnKeys>(
    tableState,
    antTableConfig,
  );

  const columns: ColumnsType<ConsentBreakdown> = useMemo(
    () => [
      {
        title: "Location",
        dataIndex: ConsentBreakdownColumnKeys.LOCATION,
        key: ConsentBreakdownColumnKeys.LOCATION,
        render: (location: string) => {
          const isoEntry = isoStringToEntry(location);

          return isoEntry
            ? formatIsoLocation({ isoEntry, showFlag: true })
            : (PRIVACY_NOTICE_REGION_RECORD?.[
                location as PrivacyNoticeRegion
              ] ?? location);
        },
      },
      {
        title: "Page",
        dataIndex: ConsentBreakdownColumnKeys.PAGE,
        key: ConsentBreakdownColumnKeys.PAGE,
        render: (page: string) => (
          <Link href={page} target="_blank" rel="noopener noreferrer">
            {page}
          </Link>
        ),
      },
    ],
    [],
  );

  return {
    // Table state and data
    columns,
    data,
    isLoading: isFetching,
    isError,
    totalRows,

    // Ant Design table integration
    tableProps: antTable.tableProps,

    // Utilities
    hasData: items.length > 0,
  };
};
