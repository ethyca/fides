import { ColumnDef, createColumnHelper } from "@tanstack/react-table";
import { useMemo } from "react";

import {
  DefaultCell,
  IndeterminateCheckboxCell,
} from "~/features/common/table/v2";
import {
  DefaultHeaderCell,
} from "~/features/common/table/v2/cells";
import DiscoveredSystemDataUseCell from "~/features/data-discovery-and-detection/action-center/tables/cells/DiscoveredSystemDataUseCell";
import { DiscoveredSystemStatusCell } from "../tables/cells/DiscoveredSystemAggregateStatusCell";
import { DiscoveredSystemActionsCell } from "../tables/cells/DiscoveredSystemAggregateActionsCell";
import { MonitorSystemAggregate } from "../types";

interface UseDiscoveredSystemColumnsProps {
  readonly: boolean;
  monitorId?: string;
  onTabChange?: (index: number) => void;
}

export const useDiscoveredSystemColumns = ({
  readonly,
  monitorId,
  onTabChange,
}: UseDiscoveredSystemColumnsProps) => {
  const columnHelper = createColumnHelper<MonitorSystemAggregate>();

  const select = columnHelper.display({
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
      cellProps: {
        borderRight: "none",
      },
    },
  });

  const systemName = columnHelper.accessor((row) => row.name, {
    id: "system_name",
    cell: (props) => <DiscoveredSystemStatusCell system={props.row.original} />,
    header: "System",
    size: 300,
    meta: {
      headerProps: !readonly
        ? {
            paddingLeft: "0px",
          }
        : undefined,
      cellProps: !readonly
        ? {
            padding: "0 !important",
          }
        : undefined,
    },
  });

  const systemType = columnHelper.accessor((row) => row.vendor_id, {
    id: "system_type",
    cell: (props) => <DefaultCell value={props.getValue() || "Unknown"} />,
    header: "Type",
    size: 150,
  });

  const description = columnHelper.display({
    id: "description",
    cell: (props) => <DefaultCell value="No description available" />,
    header: "Description",
    size: 250,
  });

  const dataUse = columnHelper.display({
    id: "data_use",
    cell: (props) => (
      <DiscoveredSystemDataUseCell system={props.row.original} />
    ),
    header: "Data uses",
    size: 400,
    meta: {
      disableRowClick: true,
    },
  });

  const actions = columnHelper.display({
    id: "actions",
    cell: (props) => (
      <DiscoveredSystemActionsCell
        system={props.row.original}
        monitorId={monitorId || ""}
        allowIgnore={true}
        onTabChange={onTabChange || (() => {})}
      />
    ),
    header: "Actions",
    meta: {
      disableRowClick: true,
    },
  });

  const readonlyColumns = useMemo(
    () => [systemName, systemType, description, dataUse],
    [systemName, systemType, description, dataUse],
  );

  if (readonly) {
    return {
      columns: readonlyColumns,
    };
  }

  const columns: ColumnDef<MonitorSystemAggregate, any>[] = [
    select,
    ...readonlyColumns,
    actions,
  ];

  return { columns };
};
