import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { DefaultCell } from "~/features/common/table/v2";
import DiscoveredSystemDataUseCell from "~/features/data-discovery-and-detection/action-center/tables/cells/DiscoveredSystemDataUseCell";

import { DiscoveredSystemActionsCell } from "../tables/cells/DiscoveredSystemAggregateActionsCell";
import { DiscoveredSystemStatusCell } from "../tables/cells/DiscoveredSystemAggregateStatusCell";
import { MonitorSystemAggregate } from "../types";

export const useDiscoveredSystemAggregateColumns = (monitorId: string) => {
  const columnHelper = createColumnHelper<MonitorSystemAggregate>();

  const columns: ColumnDef<MonitorSystemAggregate, any>[] = [
    columnHelper.accessor((row) => row.name, {
      id: "system_name",
      cell: (props) => (
        <DiscoveredSystemStatusCell system={props.row.original} />
      ),
      header: "System",
      meta: {
        width: "auto",
      },
    }),
    columnHelper.accessor((row) => row.total_updates, {
      id: "total_updates",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: "Assets",
      size: 80,
    }),
    columnHelper.display({
      id: "data_use",
      cell: (props) => (
        <DiscoveredSystemDataUseCell system={props.row.original} />
      ),
      header: "Categories of consent",
      meta: {
        width: "auto",
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
    columnHelper.accessor((row) => row.domains, {
      id: "domains",
      cell: (props) => (
        <DefaultCell
          value={
            props.getValue().length > 1
              ? `${props.getValue().length} domains`
              : props.getValue()[0]
          }
        />
      ),
      header: "Domains",
    }),
    columnHelper.display({
      id: "actions",
      cell: (props) => (
        <DiscoveredSystemActionsCell
          system={props.row.original}
          monitorId={monitorId}
        />
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
