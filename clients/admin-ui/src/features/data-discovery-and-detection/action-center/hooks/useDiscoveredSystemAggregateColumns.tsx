import { ColumnDef, createColumnHelper } from "@tanstack/react-table";
import { useMemo } from "react";

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

interface UseDiscoveredSystemAggregateColumnsProps {
  monitorId: string;
  readonly: boolean;
  allowIgnore?: boolean;
  onTabChange: (index: number) => void;
}

export const useDiscoveredSystemAggregateColumns = ({
  monitorId,
  readonly,
  allowIgnore,
  onTabChange,
}: UseDiscoveredSystemAggregateColumnsProps) => {
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
      headerProps: {
        paddingLeft: "0px",
      },
      cellProps: {
        padding: "0 !important",
      },
    },
  });

  const totalUpdates = columnHelper.accessor((row) => row.total_updates, {
    id: "total_updates",
    cell: (props) => <DefaultCell value={props.getValue()} />,
    header: "Assets",
    size: 80,
  });

  const dataUse = columnHelper.display({
    id: "data_use",
    cell: (props) => (
      <DiscoveredSystemDataUseCell system={props.row.original} />
    ),
    header: "Categories of consent",
    size: 400,
    meta: {
      disableRowClick: true,
    },
  });

  const locations = columnHelper.accessor((row) => row.locations, {
    id: "locations",
    cell: (props) => (
      <BadgeCellExpandable
        values={props.getValue().map((location) => ({
          label: PRIVACY_NOTICE_REGION_RECORD[location as PrivacyNoticeRegion],
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
  });

  const domains = columnHelper.accessor((row) => row.domains, {
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
  });

  const actions = columnHelper.display({
    id: "actions",
    cell: (props) => (
      <DiscoveredSystemActionsCell
        system={props.row.original}
        monitorId={monitorId}
        allowIgnore={allowIgnore}
        onTabChange={onTabChange}
      />
    ),
    header: "Actions",
    meta: {
      disableRowClick: true,
    },
  });

  const readonlyColumns = useMemo(
    () => [systemName, totalUpdates, dataUse, locations, domains],
    [systemName, totalUpdates, dataUse, locations, domains],
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
