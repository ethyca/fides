import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { DefaultCell, DefaultHeaderCell } from "~/features/common/table/v2";
import DiscoveryMonitorItemActions from "~/features/data-discovery-and-detection/DiscoveryMonitorItemActions";
import { Database, Field, Schema, StagedResource, Table } from "~/types/api";

export type MonitorResultsItem = StagedResource &
  Partial<Database & Schema & Table & Field>;

export enum StagedResourceType {
  DATABASE = "database",
  SCHEMA = "schema",
  TABLE = "table",
  FIELD = "field",
  // there should never be actual data that doesn't match one of the types, but
  // having a fallback makes some TypeScript smoother
  NONE = "none",
}

export const findResourceType = (item: MonitorResultsItem | undefined) => {
  if (!item) {
    return StagedResourceType.NONE;
  }
  if (item.schemas) {
    return StagedResourceType.DATABASE;
  }
  if (item.tables) {
    return StagedResourceType.SCHEMA;
  }
  if (item.fields) {
    return StagedResourceType.TABLE;
  }
  return StagedResourceType.FIELD;
};

const useStagedResourceColumns = (
  resourceType: StagedResourceType | undefined
) => {
  const columnHelper = createColumnHelper<MonitorResultsItem>();

  const defaultColumns: ColumnDef<MonitorResultsItem, any>[] = [
    columnHelper.accessor((row) => row.name, {
      id: "name",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => <DefaultHeaderCell value="Name" {...props} />,
    }),
    columnHelper.accessor((row) => row.description, {
      id: "description",
      cell: (props) => <DefaultCell value={props.getValue()} />,
      header: (props) => <DefaultHeaderCell value="Description" {...props} />,
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
    ];
    return { columns };
  }

  return { columns: defaultColumns };
};

export default useStagedResourceColumns;
