import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { DefaultCell } from "~/features/common/table/v2";
import { StagedResourceAPIResponse } from "~/types/api";

import { DiscoveredAssetActionsCell } from "../tables/cells/DiscoveredAssetActionsCell";
import { DiscoveryStatusBadgeCell } from "../tables/cells/DiscoveryStatusBadgeCell";

export const useDiscoveredAssetsColumns = ({
  systemName,
}: {
  systemName: string;
}) => {
  const columnHelper = createColumnHelper<StagedResourceAPIResponse>();

  const columns: ColumnDef<StagedResourceAPIResponse, any>[] = [
    columnHelper.accessor((row) => row.name, {
      id: "name",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Asset",
    }),
    columnHelper.accessor((row) => row.resource_type, {
      id: "resource_type",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Type",
    }),
    columnHelper.accessor((row) => row.system, {
      id: "system",
      cell: () => <DefaultCell value={systemName} />,
      header: "System",
    }),
    columnHelper.display({
      id: "data_use",
      header: "Categories of consent",
      meta: {
        width: "auto",
      },
    }),
    columnHelper.accessor((row) => row.locations, {
      id: "locations",
      cell: (props) => (
        <DefaultCell
          value={
            props.getValue().length > 1
              ? `${props.getValue().length} locations`
              : props.getValue()[0]
          }
        />
      ),
      header: "Locations",
    }),
    columnHelper.accessor((row) => row.domain, {
      id: "domain",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Domain",
    }),
    columnHelper.accessor((row) => row.with_consent, {
      id: "with_consent",
      cell: (props) => (
        <DiscoveryStatusBadgeCell withConsent={props.getValue()} />
      ),
      header: "Discovery",
    }),
    columnHelper.display({
      id: "actions",
      cell: (props) => (
        <DiscoveredAssetActionsCell asset={props.row.original} />
      ),
      header: "Actions",
      meta: {
        width: "auto",
        disableRowClick: true,
      },
    }),
  ];
  return { columns };
};
