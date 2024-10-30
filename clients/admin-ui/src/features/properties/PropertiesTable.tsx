/* eslint-disable react/no-unstable-nested-components */
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
import { Flex, HStack, Text, VStack } from "fidesui";
import _ from "lodash";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import { EDIT_PROPERTY_ROUTE } from "~/features/common/nav/v2/routes";
import Restrict, { useHasPermission } from "~/features/common/Restrict";
import { useGetHealthQuery } from "~/features/plus/plus.slice";
import { useGetAllPropertiesQuery } from "~/features/properties/property.slice";
import { Page_Property_, Property, ScopeRegistryEnum } from "~/types/api";

import AddPropertyButton from "./AddPropertyButton";
import PropertyActions from "./PropertyActions";

const columnHelper = createColumnHelper<Property>();

const emptyPropertiesResponse: Page_Property_ = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

const EmptyTableNotice = () => (
  <VStack
    mt={6}
    p={10}
    spacing={4}
    borderRadius="base"
    maxW="70%"
    data-testid="no-results-notice"
    alignSelf="center"
    margin="auto"
  >
    <VStack>
      <Text fontSize="md" fontWeight="600">
        No properties found.
      </Text>
      <Restrict scopes={[ScopeRegistryEnum.PROPERTY_CREATE]}>
        <Text fontSize="sm">
          Click “Add property” to add your first property to Fides.
        </Text>
        <AddPropertyButton
          buttonLabel="Add property"
          buttonProps={{ type: "primary" }}
        />
      </Restrict>
    </VStack>
  </VStack>
);

export const PropertiesTable = () => {
  const { isLoading: isLoadingHealthCheck } = useGetHealthQuery();

  const userCanUpdate = useHasPermission([ScopeRegistryEnum.PROPERTY_UPDATE]);

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
  const router = useRouter();
  const [globalFilter, setGlobalFilter] = useState<string>();

  const updateGlobalFilter = useCallback(
    (searchTerm: string) => {
      resetPageIndexToDefault();
      setGlobalFilter(searchTerm);
    },
    [resetPageIndexToDefault, setGlobalFilter],
  );

  const {
    isFetching,
    isLoading,
    data: properties,
  } = useGetAllPropertiesQuery({
    page: pageIndex,
    size: pageSize,
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
      columnHelper.accessor((row) => row.experiences.map((exp) => exp.name), {
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
          showHeaderMenu: true,
        },
      }),
      columnHelper.display({
        id: "actions",
        header: "Actions",
        cell: ({ row }) => <PropertyActions property={row.original} />,
      }),
    ],
    [],
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
    columnResizeMode: "onChange",
  });

  const onRowClick = (property: Property) => {
    if (userCanUpdate) {
      router.push({
        pathname: EDIT_PROPERTY_ROUTE,
        query: { id: property.id },
      });
    }
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
            <Restrict scopes={[ScopeRegistryEnum.PROPERTY_CREATE]}>
              <AddPropertyButton
                buttonLabel="Add property"
                buttonProps={{ size: "small" }}
              />
            </Restrict>
          </HStack>
        </TableActionBar>
        <FidesTableV2
          tableInstance={tableInstance}
          onRowClick={onRowClick}
          emptyTableNotice={<EmptyTableNotice />}
        />
        <PaginationBar
          totalRows={totalRows || 0}
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
