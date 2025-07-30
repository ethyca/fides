import {
  AntColumnsType as ColumnsType,
  AntSpace as Space,
  AntText as Text,
} from "fidesui";
import { useMemo, useState } from "react";

import { useFeatures } from "~/features/common/features/features.slice";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import {
  expandCollapseAllMenuItems,
  ListExpandableCell,
  MenuHeaderCell,
  TagExpandableCell,
} from "~/features/common/table/cells";
import { convertToAntFilters } from "~/features/common/utils";
import {
  AlertLevel,
  ConsentStatus,
  DiffStatus,
  PrivacyNoticeRegion,
  StagedResourceAPIResponse,
} from "~/types/api";

import { useGetWebsiteMonitorResourceFiltersQuery } from "../action-center.slice";
import {
  DiscoveredAssetsColumnKeys,
  DiscoveryStatusDisplayNames,
} from "../constants";
import { DiscoveryStatusIcon } from "../DiscoveryStatusIcon";
import { DiscoveredAssetActionsCell } from "../tables/cells/DiscoveredAssetActionsCell";
import DiscoveredAssetDataUseCell from "../tables/cells/DiscoveredAssetDataUseCell";
import { DiscoveryStatusBadgeCell } from "../tables/cells/DiscoveryStatusBadgeCell";
import { SystemCell } from "../tables/cells/SystemCell";
import { ActionCenterTabHash } from "./useActionCenterTabs";

export const useDiscoveredAssetsColumns = ({
  readonly,
  aggregatedConsent,
  onTabChange,
  onShowBreakdown,
  monitorConfigId,
  resolvedSystemId,
  diffStatus,
  columnFilters,
  sortField,
  sortOrder,
  searchQuery,
}: {
  readonly: boolean;
  aggregatedConsent: ConsentStatus | null | undefined;
  onTabChange: (tab: ActionCenterTabHash) => void;
  onShowBreakdown?: (
    stagedResource: StagedResourceAPIResponse,
    status: ConsentStatus,
  ) => void;
  monitorConfigId: string;
  resolvedSystemId: string;
  diffStatus?: DiffStatus[];
  columnFilters?: Record<string, any>;
  sortField?: string;
  sortOrder?: "ascend" | "descend";
  searchQuery?: string;
}) => {
  const { flags } = useFeatures();
  const { assetConsentStatusLabels } = flags;

  const [isLocationsExpanded, setIsLocationsExpanded] = useState(false);
  const [isPagesExpanded, setIsPagesExpanded] = useState(false);

  // if there's an error here it won't matter because the filters just won't show up
  const { data: filterOptions } = useGetWebsiteMonitorResourceFiltersQuery({
    monitor_config_id: monitorConfigId,
    resolved_system_id: resolvedSystemId,
    diff_status: diffStatus,
    search: searchQuery,
    ...columnFilters,
  });

  const columns: ColumnsType<StagedResourceAPIResponse> = useMemo(() => {
    const baseColumns: ColumnsType<StagedResourceAPIResponse> = [
      {
        title: "Asset",
        dataIndex: DiscoveredAssetsColumnKeys.NAME,
        key: DiscoveredAssetsColumnKeys.NAME,
        sorter: true,
        sortOrder:
          sortField === DiscoveredAssetsColumnKeys.NAME ? sortOrder : null,
        render: (name) => (
          <Text ellipsis={{ tooltip: true }} style={{ maxWidth: 300 }}>
            {name}
          </Text>
        ),
        fixed: "left",
      },
      {
        title: "Type",
        dataIndex: DiscoveredAssetsColumnKeys.RESOURCE_TYPE,
        key: DiscoveredAssetsColumnKeys.RESOURCE_TYPE,
        sorter: true,
        sortOrder:
          sortField === DiscoveredAssetsColumnKeys.RESOURCE_TYPE
            ? sortOrder
            : null,
        filters: convertToAntFilters(filterOptions?.resource_type),
        filteredValue: columnFilters?.resource_type || null,
      },
      {
        title: "System",
        dataIndex: DiscoveredAssetsColumnKeys.SYSTEM,
        key: DiscoveredAssetsColumnKeys.SYSTEM,
        width: 200,
        sorter: true,
        sortOrder:
          sortField === DiscoveredAssetsColumnKeys.SYSTEM ? sortOrder : null,
        render: (_, record) =>
          !!record.monitor_config_id && (
            <SystemCell
              aggregateSystem={record}
              monitorConfigId={record.monitor_config_id}
              readonly={readonly}
            />
          ),
      },
      {
        title: "Categories of consent",
        key: DiscoveredAssetsColumnKeys.DATA_USES,
        width: 400,
        filters: convertToAntFilters(filterOptions?.data_uses),
        filteredValue: columnFilters?.data_uses || null,
        sorter: true,
        sortOrder:
          sortField === DiscoveredAssetsColumnKeys.DATA_USES ? sortOrder : null,
        render: (_, record) => (
          <DiscoveredAssetDataUseCell asset={record} readonly={readonly} />
        ),
      },
      {
        title: () => (
          <MenuHeaderCell
            title="Locations"
            menu={{
              items: expandCollapseAllMenuItems,
              onClick: (e) => {
                e.domEvent.stopPropagation();
                if (e.key === "expand-all") {
                  setIsLocationsExpanded(true);
                } else if (e.key === "collapse-all") {
                  setIsLocationsExpanded(false);
                }
              },
            }}
          />
        ),
        dataIndex: DiscoveredAssetsColumnKeys.LOCATIONS,
        key: DiscoveredAssetsColumnKeys.LOCATIONS,
        width: 250,
        sorter: true,
        sortOrder:
          sortField === DiscoveredAssetsColumnKeys.LOCATIONS ? sortOrder : null,
        filters: convertToAntFilters(
          filterOptions?.locations,
          (location) =>
            PRIVACY_NOTICE_REGION_RECORD[location as PrivacyNoticeRegion] ??
            location,
        ),
        filteredValue: columnFilters?.locations || null,
        render: (locations: PrivacyNoticeRegion[]) => (
          <TagExpandableCell
            values={
              locations?.map((location) => ({
                label: PRIVACY_NOTICE_REGION_RECORD[location] ?? location,
                key: location,
              })) ?? []
            }
            columnState={{
              isExpanded: isLocationsExpanded,
              isWrapped: true,
            }}
          />
        ),
      },
      {
        title: "Domain",
        dataIndex: DiscoveredAssetsColumnKeys.DOMAIN,
        key: DiscoveredAssetsColumnKeys.DOMAIN,
        sorter: true,
        sortOrder:
          sortField === DiscoveredAssetsColumnKeys.DOMAIN ? sortOrder : null,
        // Domain filtering will be handled via search instead of column filters
      },
      {
        title: () => (
          <MenuHeaderCell
            title="Detected on"
            menu={{
              items: expandCollapseAllMenuItems,
              onClick: (e) => {
                e.domEvent.stopPropagation();
                if (e.key === "expand-all") {
                  setIsPagesExpanded(true);
                } else if (e.key === "collapse-all") {
                  setIsPagesExpanded(false);
                }
              },
            }}
          />
        ),
        dataIndex: DiscoveredAssetsColumnKeys.PAGE,
        key: DiscoveredAssetsColumnKeys.PAGE,
        sorter: true,
        sortOrder:
          sortField === DiscoveredAssetsColumnKeys.PAGE ? sortOrder : null,
        render: (pages: string[]) => (
          <ListExpandableCell
            values={pages}
            valueSuffix="pages"
            columnState={{
              isExpanded: isPagesExpanded,
            }}
          />
        ),
      },
    ];

    // Add discovery column if flag is enabled
    if (assetConsentStatusLabels) {
      baseColumns.push({
        title: () => (
          <Space>
            <div>Discovery</div>
            {aggregatedConsent === ConsentStatus.WITHOUT_CONSENT && (
              <DiscoveryStatusIcon
                consentStatus={{
                  status: AlertLevel.ALERT,
                  message: "One or more assets were detected without consent",
                }}
              />
            )}
          </Space>
        ),
        dataIndex: DiscoveredAssetsColumnKeys.CONSENT_AGGREGATED,
        key: DiscoveredAssetsColumnKeys.CONSENT_AGGREGATED,
        sorter: true,
        sortOrder:
          sortField === DiscoveredAssetsColumnKeys.CONSENT_AGGREGATED
            ? sortOrder
            : null,
        filters: convertToAntFilters(
          filterOptions?.[DiscoveredAssetsColumnKeys.CONSENT_AGGREGATED],
          (status) => {
            const statusMap: Record<string, string> = {
              with_consent: DiscoveryStatusDisplayNames.WITH_CONSENT,
              without_consent: DiscoveryStatusDisplayNames.WITHOUT_CONSENT,
              exempt: DiscoveryStatusDisplayNames.EXEMPT,
              unknown: DiscoveryStatusDisplayNames.UNKNOWN,
            };
            return statusMap[status] ?? status;
          },
        ),
        filteredValue:
          columnFilters?.[DiscoveredAssetsColumnKeys.CONSENT_AGGREGATED] ||
          null,
        render: (consentAggregated: ConsentStatus, record) => (
          <DiscoveryStatusBadgeCell
            consentAggregated={consentAggregated ?? ConsentStatus.UNKNOWN}
            stagedResource={record}
            onShowBreakdown={onShowBreakdown}
          />
        ),
      });
    }

    // Add actions column if not readonly
    if (!readonly) {
      baseColumns.push({
        title: "Actions",
        key: DiscoveredAssetsColumnKeys.ACTIONS,
        fixed: "right",
        render: (_, record) => (
          <DiscoveredAssetActionsCell
            asset={record}
            onTabChange={onTabChange}
          />
        ),
      });
    }

    return baseColumns;
  }, [
    filterOptions,
    columnFilters,
    sortField,
    sortOrder,
    assetConsentStatusLabels,
    readonly,
    isLocationsExpanded,
    isPagesExpanded,
    aggregatedConsent,
    onShowBreakdown,
    onTabChange,
  ]);

  return { columns };
};
