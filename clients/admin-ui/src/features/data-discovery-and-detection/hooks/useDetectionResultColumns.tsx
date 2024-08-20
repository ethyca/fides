import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { DefaultCell, DefaultHeaderCell } from "~/features/common/table/v2";
import { RelativeTimestampCell } from "~/features/common/table/v2/cells";
import DetectionItemAction from "~/features/data-discovery-and-detection/DetectionItemActions";
import FieldDataTypeCell from "~/features/data-discovery-and-detection/tables/cells/FieldDataTypeCell";
import ResultStatusBadgeCell from "~/features/data-discovery-and-detection/tables/ResultStatusBadgeCell";
import ResultStatusCell from "~/features/data-discovery-and-detection/tables/ResultStatusCell";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";

import findProjectFromUrn from "../utils/findProjectFromUrn";

const useDetectionResultColumns = ({
  resourceType,
}: {
  resourceType?: StagedResourceType;
}) => {
  const columnHelper = createColumnHelper<DiscoveryMonitorItem>();

  const defaultColumns: ColumnDef<DiscoveryMonitorItem, any>[] = [];

  if (!resourceType) {
    return { columns: defaultColumns };
  }

  if (resourceType === StagedResourceType.SCHEMA) {
    const columns = [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <ResultStatusCell result={props.row.original} />,
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
        id: "actions",
        cell: (props) => <DetectionItemAction resource={props.row.original} />,
        header: "Actions",
      }),
    ];
    return { columns };
  }

  if (resourceType === StagedResourceType.TABLE) {
    const columns = [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <ResultStatusCell result={props.row.original} />,
        header: (props) => <DefaultHeaderCell value="Table name" {...props} />,
      }),
      columnHelper.accessor((row) => row.description, {
        id: "description",
        cell: (props) => <DefaultCell value={props.getValue() ?? "--"} />,
        header: (props) => <DefaultHeaderCell value="Description" {...props} />,
      }),
      columnHelper.display({
        id: "status",
        cell: (props) => <ResultStatusBadgeCell result={props.row.original} />,
        header: (props) => <DefaultHeaderCell value="Status" {...props} />,
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
        id: "actions",
        cell: (props) => <DetectionItemAction resource={props.row.original} />,
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
      columnHelper.accessor((row) => row.data_type, {
        id: "data-type",
        cell: (props) => <FieldDataTypeCell type={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Data type" {...props} />,
      }),
      columnHelper.accessor((row) => row.description, {
        id: "description",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Description" {...props} />,
      }),
      columnHelper.display({
        id: "status",
        cell: (props) => <ResultStatusBadgeCell result={props.row.original} />,
        header: (props) => <DefaultHeaderCell value="Status" {...props} />,
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
        id: "actions",
        cell: (props) => <DetectionItemAction resource={props.row.original} />,
        header: "Actions",
      }),
    ];
    return { columns };
  }
  return { columns: defaultColumns };
};

export default useDetectionResultColumns;
