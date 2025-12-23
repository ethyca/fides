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
import {
  PrivacyNoticeRegion,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";

import { DiscoveredSystemAggregateColumnKeys } from "../../constants";
import { DiscoveryStatusIcon } from "../../DiscoveryStatusIcon";
import { DiscoveredSystemActionsCell } from "../../tables/cells/DiscoveredSystemAggregateActionsCell";
import { DiscoveredSystemStatusCell } from "../../tables/cells/DiscoveredSystemAggregateStatusCell";
import DiscoveredSystemDataUseCell from "../../tables/cells/DiscoveredSystemDataUseCell";
import { buildExpandCollapseMenu } from "./columnHelpers";
import { ColumnBuilderParams } from "./columnTypes";

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
    width: 100,
  },
  {
    title: "Categories of consent",
    key: DiscoveredSystemAggregateColumnKeys.DATA_USE,
    menu: buildExpandCollapseMenu(setIsDataUsesExpanded, setDataUsesVersion),
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
    menu: buildExpandCollapseMenu(setIsLocationsExpanded, setLocationsVersion),
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
    menu: buildExpandCollapseMenu(setIsDomainsExpanded, setDomainsVersion),
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
