import { ColumnsType } from "fidesui";

import { NO_VALUE } from "~/constants";
import { VendorMatchBadge } from "~/features/data-discovery-and-detection/components/VendorMatchBadge";
import {
  StagedResourceTypeValue,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";
import { IdentityProviderApplicationMetadata } from "~/types/api/models/IdentityProviderApplicationMetadata";

import { DiscoveredSystemStatusCell } from "../../tables/cells/DiscoveredSystemAggregateStatusCell";
import { ColumnBuilderParams } from "./columnTypes";

export const isIdentityProvider = (
  resourceType?: StagedResourceTypeValue,
): boolean => resourceType === StagedResourceTypeValue.OKTA_APP;

export const isIdentityProviderColumns = ({
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
    render: (metadata: IdentityProviderApplicationMetadata) => (
      <span>{metadata?.app_type ?? "-"}</span>
    ),
  },
  {
    title: "Status",
    dataIndex: "metadata",
    key: "status",
    render: (metadata: IdentityProviderApplicationMetadata) => (
      <span>{metadata?.status ?? "-"}</span>
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
    render: (metadata: IdentityProviderApplicationMetadata) =>
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
    render: (metadata: IdentityProviderApplicationMetadata) => (
      <span>
        {metadata?.created
          ? new Date(metadata.created).toLocaleDateString()
          : NO_VALUE}
      </span>
    ),
  },
];
