import {
  AntColumnsType as ColumnsType,
  AntSpace as Space,
  formatIsoLocation,
  isoStringToEntry,
} from "fidesui";
import { useMemo, useState } from "react";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import {
  ListExpandableCell,
  TagExpandableCell,
} from "~/features/common/table/cells";
import { expandCollapseAllMenuItems } from "~/features/common/table/cells/constants";
import {
  ConsentAlertInfo,
  PrivacyNoticeRegion,
  StagedResourceTypeValue,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";

import { VendorMatchBadge } from "../../components/VendorMatchBadge";
import { DiscoveredSystemAggregateColumnKeys } from "../constants";
import { DiscoveryStatusIcon } from "../DiscoveryStatusIcon";
import { DiscoveredSystemActionsCell } from "../tables/cells/DiscoveredSystemAggregateActionsCell";
import { DiscoveredSystemStatusCell } from "../tables/cells/DiscoveredSystemAggregateStatusCell";
import DiscoveredSystemDataUseCell from "../tables/cells/DiscoveredSystemDataUseCell";
import { OktaAppMetadata } from "../../types/OktaAppMetadata";
import { ActionCenterTabHash } from "./useActionCenterTabs";

interface UseDiscoveredSystemAggregateColumnsProps {
  monitorId: string;
  readonly: boolean;
  allowIgnore?: boolean;
  onTabChange: (tab: ActionCenterTabHash) => Promise<void>;
  consentStatus?: ConsentAlertInfo;
  rowClickUrl?: (record: SystemStagedResourcesAggregateRecord) => string;
  isOktaApp?: boolean;
  resourceType?: StagedResourceTypeValue;
}

export const useDiscoveredSystemAggregateColumns = ({
  monitorId,
  readonly,
  allowIgnore,
  onTabChange,
  consentStatus,
  rowClickUrl,
  isOktaApp = false,
  resourceType,
}: UseDiscoveredSystemAggregateColumnsProps) => {
  const [isLocationsExpanded, setIsLocationsExpanded] = useState(false);
  const [isDomainsExpanded, setIsDomainsExpanded] = useState(false);
  const [isDataUsesExpanded, setIsDataUsesExpanded] = useState(false);
  const [locationsVersion, setLocationsVersion] = useState(0);
  const [domainsVersion, setDomainsVersion] = useState(0);
  const [dataUsesVersion, setDataUsesVersion] = useState(0);
  const columns: ColumnsType<SystemStagedResourcesAggregateRecord> =
    useMemo(() => {
      // Okta-specific columns
      if (isOktaApp && resourceType === StagedResourceTypeValue.OKTA_APP) {
        return [
          {
            title: "App Name",
            dataIndex: "name",
            key: "app_name",
            fixed: "left",
            render: (_, record) => (
              <DiscoveredSystemStatusCell
                system={record}
                rowClickUrl={rowClickUrl}
              />
            ),
          },
          {
            title: "Type",
            dataIndex: "metadata",
            key: "app_type",
            render: (metadata: OktaAppMetadata) => (
              <span>{metadata?.app_type || "-"}</span>
            ),
          },
          {
            title: "Status",
            dataIndex: "metadata",
            key: "status",
            render: (metadata: OktaAppMetadata) => (
              <span>{metadata?.status || "-"}</span>
            ),
          },
          {
            title: "Vendor",
            dataIndex: "vendor_id",
            key: "vendor",
            render: (
              vendorId: string,
              record: SystemStagedResourcesAggregateRecord,
            ) => (
              <VendorMatchBadge
                vendorName={vendorId}
                vendorLogoUrl={record.metadata?.vendor_logo_url}
                confidence={record.metadata?.vendor_match_confidence}
                isUnknown={!vendorId}
              />
            ),
          },
          {
            title: "Sign-on URL",
            dataIndex: "metadata",
            key: "sign_on_url",
            render: (metadata: OktaAppMetadata) =>
              metadata?.sign_on_url ? (
                <a
                  href={metadata.sign_on_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View
                </a>
              ) : (
                <span>-</span>
              ),
          },
          {
            title: "Created",
            dataIndex: "metadata",
            key: "created",
            render: (metadata: OktaAppMetadata) => (
              <span>
                {metadata?.created
                  ? new Date(metadata.created).toLocaleDateString()
                  : "-"}
              </span>
            ),
          },
        ];
      }

      // Default system columns
      const baseColumns: ColumnsType<SystemStagedResourcesAggregateRecord> = [
        {
          title: () => (
            <Space>
              <div>System</div>
              <DiscoveryStatusIcon consentStatus={consentStatus} />
            </Space>
          ),
          dataIndex: "name",
          key: DiscoveredSystemAggregateColumnKeys.SYSTEM_NAME,
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
          key: DiscoveredSystemAggregateColumnKeys.TOTAL_UPDATES,
        },
        {
          title: "Categories of consent",
          key: DiscoveredSystemAggregateColumnKeys.DATA_USE,
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
          render: (_, record) => (
            <DiscoveredSystemDataUseCell
              system={record}
              columnState={{
                isExpanded: isDataUsesExpanded,
                version: dataUsesVersion,
              }}
            />
          ),
        },
        {
          title: "Locations",
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
          dataIndex: "locations",
          key: DiscoveredSystemAggregateColumnKeys.LOCATIONS,
          render: (locations: string[]) => (
            <TagExpandableCell
              values={
                locations?.map((location) => {
                  const isoEntry = isoStringToEntry(location);

                  return {
                    label: isoEntry
                      ? formatIsoLocation({ isoEntry })
                      : (PRIVACY_NOTICE_REGION_RECORD[
                          location as PrivacyNoticeRegion
                        ] ?? location) /* fallback on internal list for now */,
                    key: location,
                  };
                }) ?? []
              }
              columnState={{
                isExpanded: isLocationsExpanded,
                isWrapped: true,
                version: locationsVersion,
              }}
            />
          ),
        },
        {
          title: "Domains",
          menu: {
            items: expandCollapseAllMenuItems,
            onClick: (e) => {
              e.domEvent.stopPropagation();
              if (e.key === "expand-all") {
                setIsDomainsExpanded(true);
                setDomainsVersion((prev) => prev + 1);
              } else if (e.key === "collapse-all") {
                setIsDomainsExpanded(false);
                setDomainsVersion((prev) => prev + 1);
              }
            },
          },
          dataIndex: "domains",
          key: DiscoveredSystemAggregateColumnKeys.DOMAINS,
          render: (domains: string[]) => (
            <ListExpandableCell
              values={domains}
              valueSuffix="domains"
              columnState={{
                isExpanded: isDomainsExpanded,
                version: domainsVersion,
              }}
            />
          ),
        },
      ];

      if (!readonly) {
        baseColumns.push({
          title: "Actions",
          key: DiscoveredSystemAggregateColumnKeys.ACTIONS,
          fixed: "right",
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
      isDataUsesExpanded,
      isLocationsExpanded,
      isDomainsExpanded,
      dataUsesVersion,
      locationsVersion,
      domainsVersion,
      monitorId,
      allowIgnore,
      onTabChange,
      isOktaApp,
      resourceType,
    ]);

  return { columns };
};
