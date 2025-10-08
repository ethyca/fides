import {
  AntColumnsType as ColumnsType,
  AntTag as Tag,
  AntTooltip as Tooltip,
  AntTypography as Typography,
  formatIsoLocation,
  isoStringToEntry,
} from "fidesui";
import { useMemo } from "react";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { DEFAULT_PAGE_SIZES } from "~/features/common/table/constants";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { truncateUrl } from "~/features/common/utils";
import {
  ConsentBreakdown,
  ConsentStatus,
  PrivacyNoticeRegion,
  StagedResourceAPIResponse,
} from "~/types/api";

import { useGetConsentBreakdownQuery } from "../action-center.slice";
import {
  ConsentBreakdownColumnKeys,
  DiscoveryErrorStatuses,
  DiscoveryStatusDescriptions,
  DiscoveryStatusDisplayNames,
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
      pageQueryKey: "modalPage",
      sizeQueryKey: "modalSize",
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
          const locationText = isoEntry
            ? formatIsoLocation({ isoEntry, showFlag: true })
            : (PRIVACY_NOTICE_REGION_RECORD?.[
                location as PrivacyNoticeRegion
              ] ?? location);

          return (
            <Typography.Text ellipsis={{ tooltip: location }}>
              {locationText}
            </Typography.Text>
          );
        },
        width: 180,
      },
      {
        title: "Page",
        dataIndex: ConsentBreakdownColumnKeys.PAGE,
        key: ConsentBreakdownColumnKeys.PAGE,
        render: (page: string) => {
          const truncatedPage = truncateUrl(page, 50);
          return (
            <Link
              href={page}
              target="_blank"
              rel="noopener noreferrer"
              variant="primary"
            >
              <Typography.Text ellipsis={{ tooltip: page }} unStyled>
                {truncatedPage}
              </Typography.Text>
            </Link>
          );
        },
        minWidth: 100,
      },
      {
        title: "Compliance",
        dataIndex: ConsentBreakdownColumnKeys.STATUS,
        key: ConsentBreakdownColumnKeys.STATUS,
        width: 160,
        render: (status: ConsentStatus) => {
          const tagTooltip = DiscoveryStatusDescriptions[status];

          return (
            <Tooltip title={tagTooltip}>
              <Tag
                color="error"
                data-testid={`status-badge_${status.replace(/_/g, "-")}`}
              >
                {DiscoveryStatusDisplayNames[status]}
              </Tag>
            </Tooltip>
          );
        },
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
