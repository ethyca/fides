import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { DefaultCell } from "~/features/common/table/v2";
import { StagedResourceAPIResponse } from "~/types/api";

export const useDiscoveredAssetsColumns = () => {
  const columnHelper = createColumnHelper<StagedResourceAPIResponse>();

  const columns: ColumnDef<StagedResourceAPIResponse, any>[] = [
    /*
    // TODO: [HJ-354] uncomment when actions are implemented
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
      maxSize: 25,
    }), */
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
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "System",
      meta: {
        width: "auto",
      },
    }),
    /*
    // TODO: [HJ-369] uncomment when monitor supports categories of consent
    columnHelper.display({
      id: "data_use",
      header: "Categories of consent",
      meta: {
        width: "auto",
      },
    }), */
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
    /*
    // TODO: [HJ-354] uncomment when actions are implemented
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
    }), */
  ];
  return { columns };
};
