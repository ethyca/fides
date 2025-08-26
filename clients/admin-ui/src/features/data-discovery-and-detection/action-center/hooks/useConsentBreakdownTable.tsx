import {
  AntColumnsType as ColumnsType,
  AntTypography as Typography,
} from "fidesui";
import { useMemo } from "react";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { DEFAULT_PAGE_SIZES } from "~/features/common/table/constants";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import {
  ConsentBreakdown,
  ConsentStatus,
  PrivacyNoticeRegion,
  StagedResourceAPIResponse,
} from "~/types/api";

import { useGetConsentBreakdownQuery } from "../action-center.slice";
import { ConsentBreakdownColumnKeys } from "../constants";

const { Link } = Typography;

interface UseConsentBreakdownTableConfig {
  stagedResource: StagedResourceAPIResponse;
  status: ConsentStatus;
}

export const useConsentBreakdownTable = ({
  stagedResource,
  status,
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
    status,
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
      getRowKey: (record: ConsentBreakdown) => record.location,
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
        render: (location: string) =>
          PRIVACY_NOTICE_REGION_RECORD[location as PrivacyNoticeRegion] ??
          location,
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
