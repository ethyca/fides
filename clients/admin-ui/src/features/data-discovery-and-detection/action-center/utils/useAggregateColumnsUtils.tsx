import {
  AntColumnsType as ColumnsType,
  AntSpace as Space,
  formatIsoLocation,
  isoStringToEntry,
} from "fidesui";

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
import { OktaAppMetadata } from "../../types/OktaAppMetadata";
import { DiscoveredSystemAggregateColumnKeys } from "../constants";
import { DiscoveryStatusIcon } from "../DiscoveryStatusIcon";
import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";
import { DiscoveredSystemActionsCell } from "../tables/cells/DiscoveredSystemAggregateActionsCell";
import { DiscoveredSystemStatusCell } from "../tables/cells/DiscoveredSystemAggregateStatusCell";
import DiscoveredSystemDataUseCell from "../tables/cells/DiscoveredSystemDataUseCell";

export interface ColumnBuilderParams {
  monitorId: string;
  readonly: boolean;
  allowIgnore?: boolean;
  onTabChange: (tab: ActionCenterTabHash) => Promise<void>;
  consentStatus?: ConsentAlertInfo;
  rowClickUrl?: (record: SystemStagedResourcesAggregateRecord) => string;
  isDataUsesExpanded: boolean;
  isLocationsExpanded: boolean;
  isDomainsExpanded: boolean;
  dataUsesVersion: number;
  locationsVersion: number;
  domainsVersion: number;
  setIsDataUsesExpanded: (value: boolean) => void;
  setIsLocationsExpanded: (value: boolean) => void;
  setIsDomainsExpanded: (value: boolean) => void;
  setDataUsesVersion: (fn: (prev: number) => number) => void;
  setLocationsVersion: (fn: (prev: number) => number) => void;
  setDomainsVersion: (fn: (prev: number) => number) => void;
}

export const isIDP = (resourceType?: StagedResourceTypeValue): boolean =>
  resourceType === StagedResourceTypeValue.OKTA_APP;

export const buildIdpColumns = ({
  rowClickUrl,
}: Pick<
  ColumnBuilderParams,
  "rowClickUrl"
>): ColumnsType<SystemStagedResourcesAggregateRecord> => [
  {
    title: "App Name",
    dataIndex: "name",
    key: "app_name",
    fixed: "left",
    render: (_, record) => (
      <DiscoveredSystemStatusCell system={record} rowClickUrl={rowClickUrl} />
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
      ) : null,
  },
  {
    title: "Created",
    dataIndex: "metadata",
    key: "created",
    render: (metadata: OktaAppMetadata) => (
      <span>
        {metadata?.created
          ? new Date(metadata.created).toLocaleDateString()
          : "N/A"}
      </span>
    ),
  },
];

const buildBaseColumns = ({
  consentStatus,
  rowClickUrl,
  isDataUsesExpanded,
  isLocationsExpanded,
  isDomainsExpanded,
  dataUsesVersion,
  locationsVersion,
  domainsVersion,
  setIsDataUsesExpanded,
  setIsLocationsExpanded,
  setIsDomainsExpanded,
  setDataUsesVersion,
  setLocationsVersion,
  setDomainsVersion,
}: Omit<
  ColumnBuilderParams,
  "monitorId" | "readonly" | "allowIgnore" | "onTabChange"
>): ColumnsType<SystemStagedResourcesAggregateRecord> => [
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
      <DiscoveredSystemStatusCell system={record} rowClickUrl={rowClickUrl} />
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

export const buildReadOnlyColumns = (
  params: ColumnBuilderParams,
): ColumnsType<SystemStagedResourcesAggregateRecord> =>
  buildBaseColumns(params);

export const buildEditableColumns = (
  params: ColumnBuilderParams,
): ColumnsType<SystemStagedResourcesAggregateRecord> => {
  const baseColumns = buildBaseColumns(params);
  return [
    ...baseColumns,
    {
      title: "Actions",
      key: DiscoveredSystemAggregateColumnKeys.ACTIONS,
      fixed: "right",
      render: (_, record) => (
        <DiscoveredSystemActionsCell
          system={record}
          monitorId={params.monitorId}
          allowIgnore={params.allowIgnore}
          onTabChange={params.onTabChange}
        />
      ),
    },
  ];
};
