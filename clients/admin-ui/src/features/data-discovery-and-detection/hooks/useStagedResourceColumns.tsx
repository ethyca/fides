import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { DefaultCell, DefaultHeaderCell } from "~/features/common/table/v2";
import DiscoveryMonitorItemActions from "~/features/data-discovery-and-detection/DiscoveryMonitorItemActions";
import DiffStatusCell from "~/features/data-discovery-and-detection/status-cells/DiffStatusCell";
import MonitorStatusCell from "~/features/data-discovery-and-detection/status-cells/MonitorStatusCell";
import { DiscoveryMonitorItem } from "~/features/data-discovery-and-detection/types/DiscoveryMonitorItem";
import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";
import { findResourceType } from "~/features/data-discovery-and-detection/utils/findResourceType";

import TaxonomyDisplayAndEdit from "../TaxonomyDisplayAndEdit";

const useStagedResourceColumns = ({
  resourceType,
}: {
  resourceType: StagedResourceType | undefined;
}) => {
  const columnHelper = createColumnHelper<DiscoveryMonitorItem>();

  const defaultColumns: ColumnDef<DiscoveryMonitorItem, any>[] = [
    columnHelper.accessor((row) => row.name, {
      id: "name",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => <DefaultHeaderCell value={resourceType} {...props} />,
    }),
    columnHelper.accessor((row) => row.monitor_status, {
      id: "monitor_status",
      cell: (props) => <MonitorStatusCell status={props.getValue()} />,
      header: (props) => <DefaultHeaderCell value="Monitoring" {...props} />,
      size: 50,
    }),
    columnHelper.accessor((row) => row.diff_status, {
      id: "diff_status",
      cell: (props) => <DiffStatusCell status={props.getValue()} />,
      header: (props) => <DefaultHeaderCell value="Change type" {...props} />,
    }),
    columnHelper.accessor((row) => row.modified, {
      id: "modified",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => <DefaultHeaderCell value="Last modified" {...props} />,
    }),
    columnHelper.accessor((row) => row, {
      id: "Action",
      cell: (props) => (
        <DiscoveryMonitorItemActions
          resource={props.getValue()}
          resourceType={findResourceType(props.getValue())}
        />
      ),
      header: (props) => <DefaultHeaderCell value="Action" {...props} />,
    }),
  ];

  if (!resourceType) {
    return { columns: defaultColumns };
  }

  if (resourceType === StagedResourceType.DATABASE) {
    const columns = [
      ...defaultColumns,
      columnHelper.accessor((row) => row.schemas, {
        id: "schemas",
        cell: (props) => <DefaultCell value={props.getValue()?.length} />,
        header: (props) => (
          <DefaultHeaderCell value="Schema count" {...props} />
        ),
      }),
    ];
    return { columns };
  }

  if (resourceType === StagedResourceType.SCHEMA) {
    const columns = [
      ...defaultColumns,
      columnHelper.accessor((row) => row.tables, {
        id: "tables",
        cell: (props) => <DefaultCell value={props.getValue()?.length} />,
        header: (props) => <DefaultHeaderCell value="Table count" {...props} />,
      }),
    ];
    return { columns };
  }

  if (resourceType === StagedResourceType.TABLE) {
    const columns = [
      ...defaultColumns,
      columnHelper.accessor((row) => row.fields, {
        id: "fields",
        cell: (props) => <DefaultCell value={props.getValue()?.length} />,
        header: (props) => <DefaultHeaderCell value="# of fields" {...props} />,
      }),
      columnHelper.accessor((row) => row.num_rows, {
        id: "num_rows",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="# of rows" {...props} />,
      }),
    ];
    return { columns };
  }

  if (resourceType === StagedResourceType.FIELD) {
    const columns = [
      ...defaultColumns,
      columnHelper.accessor((row) => row.data_type, {
        id: "data_type",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Data type" {...props} />,
      }),
      columnHelper.accessor((row) => row.classifications, {
        id: "classifications",
        cell: (props) => {
          const bestTaxonomyMatch =
            props.getValue() && props.getValue().length
              ? props.getValue()![0]
              : null;

          return (
            <TaxonomyDisplayAndEdit
              fidesLangKey={bestTaxonomyMatch?.label}
              isEditable
            />
          );
        },
        header: (props) => <DefaultHeaderCell value="Label" {...props} />,
        minSize: 240, // keep a minimum width so the Select has space to display the options properly
      }),
    ];
    return { columns };
  }

  return { columns: defaultColumns };
};

export default useStagedResourceColumns;
