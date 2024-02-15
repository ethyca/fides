/* eslint-disable react/no-unstable-nested-components */
import { Button, Flex, HStack } from "@fidesui/react";
import {
  createColumnHelper,
  getCoreRowModel,
  getGroupedRowModel,
  getExpandedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  BadgeCell,
  DefaultCell,
  DefaultHeaderCell,
  GroupCountBadgeCell,
  FidesTableV2,
  GlobalFilterV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "common/table/v2";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";
import AddVendor from "~/features/configure-consent/AddVendor";
import { ADD_MULTIPLE_VENDORS_ROUTE } from "~/features/common/nav/v2/routes";
import {
  useGetHealthQuery,
  useGetPropertiesQuery,
} from "~/features/plus/plus.slice";
import { Property } from "./types";

const columnHelper = createColumnHelper<Property>();

export type Page_Property_ = {
  items: Array<Property>;
  total: number;
  page: number;
  size: number;
  pages?: number;
};

const emptyInventoriesReportResponse: Page_Property_ = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};
export const InventoryTable = () => {
  const { isLoading: isLoadingHealthCheck } = useGetHealthQuery();

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
    resetPageIndexToDefault,
  } = useServerSidePagination();

  const [globalFilter, setGlobalFilter] = useState<string>();

  const updateGlobalFilter = (searchTerm: string) => {
    resetPageIndexToDefault();
    setGlobalFilter(searchTerm);
  };

  const {
    isFetching: isReportFetching,
    isLoading: isReportLoading,
    data: inventoriesReport,
  } = useGetPropertiesQuery({
    pageIndex,
    pageSize,
    search: globalFilter,
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(
    () => inventoriesReport || emptyInventoriesReportResponse,
    [inventoriesReport]
  );

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const inventoryColumns = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Property" {...props} />,
      }),
      columnHelper.accessor((row) => row.type, {
        id: "type",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Type" {...props} />,
      }),
      columnHelper.accessor((row) => row.domains, {
        id: "domains",
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="domains"
            value={props.getValue()}
            {...props}
          />
        ),
        header: (props) => <DefaultHeaderCell value="Domains" {...props} />,
        meta: {
          displayText: "Domains",
          showHeaderMenu: true,
        },
      }),
    ],
    []
  );

  const tableInstance = useReactTable<Property>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    columns: inventoryColumns,
    manualPagination: true,
    data,
    state: {
      expanded: true,
    },
  });

  const onRowClick = (property: Property) => {};

  const goToAddMultiple = () => {
    router.push(ADD_MULTIPLE_VENDORS_ROUTE);
  };

  if (isReportLoading || isLoadingHealthCheck) {
    return <TableSkeletonLoader rowHeight={36} numRows={15} />;
  }
  return (
    <Flex flex={1} direction="column" overflow="auto">
      <TableActionBar>
        <GlobalFilterV2
          globalFilter={globalFilter}
          setGlobalFilter={updateGlobalFilter}
          placeholder="Search property or domain"
        />
        <HStack alignItems="center" spacing={4}>
          <AddVendor
            buttonLabel="Add property"
            buttonVariant="outline"
            onButtonClick={goToAddMultiple}
          />
        </HStack>
      </TableActionBar>
      <FidesTableV2 tableInstance={tableInstance} onRowClick={onRowClick} />
      <PaginationBar
        totalRows={totalRows}
        pageSizes={PAGE_SIZES}
        setPageSize={setPageSize}
        onPreviousPageClick={onPreviousPageClick}
        isPreviousPageDisabled={isPreviousPageDisabled || isReportFetching}
        onNextPageClick={onNextPageClick}
        isNextPageDisabled={isNextPageDisabled || isReportFetching}
        startRange={startRange}
        endRange={endRange}
      />
    </Flex>
  );
};
