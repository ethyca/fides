import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { DefaultCell, DefaultHeaderCell } from "~/features/common/table/v2";
import {
  IndeterminateCheckboxCell,
  RelativeTimestampCell,
} from "~/features/common/table/v2/cells";
import FieldDataTypeCell from "~/features/data-discovery-and-detection/tables/cells/FieldDataTypeCell";
import ResultStatusBadgeCell from "~/features/data-discovery-and-detection/tables/cells/ResultStatusBadgeCell";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";
import findProjectFromUrn from "~/features/data-discovery-and-detection/utils/findProjectFromUrn";
import { DiffStatus } from "~/types/api";

import DiscoveryItemActionsCell from "../tables/cells/DiscoveryItemActionsCell";
import EditCategoriesCell from "../tables/cells/EditCategoryCell";
import ResultStatusCell from "../tables/cells/ResultStatusCell";

const useDiscoveryResultColumns = ({
  resourceType,
}: {
  resourceType: StagedResourceType | undefined;
}) => {
  const columnHelper = createColumnHelper<DiscoveryMonitorItem>();

  const defaultColumns: ColumnDef<DiscoveryMonitorItem, any>[] = [];

  if (resourceType === StagedResourceType.SCHEMA) {
    const columns = [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => (
          <ResultStatusCell
            result={props.row.original}
            changeTypeOverride={ResourceChangeType.CLASSIFICATION}
          />
        ),
        header: (props) => <DefaultHeaderCell value="Name" {...props} />,
      }),
      columnHelper.accessor((row) => row.urn, {
        id: "project",
        cell: (props) => (
          <DefaultCell value={findProjectFromUrn(props.getValue())} />
        ),
        header: (props) => <DefaultHeaderCell value="Project" {...props} />,
      }),
      columnHelper.display({
        id: "status",
        cell: (props) => <ResultStatusBadgeCell result={props.row.original} />,
        header: (props) => <DefaultHeaderCell value="Status" {...props} />,
      }),
      columnHelper.accessor((row) => row.system, {
        id: "system",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="System" {...props} />,
      }),
      columnHelper.accessor((row) => row.monitor_config_id, {
        id: "monitor",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Detected by" {...props} />,
      }),
      columnHelper.accessor((row) => row.updated_at, {
        id: "time",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="When" {...props} />,
      }),
      columnHelper.display({
        id: "action",
        cell: (props) =>
          props.row.original.diff_status !== DiffStatus.MUTED ? (
            <DiscoveryItemActionsCell resource={props.row.original} />
          ) : (
            <DefaultCell value="--" />
          ),
        header: "Actions",
        size: 180,
      }),
    ];
    return { columns };
  }

  if (resourceType === StagedResourceType.TABLE) {
    const columns = [
      columnHelper.display({
        id: "select",
        cell: ({ row }) => (
          <IndeterminateCheckboxCell
            isChecked={row.getIsSelected()}
            onChange={row.getToggleSelectedHandler()}
            dataTestId={`select-${row.original.name ?? row.id}`}
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
      }),
      columnHelper.accessor((row) => row.name, {
        id: "tables",
        cell: (props) => <ResultStatusCell result={props.row.original} />,
        header: (props) => <DefaultHeaderCell value="Table name" {...props} />,
      }),
      columnHelper.accessor((row) => row.description, {
        id: "description",
        cell: (props) => (
          <DefaultCell value={props.getValue()} cellProps={props} />
        ),
        header: (props) => <DefaultHeaderCell value="Description" {...props} />,
        meta: {
          showHeaderMenu: true,
        },
      }),
      columnHelper.display({
        id: "status",
        cell: (props) => <ResultStatusBadgeCell result={props.row.original} />,
        header: (props) => <DefaultHeaderCell value="Status" {...props} />,
      }),
      columnHelper.display({
        id: "type",
        cell: () => <DefaultCell value="Table" />,
        header: "Type",
      }),
      columnHelper.accessor((row) => row.updated_at, {
        id: "time",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: "Time",
      }),
      columnHelper.display({
        id: "actions",
        cell: (props) => (
          <DiscoveryItemActionsCell resource={props.row.original} />
        ),
        header: "Actions",
      }),
    ];
    return { columns };
  }

  if (resourceType === StagedResourceType.FIELD) {
    const columns = [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <ResultStatusCell result={props.row.original} />,
        header: (props) => <DefaultHeaderCell value="Field name" {...props} />,
      }),
      columnHelper.accessor((row) => row.source_data_type, {
        id: "data-type",
        cell: (props) => <FieldDataTypeCell type={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Data type" {...props} />,
      }),
      columnHelper.accessor((row) => row.description, {
        id: "description",
        cell: (props) => (
          <DefaultCell value={props.getValue()} cellProps={props} />
        ),
        header: (props) => <DefaultHeaderCell value="Description" {...props} />,
        meta: {
          showHeaderMenu: true,
        },
      }),
      columnHelper.display({
        id: "status",
        cell: (props) => <ResultStatusBadgeCell result={props.row.original} />,
        header: (props) => <DefaultHeaderCell value="Status" {...props} />,
      }),
      columnHelper.display({
        id: "type",
        cell: () => <DefaultCell value="Field" />,
        header: "Type",
      }),
      columnHelper.display({
        id: "classifications",
        cell: ({ row }) => {
          return <EditCategoriesCell resource={row.original} />;
        },
        meta: { overflow: "visible", disableRowClick: true },
        header: "Data category",
        minSize: 280, // keep a minimum width so the Select has space to display the options properly
      }),
      columnHelper.accessor((row) => row.updated_at, {
        id: "time",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="When" {...props} />,
      }),
      columnHelper.display({
        id: "actions",
        cell: (props) => (
          <DiscoveryItemActionsCell resource={props.row.original} />
        ),
        header: "Actions",
      }),
    ];
    return { columns };
  }

  return { columns: defaultColumns };
};

export default useDiscoveryResultColumns;
