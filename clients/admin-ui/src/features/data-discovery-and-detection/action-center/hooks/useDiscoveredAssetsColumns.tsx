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
  diffStatus,
  columnFilters,
}: {
  readonly: boolean;
  aggregatedConsent: ConsentStatus | null | undefined;
  onTabChange: (tab: ActionCenterTabHash) => void;
  onShowBreakdown?: (
    stagedResource: StagedResourceAPIResponse,
    status: ConsentStatus,
  ) => void;
  monitorConfigId: string;
  diffStatus?: DiffStatus[];
  columnFilters?: Record<string, any>;
}) => {
  const { flags } = useFeatures();
  const { assetConsentStatusLabels } = flags;

  const [isLocationsExpanded, setIsLocationsExpanded] = useState(false);
  const [isPagesExpanded, setIsPagesExpanded] = useState(false);

  const { data: filterOptions } = useGetWebsiteMonitorResourceFiltersQuery({
    monitor_config_id: monitorConfigId,
    diff_status: diffStatus,
    ...columnFilters,
  });

  const columns: ColumnsType<StagedResourceAPIResponse> = useMemo(() => {
    const baseColumns: ColumnsType<StagedResourceAPIResponse> = [
      {
        title: "Asset",
        dataIndex: "name",
        key: "name",
        render: (name) => (
          <Text ellipsis={{ tooltip: true }} style={{ maxWidth: 300 }}>
            {name}
          </Text>
        ),
        fixed: "left",
      },
      {
        title: "Type",
        dataIndex: "resource_type",
        key: "resource_type",
        filters: convertToAntFilters(filterOptions?.resource_type),
        filteredValue: columnFilters?.resource_type || null,
      },
      {
        title: "System",
        dataIndex: "system",
        key: "system",
        width: 200,
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
        key: "data_use",
        width: 400,
        filters: convertToAntFilters(filterOptions?.data_uses),
        filteredValue: columnFilters?.data_use || null,
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
                if (e.key === "expand-all") {
                  setIsLocationsExpanded(true);
                } else if (e.key === "collapse-all") {
                  setIsLocationsExpanded(false);
                }
              },
            }}
          />
        ),
        dataIndex: "locations",
        key: "locations",
        width: 250,
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
        dataIndex: "domain",
        key: "domain",
        // Domain filtering will be handled via search instead of column filters
      },
      {
        title: () => (
          <MenuHeaderCell
            title="Detected on"
            menu={{
              items: expandCollapseAllMenuItems,
              onClick: (e) => {
                if (e.key === "expand-all") {
                  setIsPagesExpanded(true);
                } else if (e.key === "collapse-all") {
                  setIsPagesExpanded(false);
                }
              },
            }}
          />
        ),
        dataIndex: "page",
        key: "page",
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
        dataIndex: "consent_aggregated",
        key: "consent_aggregated",
        filters: convertToAntFilters(
          filterOptions?.consent_aggregated,
          (status) => {
            const statusMap: Record<string, string> = {
              with_consent: "With consent",
              without_consent: "Without consent",
              exempt: "Exempt",
              unknown: "Unknown",
            };
            return statusMap[status] ?? status;
          },
        ),
        filteredValue: columnFilters?.consent_aggregated || null,
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
        key: "actions",
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
    readonly,
    assetConsentStatusLabels,
    aggregatedConsent,
    onTabChange,
    onShowBreakdown,
    isLocationsExpanded,
    isPagesExpanded,
    filterOptions,
  ]);

  return { columns };
};
