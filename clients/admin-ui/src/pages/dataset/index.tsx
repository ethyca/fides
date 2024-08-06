/* eslint-disable @typescript-eslint/no-use-before-define */
/* eslint-disable react/no-unstable-nested-components */
import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Box, Button, Text, VStack } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useDispatch } from "react-redux";

import { usePollForClassifications } from "~/features/common/classifications";
import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { DATASET_EDIT_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
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
import {
  setActiveDatasetFidesKey,
  useGetDatasetsQuery,
} from "~/features/dataset/dataset.slice";
import { Dataset, GenerateTypes } from "~/types/api";

const columnHelper = createColumnHelper<Dataset>();

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

const DataSets: NextPage = () => {
  const dispatch = useDispatch();
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
    data: datasetResponse,
    isLoading,
    isFetching,
  } = useGetDatasetsQuery({
    page: pageIndex,
    size: pageSize,
    search: globalFilter,
    exclude_saas_datasets: true,
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => datasetResponse ?? EMPTY_RESPONSE, [datasetResponse]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const handleEdit = useCallback(
    (dataset: Dataset) => {
      dispatch(setActiveDatasetFidesKey(dataset.fides_key));
      router.push({
        pathname: DATASET_EDIT_ROUTE,
        query: {
          id: dataset.fides_key,
        },
      });
    },
    [dispatch, router],
  );

  const features = useFeatures();
  usePollForClassifications({
    resourceType: GenerateTypes.DATASETS,
    skip: !features.plus,
  });

  const columns = useMemo(
    () =>
      [
        columnHelper.accessor((row) => row.name, {
          id: "name",
          cell: (props) => <DefaultCell value={props.getValue()} />,
          header: (props) => (
            <DefaultHeaderCell value="Dataset Name" {...props} />
          ),
          size: 180,
        }),
        columnHelper.accessor((row) => row.fides_key, {
          id: "fides_key",
          cell: (props) => <DefaultCell value={props.getValue()} />,
          header: (props) => <DefaultHeaderCell value="Fides Key" {...props} />,
          size: 150,
        }),
        columnHelper.accessor((row) => row.description, {
          id: "description",
          cell: (props) => <DefaultCell value={props.getValue()} />,
          header: (props) => (
            <DefaultHeaderCell value="Description" {...props} />
          ),
          size: 300,
        }),

        // Will be added back in PROD-2481
        // columnHelper.display({
        //   id: "actions",
        //   header: "Actions",
        //   cell: ({ row }) => {
        //     const system = row.original;
        //     return (
        //       <HStack spacing={0} data-testid={`system-${system.fides_key}`}>
        //         <IconButton
        //           aria-label="Edit property"
        //           data-testid="edit-btn"
        //           variant="outline"
        //           size="xs"
        //           mr={2}
        //           icon={<EditIcon />}
        //           onClick={() => handleEdit(system)}
        //         />
        //       </HStack>
        //     );
        //   },
        //   meta: {
        //     disableRowClick: true,
        //   },
        // })
      ].filter(Boolean) as ColumnDef<Dataset, any>[],
    [],
  );

  const tableInstance = useReactTable<Dataset>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columns,
    data,
  });

  return (
    <Layout title="Datasets" mainProps={{ paddingTop: 0 }}>
      <Box data-testid="system-management">
        <PageHeader breadcrumbs={[{ title: "Datasets" }]} />
        {isLoading ? (
          <TableSkeletonLoader rowHeight={36} numRows={15} />
        ) : (
          <Box data-testid="dataset-table">
            <TableActionBar>
              <GlobalFilterV2
                globalFilter={globalFilter}
                setGlobalFilter={updateGlobalFilter}
                placeholder="Search"
                testid="system-search"
              />
              <Button
                as={NextLink}
                href="/dataset/new"
                mr={2}
                colorScheme="primary"
                size="xs"
                data-testid="create-dataset-btn"
              >
                Create new dataset
              </Button>
            </TableActionBar>
            <FidesTableV2
              tableInstance={tableInstance}
              emptyTableNotice={<EmptyTableNotice />}
              onRowClick={handleEdit}
            />
          </Box>
        )}
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
        No datasets found.
      </Text>
      <Text fontSize="sm">
        Click &quot;Create new dataset&quot; to add your first dataset to Fides.
      </Text>
    </VStack>
  </VStack>
);

export default DataSets;
