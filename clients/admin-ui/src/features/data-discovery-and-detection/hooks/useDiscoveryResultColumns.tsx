import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { DefaultCell, DefaultHeaderCell } from "~/features/common/table/v2";
import {
  IndeterminateCheckboxCell,
  RelativeTimestampCell,
} from "~/features/common/table/v2/cells";
import ResultStatusBadgeCell from "~/features/data-discovery-and-detection/tables/ResultStatusBadgeCell";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";
import findProjectFromUrn from "~/features/data-discovery-and-detection/utils/findProjectFromUrn";
import { DiffStatus } from "~/types/api";

import DiscoveryItemActions from "../DiscoveryItemActions";
import ResultStatusCell from "../tables/ResultStatusCell";
import TaxonomyDisplayAndEdit from "../TaxonomyDisplayAndEdit";
import findActivityType from "../utils/getResourceActivityLabel";

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
      columnHelper.accessor((resource) => findActivityType(resource), {
        id: "type",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Type" {...props} />,
      }),
      columnHelper.accessor((row) => row.monitor_config_id, {
        id: "monitor",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Detected by" {...props} />,
      }),
      columnHelper.accessor((row) => row.source_modified, {
        id: "time",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="When" {...props} />,
      }),
      columnHelper.display({
        id: "action",
        cell: (props) =>
          props.row.original.diff_status === DiffStatus.MONITORED ? (
            <DiscoveryItemActions resource={props.row.original} />
          ) : (
            <DefaultCell value="--" />
          ),
        header: "Actions",
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
      columnHelper.accessor((row) => row.source_modified, {
        id: "time",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: "Time",
      }),
      columnHelper.display({
        id: "actions",
        cell: (props) => <DiscoveryItemActions resource={props.row.original} />,
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
          return <TaxonomyDisplayAndEdit resource={row.original} />;
        },
        meta: { overflow: "visible" },
        header: "Data category",
        minSize: 280, // keep a minimum width so the Select has space to display the options properly
      }),
      columnHelper.accessor((row) => row.source_modified, {
        id: "time",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="When" {...props} />,
      }),
      columnHelper.display({
        id: "actions",
        cell: (props) => <DiscoveryItemActions resource={props.row.original} />,
        header: "Actions",
      }),
    ];
    return { columns };
  }

  return { columns: defaultColumns };
};

export default useDiscoveryResultColumns;
