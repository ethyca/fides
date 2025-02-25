import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { DefaultCell, DefaultHeaderCell } from "~/features/common/table/v2";
import { RelativeTimestampCell } from "~/features/common/table/v2/cells";
import DetectionItemActionsCell from "~/features/data-discovery-and-detection/tables/cells/DetectionItemActionsCell";
import FieldDataTypeCell from "~/features/data-discovery-and-detection/tables/cells/FieldDataTypeCell";
import ResultStatusCell from "~/features/data-discovery-and-detection/tables/cells/ResultStatusCell";
import ResultStatusBadgeCell from "~/features/data-discovery-and-detection/tables/cells/StagedResourceStatusBadgeCell";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import { StagedResourceTypeValue } from "~/types/api";

import findProjectFromUrn from "../utils/findProjectFromUrn";

const useDetectionResultColumns = ({
  resourceType,
  changeTypeOverride,
}: {
  resourceType?: StagedResourceTypeValue | undefined;
  changeTypeOverride?: ResourceChangeType;
}) => {
  const columnHelper = createColumnHelper<DiscoveryMonitorItem>();

  const defaultColumns: ColumnDef<DiscoveryMonitorItem, any>[] = [];

  if (!resourceType) {
    return { columns: defaultColumns };
  }

  if (resourceType === StagedResourceTypeValue.SCHEMA) {
    const columns = [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => (
          <ResultStatusCell
            changeTypeOverride={changeTypeOverride}
            result={props.row.original}
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
        cell: (props) => (
          <ResultStatusBadgeCell
            changeTypeOverride={changeTypeOverride}
            result={props.row.original}
          />
        ),
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
        cell: (props) => (
          <DetectionItemActionsCell
            // we don't want to show Confirm or other actions for children
            // if we're in the Monitored/Unmonitored tabs
            ignoreChildActions={
              changeTypeOverride === ResourceChangeType.MONITORED ||
              changeTypeOverride === ResourceChangeType.MUTED
            }
            resource={props.row.original}
          />
        ),
        header: "Actions",
        size: 180,
      }),
    ];
    return { columns };
  }

  if (resourceType === StagedResourceTypeValue.TABLE) {
    const columns = [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => (
          <ResultStatusCell
            changeTypeOverride={changeTypeOverride}
            result={props.row.original}
          />
        ),
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
        cell: (props) => (
          <ResultStatusBadgeCell
            changeTypeOverride={changeTypeOverride}
            result={props.row.original}
          />
        ),
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
        cell: (props) => (
          <DetectionItemActionsCell resource={props.row.original} />
        ),
        header: "Actions",
      }),
    ];
    return { columns };
  }

  if (resourceType === StagedResourceTypeValue.FIELD) {
    const columns = [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => (
          <ResultStatusCell
            changeTypeOverride={changeTypeOverride}
            result={props.row.original}
          />
        ),
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
        cell: (props) => (
          <ResultStatusBadgeCell
            changeTypeOverride={changeTypeOverride}
            result={props.row.original}
          />
        ),
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
        cell: (props) => (
          <DetectionItemActionsCell resource={props.row.original} />
        ),
        header: "Actions",
      }),
    ];
    return { columns };
  }
  return { columns: defaultColumns };
};

export default useDetectionResultColumns;
