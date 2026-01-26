import {
  ColumnsType,
  formatIsoLocation,
  isoStringToEntry,
  Tag,
  Text,
} from "fidesui";
import { useMemo, useState } from "react";

import { useFeatures } from "~/features/common/features/features.slice";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { TagExpandableCell } from "~/features/common/table/cells";
import { expandCollapseAllMenuItems } from "~/features/common/table/cells/constants";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { convertToAntFilters } from "~/features/common/utils";
import { Asset, ConsentStatus, PrivacyNoticeRegion } from "~/types/api";

import type { AssetReportingFilters } from "../asset-reporting.slice";
import {
  useGetAllAssetsQuery,
  useGetAssetReportingFilterOptionsQuery,
} from "../asset-reporting.slice";

enum AssetReportingColumnKeys {
  NAME = "name",
  ASSET_TYPE = "asset_type",
  SYSTEM_NAME = "system_name",
  CONSENT_STATUS = "consent_status",
  DATA_USES = "data_uses",
  DOMAIN = "domain",
  LOCATIONS = "locations",
}

const CONSENT_STATUS_COLORS: Record<
  ConsentStatus,
  "success" | "error" | "warning" | "default" | "caution" | undefined
> = {
  [ConsentStatus.WITH_CONSENT]: "success",
  [ConsentStatus.WITHOUT_CONSENT]: "error",
  [ConsentStatus.PRE_CONSENT]: "warning",
  [ConsentStatus.EXEMPT]: "default",
  [ConsentStatus.NOT_APPLICABLE]: undefined,
  [ConsentStatus.UNKNOWN]: "caution",
  [ConsentStatus.CMP_ERROR]: "error",
};

const CONSENT_STATUS_LABELS: Record<ConsentStatus, string> = {
  [ConsentStatus.WITH_CONSENT]: "With consent",
  [ConsentStatus.WITHOUT_CONSENT]: "Without consent",
  [ConsentStatus.PRE_CONSENT]: "Pre-consent",
  [ConsentStatus.EXEMPT]: "Exempt",
  [ConsentStatus.NOT_APPLICABLE]: "Not applicable",
  [ConsentStatus.UNKNOWN]: "Unknown",
  [ConsentStatus.CMP_ERROR]: "CMP error",
};

interface UseAssetReportingTableConfig {
  filters: AssetReportingFilters;
}

export const useAssetReportingTable = ({
  filters,
}: UseAssetReportingTableConfig) => {
  const { flags } = useFeatures();
  const { assetConsentStatusLabels } = flags;
  const { getDataUseByKey, getDataUseDisplayName } = useTaxonomies();

  const [isDataUsesExpanded, setIsDataUsesExpanded] = useState(false);
  const [dataUsesVersion, setDataUsesVersion] = useState(0);
  const [isLocationsExpanded, setIsLocationsExpanded] = useState(false);
  const [locationsVersion, setLocationsVersion] = useState(0);

  const tableState = useTableState<AssetReportingColumnKeys>({
    sorting: {
      validColumns: Object.values(AssetReportingColumnKeys),
    },
  });

  const {
    columnFilters,
    pageIndex,
    pageSize,
    sortKey,
    sortOrder,
    searchQuery,
    updateSearch,
    updateFilters,
    updateSorting,
    updatePageIndex,
    updatePageSize,
    resetState,
  } = tableState;

  const { data, isLoading, isFetching } = useGetAllAssetsQuery({
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
    ...filters,
    ...columnFilters,
  });

  // Fetch dynamic filter options based on current filters
  const { data: filterOptions } = useGetAssetReportingFilterOptionsQuery({
    search: searchQuery,
    ...filters,
    ...columnFilters,
  });

  const columns: ColumnsType<Asset> = useMemo(() => {
    const baseColumns: ColumnsType<Asset> = [
      {
        title: "Asset name",
        dataIndex: AssetReportingColumnKeys.NAME,
        key: AssetReportingColumnKeys.NAME,
        width: 200,
        render: (value: string) => (
          <Text ellipsis={{ tooltip: true }} style={{ maxWidth: 300 }}>
            {value}
          </Text>
        ),
        fixed: "left",
        sorter: true,
        sortOrder: sortKey === AssetReportingColumnKeys.NAME ? sortOrder : null,
      },
      {
        title: "Type",
        dataIndex: AssetReportingColumnKeys.ASSET_TYPE,
        key: AssetReportingColumnKeys.ASSET_TYPE,
        width: 150,
        sorter: true,
        sortOrder:
          sortKey === AssetReportingColumnKeys.ASSET_TYPE ? sortOrder : null,
        filters: convertToAntFilters(filterOptions?.asset_type),
        filteredValue: columnFilters?.asset_type || null,
      },
      {
        title: "System",
        dataIndex: AssetReportingColumnKeys.SYSTEM_NAME,
        key: AssetReportingColumnKeys.SYSTEM_NAME,
        width: 180,
        render: (value: string) => (
          <Text ellipsis={{ tooltip: true }} style={{ maxWidth: 250 }}>
            {value || "N/A"}
          </Text>
        ),
        sorter: true,
        sortOrder:
          sortKey === AssetReportingColumnKeys.SYSTEM_NAME ? sortOrder : null,
      },
    ];

    // Add consent status column if flag is enabled
    if (assetConsentStatusLabels) {
      baseColumns.push({
        title: "Consent status",
        dataIndex: AssetReportingColumnKeys.CONSENT_STATUS,
        key: AssetReportingColumnKeys.CONSENT_STATUS,
        width: 160,
        render: (status: ConsentStatus) =>
          status ? (
            <Tag color={CONSENT_STATUS_COLORS[status]}>
              {CONSENT_STATUS_LABELS[status]}
            </Tag>
          ) : (
            "N/A"
          ),
        sorter: true,
        sortOrder:
          sortKey === AssetReportingColumnKeys.CONSENT_STATUS
            ? sortOrder
            : null,
        filters: convertToAntFilters(
          filterOptions?.consent_status,
          (status) => CONSENT_STATUS_LABELS[status as ConsentStatus] || status,
        ),
        filteredValue: columnFilters?.consent_status || null,
      });
    }

    // Add remaining columns
    baseColumns.push(
      {
        title: "Categories of consent",
        key: AssetReportingColumnKeys.DATA_USES,
        menu: {
          items: expandCollapseAllMenuItems,
          onClick: (e) => {
            e.domEvent.stopPropagation();
            if (e.key === "expand-all") {
              setIsDataUsesExpanded(true);
              setDataUsesVersion((prev) => prev + 1);
            } else if (e.key === "collapse-all") {
              setIsDataUsesExpanded(false);
              setDataUsesVersion((prev) => prev + 1);
            }
          },
        },
        filters: convertToAntFilters(
          filterOptions?.data_uses,
          (key) => getDataUseByKey(key)?.name || key,
        ),
        filteredValue: columnFilters?.data_uses || null,
        render: (_, record: Asset) => (
          <TagExpandableCell
            values={record.data_uses?.map((d) => ({
              label: getDataUseDisplayName(d),
              key: d,
            }))}
            columnState={{
              isExpanded: isDataUsesExpanded,
              version: dataUsesVersion,
            }}
          />
        ),
        width: 200,
      },
      {
        title: "Domain",
        dataIndex: AssetReportingColumnKeys.DOMAIN,
        key: AssetReportingColumnKeys.DOMAIN,
        width: 180,
        render: (value: string) => (
          <Text ellipsis={{ tooltip: true }} style={{ maxWidth: 250 }}>
            {value || "N/A"}
          </Text>
        ),
      },
      {
        title: "Locations",
        dataIndex: AssetReportingColumnKeys.LOCATIONS,
        key: AssetReportingColumnKeys.LOCATIONS,
        menu: {
          items: expandCollapseAllMenuItems,
          onClick: (e) => {
            e.domEvent.stopPropagation();
            if (e.key === "expand-all") {
              setIsLocationsExpanded(true);
              setLocationsVersion((prev) => prev + 1);
            } else if (e.key === "collapse-all") {
              setIsLocationsExpanded(false);
              setLocationsVersion((prev) => prev + 1);
            }
          },
        },
        filters: convertToAntFilters(filterOptions?.locations, (location) => {
          const isoEntry = isoStringToEntry(location);
          return isoEntry
            ? formatIsoLocation({ isoEntry })
            : (PRIVACY_NOTICE_REGION_RECORD[location as PrivacyNoticeRegion] ??
                location);
        }),
        filteredValue: columnFilters?.locations || null,
        render: (locations: PrivacyNoticeRegion[]) => (
          <TagExpandableCell
            values={
              locations?.map((location) => {
                const isoEntry = isoStringToEntry(location);
                return {
                  label: isoEntry
                    ? formatIsoLocation({ isoEntry })
                    : (PRIVACY_NOTICE_REGION_RECORD[location] ?? location),
                  key: location,
                };
              }) ?? []
            }
            columnState={{
              isExpanded: isLocationsExpanded,
              version: locationsVersion,
            }}
          />
        ),
      },
    );

    return baseColumns;
  }, [
    sortKey,
    sortOrder,
    columnFilters,
    filterOptions,
    assetConsentStatusLabels,
    isDataUsesExpanded,
    dataUsesVersion,
    getDataUseByKey,
    getDataUseDisplayName,
    isLocationsExpanded,
    locationsVersion,
  ]);

  const antTableConfig = useMemo(
    () => ({
      enableSelection: false,
      getRowKey: (record: Asset) => record.id,
      isLoading,
      isFetching,
      dataSource: data?.items || [],
      totalRows: data?.total || 0,
      customTableProps: {
        sticky: {
          offsetHeader: 40,
          offsetScroll: 0,
        },
      },
    }),
    [isLoading, isFetching, data?.items, data?.total],
  );

  const antTable = useAntTable<Asset, AssetReportingColumnKeys>(
    tableState,
    antTableConfig,
  );

  return {
    columns,
    data,
    isLoading,
    isFetching,
    searchQuery,
    updateSearch,
    updateFilters,
    updateSorting,
    updatePageIndex,
    updatePageSize,
    resetState,
    columnFilters,
    tableProps: antTable.tableProps,
    selectionProps: antTable.selectionProps,
  };
};
