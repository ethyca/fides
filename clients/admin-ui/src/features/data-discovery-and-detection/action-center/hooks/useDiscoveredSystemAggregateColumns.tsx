import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import {
  DefaultCell,
  IndeterminateCheckboxCell,
} from "~/features/common/table/v2";
import {
  BadgeCellExpandable,
  ListCellExpandable,
} from "~/features/common/table/v2/cells";
import DiscoveredSystemDataUseCell from "~/features/data-discovery-and-detection/action-center/tables/cells/DiscoveredSystemDataUseCell";
import { PrivacyNoticeRegion } from "~/types/api";

import { DiscoveredSystemActionsCell } from "../tables/cells/DiscoveredSystemAggregateActionsCell";
import { DiscoveredSystemStatusCell } from "../tables/cells/DiscoveredSystemAggregateStatusCell";
import { MonitorSystemAggregate } from "../types";

export const useDiscoveredSystemAggregateColumns = (monitorId: string) => {
  const columnHelper = createColumnHelper<MonitorSystemAggregate>();

  const columns: ColumnDef<MonitorSystemAggregate, any>[] = [
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
      meta: {
        disableRowClick: true,
      },
    }),
    columnHelper.accessor((row) => row.name, {
      id: "system_name",
      cell: (props) => (
        <DiscoveredSystemStatusCell system={props.row.original} />
      ),
      header: "System",
      size: 300,
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
      size: 400,
      meta: {
        disableRowClick: true,
      },
    }),
    columnHelper.accessor((row) => row.locations, {
      id: "locations",
      cell: (props) => (
        <BadgeCellExpandable
          values={props.getValue().map((location: PrivacyNoticeRegion) => ({
            label: PRIVACY_NOTICE_REGION_RECORD[location],
            key: location,
          }))}
        />
      ),
      header: "Locations",
      size: 300,
      meta: {
        showHeaderMenu: true,
        disableRowClick: true,
      },
    }),
    columnHelper.accessor((row) => row.domains, {
      id: "domains",
      cell: (props) => (
        <ListCellExpandable
          values={props.getValue()}
          valueSuffix="domains"
          cellProps={props}
        />
      ),
      header: "Domains",
      meta: {
        showHeaderMenu: true,
        disableRowClick: true,
      },
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
        disableRowClick: true,
      },
    }),
  ];

  return { columns };
};
