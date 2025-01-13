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
import { Text, VStack } from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import { DATA_CATALOG_ROUTE } from "~/features/common/nav/v2/routes";
import {
  DefaultCell,
  FidesTableV2,
  PaginationBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { RelativeTimestampCell } from "~/features/common/table/v2/cells";
import CatalogResourceNameCell from "~/features/data-catalog/CatalogResourceNameCell";
import CatalogStatusBadgeCell from "~/features/data-catalog/CatalogStatusBadgeCell";
import { useGetCatalogProjectsQuery } from "~/features/data-catalog/data-catalog.slice";
import { getCatalogResourceStatus } from "~/features/data-catalog/utils";
import { StagedResourceAPIResponse } from "~/types/api";

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  size: 50,
  pages: 1,
};

const EmptyTableNotice = () => (
  <VStack
    mt={6}
    p={10}
    spacing={4}
    borderRadius="base"
    maxW="70%"
    data-testid="empty-state"
    alignSelf="center"
    margin="auto"
  >
    <VStack>
      <Text fontSize="md" fontWeight="600">
        No resources found
      </Text>
    </VStack>
  </VStack>
);

const columnHelper = createColumnHelper<StagedResourceAPIResponse>();

const CatalogProjectsTable = ({
  systemKey,
  monitorConfigIds,
}: {
  systemKey: string;
  monitorConfigIds: string[];
}) => {
  const [rowSelectionState, setRowSelectionState] = useState<RowSelectionState>(
    {},
  );

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

  const {
    isFetching,
    isLoading,
    data: queryResult,
  } = useGetCatalogProjectsQuery({
    page: pageIndex,
    size: pageSize,
    monitor_config_ids: monitorConfigIds,
  });

  const router = useRouter();

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => queryResult ?? EMPTY_RESPONSE, [queryResult]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const columns: ColumnDef<StagedResourceAPIResponse, any>[] = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => (
          <CatalogResourceNameCell resource={props.row.original} />
        ),
        header: "Project",
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
      columnHelper.accessor((row) => row.monitor_config_id, {
        id: "monitorConfigId",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: "Detected by",
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
        meta: {
          cellProps: {
            borderRight: "none",
          },
        },
      }),
    ],
    [],
  );

  const tableInstance = useReactTable<StagedResourceAPIResponse>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    manualPagination: true,
    columnResizeMode: "onChange",
    columns,
    data,
    onRowSelectionChange: setRowSelectionState,
    state: {
      rowSelection: rowSelectionState,
    },
  });

  if (isLoading || isFetching) {
    return <TableSkeletonLoader rowHeight={36} numRows={36} />;
  }

  return (
    <>
      <FidesTableV2
        tableInstance={tableInstance}
        emptyTableNotice={<EmptyTableNotice />}
        onRowClick={(row) =>
          router.push(`${DATA_CATALOG_ROUTE}/${systemKey}/projects/${row.urn}`)
        }
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

export default CatalogProjectsTable;
