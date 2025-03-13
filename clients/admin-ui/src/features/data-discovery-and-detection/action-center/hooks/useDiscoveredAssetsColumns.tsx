import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import {
  DefaultCell,
  IndeterminateCheckboxCell,
} from "~/features/common/table/v2";
import {
  DefaultHeaderCell,
  ListCellExpandable,
} from "~/features/common/table/v2/cells";
import { DiscoveredAssetActionsCell } from "~/features/data-discovery-and-detection/action-center/tables/cells/DiscoveredAssetActionsCell";
import DiscoveredAssetDataUseCell from "~/features/data-discovery-and-detection/action-center/tables/cells/DiscoveredAssetDataUseCell";
import { StagedResourceAPIResponse } from "~/types/api";

import { SystemCell } from "../tables/cells/SystemCell";

export const useDiscoveredAssetsColumns = () => {
  const columnHelper = createColumnHelper<StagedResourceAPIResponse>();

  const columns: ColumnDef<StagedResourceAPIResponse, any>[] = [
    columnHelper.display({
      id: "select",
      cell: ({ row }) => (
        <IndeterminateCheckboxCell
          isChecked={row.getIsSelected()}
          onChange={row.getToggleSelectedHandler()}
          dataTestId={`select-${row.original.name || row.id}`}
        />
      ),
      header: ({ table }) => (
        <IndeterminateCheckboxCell
          isChecked={table.getIsAllPageRowsSelected()}
          isIndeterminate={table.getIsSomeRowsSelected()}
          onChange={table.getToggleAllRowsSelectedHandler()}
          dataTestId="select-all-rows"
        />
      ),
      maxSize: 40,
    }),
    columnHelper.accessor((row) => row.name, {
      id: "name",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Asset",
      size: 300,
    }),
    columnHelper.accessor((row) => row.resource_type, {
      id: "resource_type",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Type",
    }),
    columnHelper.accessor((row) => row.system, {
      id: "system",
      cell: (props) =>
        !!props.row.original.monitor_config_id && (
          <SystemCell
            aggregateSystem={props.row.original}
            monitorConfigId={props.row.original.monitor_config_id}
          />
        ),
      header: "System",
      size: 200,
      meta: {
        noPadding: true,
      },
    }),
    columnHelper.display({
      id: "data_use",
      cell: (props) => (
        <DiscoveredAssetDataUseCell asset={props.row.original} />
      ),
      header: "Categories of consent",
      size: 400,
      meta: {
        disableRowClick: true,
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
    /*
    // TODO: [HJ-344] uncomment when monitor supports discovery status
    columnHelper.accessor((row) => row.with_consent, {
      id: "with_consent",
      cell: (props) => (
        <DiscoveryStatusBadgeCell
          withConsent={props.getValue()}
          dateDiscovered={props.row.original.updated_at}
        />
      ),
      header: "Discovery",
    }), */
    columnHelper.accessor((row) => row.page, {
      id: "page",
      cell: (props) => (
        <ListCellExpandable
          values={props.getValue()}
          valueSuffix="pages"
          cellProps={props}
        />
      ),
      header: (props) => <DefaultHeaderCell value="Detected on" {...props} />,
      meta: {
        showHeaderMenu: true,
      },
    }),
    columnHelper.display({
      id: "actions",
      cell: (props) => (
        <DiscoveredAssetActionsCell asset={props.row.original} />
      ),
      header: "Actions",
      meta: {
        disableRowClick: true,
      },
    }),
  ];
  return { columns };
};
