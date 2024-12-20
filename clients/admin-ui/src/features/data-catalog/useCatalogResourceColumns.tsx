import { ColumnDef, createColumnHelper } from "@tanstack/react-table";

import { DefaultCell } from "~/features/common/table/v2";
import { RelativeTimestampCell } from "~/features/common/table/v2/cells";
import CatalogResourceActionsCell from "~/features/data-catalog/CatalogResourceActionsCell";
import CatalogResourceNameCell from "~/features/data-catalog/CatalogResourceNameCell";
import CatalogStatusBadgeCell from "~/features/data-catalog/CatalogStatusBadgeCell";
import { getCatalogResourceStatus } from "~/features/data-catalog/utils";
import EditCategoryCell from "~/features/data-discovery-and-detection/tables/cells/EditCategoryCell";
import FieldDataTypeCell from "~/features/data-discovery-and-detection/tables/cells/FieldDataTypeCell";
import { StagedResourceType } from "~/features/data-discovery-and-detection/types/StagedResourceType";
import { StagedResourceAPIResponse } from "~/types/api";

const columnHelper = createColumnHelper<StagedResourceAPIResponse>();

const useCatalogResourceColumns = (type: StagedResourceType) => {
  const defaultColumns: ColumnDef<StagedResourceAPIResponse, any>[] = [];

  if (!type) {
    return defaultColumns;
  }

  if (type === StagedResourceType.TABLE) {
    const columnDefs = [
      columnHelper.display({
        id: "name",
        cell: ({ row }) => <CatalogResourceNameCell resource={row.original} />,
        header: "Table",
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
      columnHelper.display({
        id: "category",
        cell: ({ row }) => <EditCategoryCell resource={row.original} />,
        header: "Data categories",
        minSize: 280,
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
        cell: ({ row }) => (
          <CatalogResourceActionsCell resource={row.original} />
        ),
        header: "Actions",
        meta: {
          disableRowClick: true,
        },
      }),
    ];
    return columnDefs;
  }

  if (type === StagedResourceType.FIELD) {
    const columns = [
      columnHelper.display({
        id: "name",
        cell: ({ row }) => <CatalogResourceNameCell resource={row.original} />,
        header: "Field",
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
      columnHelper.accessor((row) => row.data_type, {
        id: "dataType",
        cell: (props) => <FieldDataTypeCell type={props.getValue()} />,
        header: "Data type",
      }),
      columnHelper.display({
        id: "category",
        cell: ({ row }) => <EditCategoryCell resource={row.original} />,
        header: "Data categories",
        minSize: 280,
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
        cell: ({ row }) => (
          <CatalogResourceActionsCell resource={row.original} />
        ),
        header: "Actions",
        meta: {
          disableRowClick: true,
        },
      }),
    ];
    return columns;
  }
  return defaultColumns;
};

export default useCatalogResourceColumns;
