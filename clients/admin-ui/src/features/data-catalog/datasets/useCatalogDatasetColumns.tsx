/* eslint-disable react/no-unstable-nested-components */

import { ColumnDef, createColumnHelper } from "@tanstack/react-table";
import { AntButton } from "fidesui";
import { useMemo } from "react";

import {
  DefaultCell,
  IndeterminateCheckboxCell,
} from "~/features/common/table/v2";
import { RelativeTimestampCell } from "~/features/common/table/v2/cells";
import { StagedResourceAPIResponse } from "~/types/api";

const columnHelper = createColumnHelper<StagedResourceAPIResponse>();

const useCatalogDatasetColumns = () => {
  const columns: ColumnDef<StagedResourceAPIResponse, any>[] = useMemo(
    () => [
      columnHelper.display({
        id: "select",
        cell: ({ row }) => (
          <IndeterminateCheckboxCell
            isChecked={row.getIsSelected()}
            onChange={row.getToggleSelectedHandler()}
            dataTestId={`select-row-${row.id}`}
          />
        ),
        header: ({ table }) => (
          <IndeterminateCheckboxCell
            isChecked={table.getIsAllPageRowsSelected()}
            onChange={table.getToggleAllPageRowsSelectedHandler()}
            dataTestId="select-all-rows"
          />
        ),
        maxSize: 25,
        enableResizing: false,
        meta: {
          cellProps: {
            borderRight: "none",
          },
          disableRowClick: true,
        },
      }),
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => (
          <DefaultCell value={props.getValue()} fontWeight="semibold" />
        ),
        header: "Name",
      }),
      columnHelper.display({
        id: "status",
        cell: () => <DefaultCell value="TODO" />,
        header: "Status",
      }),
      columnHelper.accessor((row) => row.description, {
        id: "description",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: "Description",
      }),
      columnHelper.accessor((row) => row.updated_at, {
        id: "lastUpdated",
        cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
        header: "Updated",
      }),
      columnHelper.display({
        id: "actions",
        cell: () => (
          <AntButton size="small" disabled>
            Actions
          </AntButton>
        ),
        header: "Actions",
      }),
    ],
    [],
  );

  return columns;
};

export default useCatalogDatasetColumns;
