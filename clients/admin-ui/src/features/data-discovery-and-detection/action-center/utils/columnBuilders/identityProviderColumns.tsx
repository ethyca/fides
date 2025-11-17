import { AntColumnsType as ColumnsType } from "fidesui";

import {
  StagedResourceTypeValue,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";

import { VendorMatchBadge } from "../../../components/VendorMatchBadge";
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
      render: (metadata) => <span>{metadata ?? "-"}</span>,
    },
    {
      title: "Status",
      dataIndex: "metadata",
      key: "status",
      render: (metadata) => <span>{metadata ?? "-"}</span>,
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
      render: (metadata) =>
        metadata ? (
          <a href={metadata} target="_blank" rel="noopener noreferrer">
            View
          </a>
        ) : null,
    },
    {
      title: "Created",
      dataIndex: "metadata",
      key: "created",
      render: (metadata) => (
        <span>{metadata ? new Date(metadata).toLocaleDateString() : "N/A"}</span>
      ),
    },
  ];
