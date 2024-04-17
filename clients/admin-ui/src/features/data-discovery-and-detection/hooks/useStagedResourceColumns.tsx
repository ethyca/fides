import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { DefaultCell, DefaultHeaderCell } from "~/features/common/table/v2";
import { Database, Field, Schema, StagedResource, Table } from "~/types/api";

export type MonitorResultsItem = StagedResource &
  Partial<Database & Schema & Table & Field>;

const useStagedResourceColumns = (items: MonitorResultsItem[] | undefined) => {
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
  ];

  if (!items?.length) {
    return { columns: defaultColumns };
  }

  if (items[0].schemas) {
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

  if (items[0].tables) {
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

  if (items[0].fields) {
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

  if (items[0].data_type) {
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
