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
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import Restrict from "~/features/common/Restrict";
import SearchInput from "~/features/common/SearchInput";
import { ListExpandableCell } from "~/features/common/table/cells";
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
import {
  setActiveSystem,
  useDeleteSystemMutation,
  useGetSystemsQuery,
} from "~/features/system";
import { usMockGetSystemsWithGroupsQuery } from "~/mocks/TEMP-system-groups/endpoints/systems";
import { DEFAULT_SYSTEMS_WITH_GROUPS } from "~/mocks/TEMP-system-groups/endpoints/systems-with-groups-response";
import NewTable from "~/pages/systems/new-table";
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

  const systemsResponse = DEFAULT_SYSTEMS_WITH_GROUPS;

  const {
    // data: systemsResponse,
    isLoading,
    isFetching,
  } = useGetSystemsQuery({
    page: pageIndex,
    size: pageSize,
    search: globalFilter,
  });

  // const { data: systemsResponse, isLoading } = usMockGetSystemsWithGroupsQuery({
  //   page: pageIndex,
  //   size: pageSize,
  //   search: globalFilter,
  //   groupFilters: [],
  // });

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
        hash: "#information",
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

  return (
    <Layout title="System inventory">
      <Box data-testid="system-management">
        <PageHeader
          heading="System inventory"
          breadcrumbItems={[{ title: "All systems" }]}
        />
        {isLoading ? (
          <TableSkeletonLoader rowHeight={36} numRows={15} />
        ) : (
          <NewTable data={data} loading={isLoading} />
        )}
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
