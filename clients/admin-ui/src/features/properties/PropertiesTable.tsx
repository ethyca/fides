/* eslint-disable react/no-unstable-nested-components */
import { Flex, HStack } from "@fidesui/react";
import {
  createColumnHelper,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  GroupCountBadgeCell,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "common/table/v2";
import _ from "lodash";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import { ADD_PROPERTY_ROUTE } from "~/features/common/nav/v2/routes";
import { useGetHealthQuery } from "~/features/plus/plus.slice";
import { useGetPropertiesQuery } from "~/features/properties/property.slice";
import { Page_Property_, Property } from "~/types/api";

import AddProperty from "./AddPropertyButton";
import PropertyActions from "./PropertyActions";

const columnHelper = createColumnHelper<Property>();

const emptyPropertiesResponse: Page_Property_ = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};
export const PropertiesTable = () => {
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
    isFetching,
    isLoading,
    data: properties,
  } = useGetPropertiesQuery({
    pageIndex,
    pageSize,
    search: globalFilter,
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => properties || emptyPropertiesResponse, [properties]);

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
        cell: (props) => <DefaultCell value={_.capitalize(props.getValue())} />,
        header: (props) => <DefaultHeaderCell value="Type" {...props} />,
      }),
      columnHelper.accessor((row) => row.experiences, {
        id: "experiences",
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="experiences"
            value={props.getValue()}
            {...props}
          />
        ),
        header: (props) => <DefaultHeaderCell value="Experience" {...props} />,
        meta: {
          displayText: "Experience",
          showHeaderMenu: true,
        },
      }),
      columnHelper.display({
        id: "actions",
        header: "Actions",
        cell: ({ row }) => <PropertyActions property={row.original} />,
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

  const onRowClick = () => {};

  const goToAddProperty = () => {
    router.push(ADD_PROPERTY_ROUTE);
  };

  if (isLoading || isLoadingHealthCheck) {
    return <TableSkeletonLoader rowHeight={36} numRows={15} />;
  }
  return (
    <div>
      <Flex flex={1} direction="column" overflow="auto">
        <TableActionBar>
          <GlobalFilterV2
            globalFilter={globalFilter}
            setGlobalFilter={updateGlobalFilter}
            placeholder="Search property"
          />
          <HStack alignItems="center" spacing={4}>
            <AddProperty
              buttonLabel="Add property"
              buttonVariant="outline"
              onButtonClick={goToAddProperty}
            />
          </HStack>
        </TableActionBar>
        <FidesTableV2 tableInstance={tableInstance} onRowClick={onRowClick} />
        <PaginationBar
          totalRows={totalRows}
          pageSizes={PAGE_SIZES}
          setPageSize={setPageSize}
          onPreviousPageClick={onPreviousPageClick}
          isPreviousPageDisabled={isPreviousPageDisabled || isFetching}
          onNextPageClick={onNextPageClick}
          isNextPageDisabled={isNextPageDisabled || isFetching}
          startRange={startRange}
          endRange={endRange}
        />
      </Flex>
    </div>
  );
};
