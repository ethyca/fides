/* eslint-disable react/no-unstable-nested-components */

import { ColumnDef, createColumnHelper } from "@tanstack/react-table";
import { useMemo } from "react";

import { DefaultCell } from "~/features/common/table/v2";
import { RelativeTimestampCell } from "~/features/common/table/v2/cells";
import CatalogResourceNameCell from "~/features/data-catalog/CatalogResourceNameCell";
import CatalogStatusBadgeCell from "~/features/data-catalog/CatalogStatusBadgeCell";
import { getCatalogResourceStatus } from "~/features/data-catalog/utils";
import { StagedResourceAPIResponse } from "~/types/api";

const columnHelper = createColumnHelper<StagedResourceAPIResponse>();

const useCatalogDatasetColumns = () => {
  const columns: ColumnDef<StagedResourceAPIResponse, any>[] = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => (
          <CatalogResourceNameCell resource={props.row.original} />
        ),
        header: "Dataset",
      }),
      columnHelper.display({
        id: "status",
        cell: ({ row }) => (
          <CatalogStatusBadgeCell
            status={getCatalogResourceStatus(row.original)}
          />
        ),
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
    ],
    [],
  );

  return columns;
};

export default useCatalogDatasetColumns;
