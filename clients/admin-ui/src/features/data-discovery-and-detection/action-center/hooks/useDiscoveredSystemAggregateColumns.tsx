import { AntColumnsType as ColumnsType, AntSpace as Space } from "fidesui";
import { useMemo, useState } from "react";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import {
  expandCollapseAllMenuItems,
  ListExpandableCell,
  MenuHeaderCell,
  TagExpandableCell,
} from "~/features/common/table/cells";
import {
  ConsentAlertInfo,
  PrivacyNoticeRegion,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";

import { DiscoveryStatusIcon } from "../DiscoveryStatusIcon";
import { DiscoveredSystemActionsCell } from "../tables/cells/DiscoveredSystemAggregateActionsCell";
import { DiscoveredSystemStatusCell } from "../tables/cells/DiscoveredSystemAggregateStatusCell";
import DiscoveredSystemDataUseCell from "../tables/cells/DiscoveredSystemDataUseCell";
import { ActionCenterTabHash } from "./useActionCenterTabs";

interface UseDiscoveredSystemAggregateColumnsProps {
  monitorId: string;
  readonly: boolean;
  allowIgnore?: boolean;
  onTabChange: (tab: ActionCenterTabHash) => void;
  consentStatus?: ConsentAlertInfo;
  rowClickUrl?: (record: SystemStagedResourcesAggregateRecord) => string;
}

export const useDiscoveredSystemAggregateColumns = ({
  monitorId,
  readonly,
  allowIgnore,
  onTabChange,
  consentStatus,
  rowClickUrl,
}: UseDiscoveredSystemAggregateColumnsProps) => {
  const [isLocationsExpanded, setIsLocationsExpanded] = useState(false);
  const [isDomainsExpanded, setIsDomainsExpanded] = useState(false);
  const columns: ColumnsType<SystemStagedResourcesAggregateRecord> =
    useMemo(() => {
      const baseColumns: ColumnsType<SystemStagedResourcesAggregateRecord> = [
        {
          title: () => (
            <Space>
              <div>System</div>
              <DiscoveryStatusIcon consentStatus={consentStatus} />
            </Space>
          ),
          dataIndex: "name",
          key: "system_name",
          fixed: "left",
          render: (_, record) => (
            <DiscoveredSystemStatusCell
              system={record}
              rowClickUrl={rowClickUrl}
            />
          ),
        },
        {
          title: "Assets",
          dataIndex: "total_updates",
          key: "total_updates",
        },
        {
          title: "Categories of consent",
          key: "data_use",
          render: (_, record) => (
            <DiscoveredSystemDataUseCell system={record} />
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
          render: (locations: string[]) => (
            <TagExpandableCell
              values={
                locations?.map((location) => ({
                  label:
                    PRIVACY_NOTICE_REGION_RECORD[
                      location as PrivacyNoticeRegion
                    ] ?? location,
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
          title: () => (
            <MenuHeaderCell
              title="Domains"
              menu={{
                items: expandCollapseAllMenuItems,
                onClick: (e) => {
                  if (e.key === "expand-all") {
                    setIsDomainsExpanded(true);
                  } else if (e.key === "collapse-all") {
                    setIsDomainsExpanded(false);
                  }
                },
              }}
            />
          ),
          dataIndex: "domains",
          key: "domains",
          render: (domains: string[]) => (
            <ListExpandableCell
              values={domains}
              valueSuffix="domains"
              columnState={{
                isExpanded: isDomainsExpanded,
              }}
            />
          ),
        },
      ];

      if (!readonly) {
        baseColumns.push({
          title: "Actions",
          key: "actions",
          render: (_, record) => (
            <DiscoveredSystemActionsCell
              system={record}
              monitorId={monitorId}
              allowIgnore={allowIgnore}
              onTabChange={onTabChange}
            />
          ),
        });
      }

      return baseColumns;
    }, [
      readonly,
      consentStatus,
      rowClickUrl,
      isLocationsExpanded,
      isDomainsExpanded,
      monitorId,
      allowIgnore,
      onTabChange,
    ]);

  return { columns };
};
