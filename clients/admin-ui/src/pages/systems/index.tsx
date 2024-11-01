/* eslint-disable react/no-unstable-nested-components */
/* eslint-disable @typescript-eslint/no-use-before-define */
import {
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  AntButton as Button,
  Box,
  ConfirmationModal,
  EditIcon,
  HStack,
  Text,
  useDisclosure,
  useToast,
  VStack,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useCallback, useEffect, useMemo, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import { getErrorMessage } from "~/features/common/helpers";
import { TrashCanOutlineIcon } from "~/features/common/Icon/TrashCanOutlineIcon";
import Layout from "~/features/common/Layout";
import {
  ADD_SYSTEMS_ROUTE,
  EDIT_SYSTEM_ROUTE,
} from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import Restrict from "~/features/common/Restrict";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import EditDataUseCell from "~/features/data-discovery-and-detection/new-dataset-lifecycle/EditDataUseCell";
import {
  setActiveSystem,
  useDeleteSystemMutation,
  useGetSystemsQuery,
} from "~/features/system";
import { BasicSystemResponse, ScopeRegistryEnum } from "~/types/api";
import { isErrorResult } from "~/types/errors";

const columnHelper = createColumnHelper<BasicSystemResponse>();

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

const Systems: NextPage = () => {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const toast = useToast();
  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();
  const [deleteSystem] = useDeleteSystemMutation();
  const [selectedSystemForDelete, setSelectedSystemForDelete] =
    React.useState<BasicSystemResponse | null>(null);

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
  const updateGlobalFilter = useCallback(
    (searchTerm: string) => {
      resetPageIndexToDefault();
      setGlobalFilter(searchTerm);
    },
    [resetPageIndexToDefault, setGlobalFilter],
  );

  const {
    data: systemsResponse,
    isLoading,
    isFetching,
  } = useGetSystemsQuery({
    page: pageIndex,
    size: pageSize,
    search: globalFilter,
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => systemsResponse ?? EMPTY_RESPONSE, [systemsResponse]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const getSystemName = (system: BasicSystemResponse) =>
    system.name && !(system.name === "") ? system.name : system.fides_key;

  const handleEdit = useCallback(
    (system: BasicSystemResponse) => {
      dispatch(setActiveSystem(system));
      router.push({
        pathname: EDIT_SYSTEM_ROUTE,
        query: {
          id: system.fides_key,
        },
      });
    },
    [dispatch, router],
  );

  const handleDelete = async (system: BasicSystemResponse) => {
    const result = await deleteSystem(system.fides_key);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(successToastParams("Successfully deleted system"));
    }
    onDeleteClose();
  };

  const columns = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => (
          <DefaultCell value={getSystemName(props.row.original)} />
        ),
        header: (props) => <DefaultHeaderCell value="System Name" {...props} />,
        size: 200,
      }),
      columnHelper.accessor((row) => row.description, {
        id: "description",
        header: (props) => <DefaultHeaderCell value="Description" {...props} />,
        cell: (props) => (
          <DefaultCell value={props.getValue()} cellProps={props} />
        ),
        size: 300,
        meta: {
          showHeaderMenu: true,
        },
      }),
      columnHelper.display({
        id: "data-uses",
        cell: ({ row }) => <EditDataUseCell system={row.original} />,
        header: (props) => <DefaultHeaderCell value="Data uses" {...props} />,
        meta: {
          disableRowClick: true,
        },
      }),
      columnHelper.accessor((row) => row.administrating_department, {
        id: "department",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Department" {...props} />,
        size: 200,
      }),
      columnHelper.accessor((row) => row.processes_personal_data, {
        id: "processes_personal_data",
        cell: (props) => (
          <DefaultCell value={props.getValue() ? "Yes" : "No"} />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Processes Personal Data" {...props} />
        ),
        size: 100,
      }),
      columnHelper.display({
        id: "actions",
        header: "Actions",
        cell: ({ row }) => {
          const system = row.original;
          return (
            <HStack spacing={0} data-testid={`system-${system.fides_key}`}>
              <Button
                aria-label="Edit property"
                data-testid="edit-btn"
                size="small"
                className="mr-2"
                icon={<EditIcon />}
                onClick={() => handleEdit(system)}
              />
              <Restrict scopes={[ScopeRegistryEnum.SYSTEM_DELETE]}>
                <Button
                  aria-label="Delete system"
                  data-testid="delete-btn"
                  size="small"
                  className="mr-2"
                  icon={<TrashCanOutlineIcon />}
                  onClick={() => {
                    setSelectedSystemForDelete(system);
                    onDeleteOpen();
                  }}
                />
              </Restrict>
            </HStack>
          );
        },
        meta: {
          disableRowClick: true,
        },
      }),
    ],
    [handleEdit, onDeleteOpen],
  );

  const tableInstance = useReactTable<BasicSystemResponse>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columnResizeMode: "onChange",
    columns,
    data,
  });

  return (
    <Layout title="System inventory" mainProps={{ paddingTop: 0 }}>
      <Box data-testid="system-management">
        <PageHeader breadcrumbs={[{ title: "System inventory" }]}>
          <Text fontSize="sm" mb={1}>
            View and manage recently detected systems and vendors here.
          </Text>
        </PageHeader>
        {isLoading ? (
          <TableSkeletonLoader rowHeight={36} numRows={15} />
        ) : (
          <>
            <TableActionBar>
              <GlobalFilterV2
                globalFilter={globalFilter}
                setGlobalFilter={updateGlobalFilter}
                placeholder="Search"
                testid="system-search"
              />
            </TableActionBar>
            <FidesTableV2
              tableInstance={tableInstance}
              emptyTableNotice={<EmptyTableNotice />}
              onRowClick={handleEdit}
            />
          </>
        )}
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

        <ConfirmationModal
          isOpen={deleteIsOpen}
          onClose={onDeleteClose}
          onConfirm={() => handleDelete(selectedSystemForDelete!)}
          title={`Delete ${
            selectedSystemForDelete && getSystemName(selectedSystemForDelete)
          }`}
          message={
            <>
              <Text>
                You are about to permanently delete the system{" "}
                <Text
                  color="complimentary.500"
                  as="span"
                  fontWeight="bold"
                  whiteSpace="nowrap"
                >
                  {selectedSystemForDelete &&
                    getSystemName(selectedSystemForDelete)}
                </Text>
                .
              </Text>
              <Text>Are you sure you would like to continue?</Text>
            </>
          }
        />
      </Box>
    </Layout>
  );
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
    textAlign="center"
  >
    <VStack>
      <Text fontSize="md" fontWeight="600">
        No systems found.
      </Text>
      <Text fontSize="sm">
        Click &quot;Add a system&quot; to add your first system to Fides.
      </Text>
    </VStack>
    <Button
      href={ADD_SYSTEMS_ROUTE}
      size="small"
      type="primary"
      data-testid="add-privacy-notice-btn"
    >
      Add a system +
    </Button>
  </VStack>
);

export default Systems;
