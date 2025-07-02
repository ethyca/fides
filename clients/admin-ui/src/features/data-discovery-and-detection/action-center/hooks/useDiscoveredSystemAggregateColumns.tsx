import { createColumnHelper } from "@tanstack/react-table";
import { useMemo } from "react";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import {
  DefaultCell,
  IndeterminateCheckboxCell,
} from "~/features/common/table/v2";
import {
  BadgeCellExpandable,
  DefaultHeaderCell,
  ListCellExpandable,
} from "~/features/common/table/v2/cells";
import DiscoveredSystemDataUseCell from "~/features/data-discovery-and-detection/action-center/tables/cells/DiscoveredSystemDataUseCell";
import { ActionCenterTabHash } from "~/features/data-discovery-and-detection/action-center/tables/useActionCenterTabs";
import {
  PrivacyNoticeRegion,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";

import { DiscoveredSystemActionsCell } from "../tables/cells/DiscoveredSystemAggregateActionsCell";
import { DiscoveredSystemStatusCell } from "../tables/cells/DiscoveredSystemAggregateStatusCell";

interface UseDiscoveredSystemAggregateColumnsProps {
  monitorId: string;
  readonly: boolean;
  allowIgnore?: boolean;
  onTabChange: (tab: ActionCenterTabHash) => void;
}

export const useDiscoveredSystemAggregateColumns = ({
  monitorId,
  readonly,
  allowIgnore,
  onTabChange,
}: UseDiscoveredSystemAggregateColumnsProps) => {
  const columnHelper =
    createColumnHelper<SystemStagedResourcesAggregateRecord>();

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
        values={
          props.getValue()?.map((location) => ({
            label:
              PRIVACY_NOTICE_REGION_RECORD[location as PrivacyNoticeRegion],
            key: location,
          })) ?? []
        }
      />
    ),
    header: (props) => <DefaultHeaderCell value="Locations" {...props} />,
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
    header: (props) => <DefaultHeaderCell value="Domains" {...props} />,
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

  const readonlyColumns = [
    systemName,
    totalUpdates,
    dataUse,
    locations,
    domains,
  ];

  const allColumns = [select, ...readonlyColumns, actions];

  const columns = useMemo(
    () => (readonly ? readonlyColumns : allColumns),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [readonly],
  );

  return { columns };
};
