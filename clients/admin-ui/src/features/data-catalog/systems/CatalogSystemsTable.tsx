/* eslint-disable react/no-unstable-nested-components */

import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  RowSelectionState,
  useReactTable,
} from "@tanstack/react-table";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import { DATA_CATALOG_ROUTE } from "~/features/common/nav/v2/routes";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  PaginationBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { getQueryParamsFromArray } from "~/features/common/utils";
import { useGetCatalogSystemsQuery } from "~/features/data-catalog/data-catalog.slice";
import EmptyCatalogTableNotice from "~/features/data-catalog/datasets/EmptyCatalogTableNotice";
import EditDataUseCell from "~/features/data-catalog/systems/EditDataUseCell";
import SystemActionsCell from "~/features/data-catalog/systems/SystemActionCell";
import { useLazyGetAvailableDatabasesByConnectionQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { SystemWithMonitorKeys } from "~/types/api";

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  size: 50,
  pages: 1,
};

const columnHelper = createColumnHelper<SystemWithMonitorKeys>();

const CatalogSystemsTable = () => {
  const [rowSelectionState, setRowSelectionState] = useState<RowSelectionState>(
    {},
  );

  const router = useRouter();

  const {
    PAGE_SIZES,
    pageSize,
    setPageSize,
    onPreviousPageClick,
    isPreviousPageDisabled,
    onNextPageClick,
    isNextPageDisabled,
    startRange,
    endRange,
    pageIndex,
    setTotalPages,
  } = useServerSidePagination();

  const { data: queryResult, isLoading } = useGetCatalogSystemsQuery({
    page: pageIndex,
    size: pageSize,
    show_hidden: false,
  });

  const [getProjects] = useLazyGetAvailableDatabasesByConnectionQuery();

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => queryResult ?? EMPTY_RESPONSE, [queryResult]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const handleRowClicked = async (row: SystemWithMonitorKeys) => {
    // if there are projects, go to project view; otherwise go to datasets view
    const projectsResponse = await getProjects({
      connection_config_key: row.connection_configs!.key,
      page: 1,
      size: 1,
    });

    const hasProjects = !!projectsResponse?.data?.total;
    const queryString = getQueryParamsFromArray(
      row.monitor_config_keys ?? [],
      "monitor_config_ids",
    );

    const url = `${DATA_CATALOG_ROUTE}/${row.fides_key}/${hasProjects ? "projects" : "resources"}?${queryString}`;
    router.push(url);
  };

  const columns: ColumnDef<SystemWithMonitorKeys, any>[] = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: ({ getValue, row }) => (
          <DefaultCell
            value={getValue()}
            fontWeight={
              row.original.connection_configs?.key ? "semibold" : "normal"
            }
          />
        ),
        header: (props) => <DefaultHeaderCell value="Name" {...props} />,
      }),
      columnHelper.display({
        id: "data-uses",
        cell: ({ row }) => <EditDataUseCell system={row.original} />,
        header: (props) => <DefaultHeaderCell value="Data uses" {...props} />,
        meta: {
          disableRowClick: true,
        },
        minSize: 280,
      }),
      columnHelper.display({
        id: "actions",
        cell: (props) => (
          <SystemActionsCell
            onDetailClick={() =>
              router.push(`/systems/configure/${props.row.original.fides_key}`)
            }
          />
        ),
        maxSize: 20,
        enableResizing: false,
        meta: {
          cellProps: {
            borderLeft: "none",
          },
          disableRowClick: true,
        },
      }),
    ],
    [router],
  );

  const tableInstance = useReactTable<SystemWithMonitorKeys>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getRowId: (row) => row.fides_key,
    manualPagination: true,
    columnResizeMode: "onChange",
    columns,
    data,
    onRowSelectionChange: setRowSelectionState,
    state: {
      rowSelection: rowSelectionState,
    },
  });

  if (isLoading) {
    return <TableSkeletonLoader rowHeight={36} numRows={36} />;
  }

  return (
    <>
      <FidesTableV2
        tableInstance={tableInstance}
        emptyTableNotice={<EmptyCatalogTableNotice />}
        onRowClick={handleRowClicked}
        getRowIsClickable={(row) => !!row.connection_configs?.key}
      />
      <PaginationBar
        totalRows={totalRows || 0}
        pageSizes={PAGE_SIZES}
        setPageSize={setPageSize}
        onPreviousPageClick={onPreviousPageClick}
        isPreviousPageDisabled={isPreviousPageDisabled}
        onNextPageClick={onNextPageClick}
        isNextPageDisabled={isNextPageDisabled}
        startRange={startRange}
        endRange={endRange}
      />
    </>
  );
};

export default CatalogSystemsTable;
