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
import {
  AntButton as Button,
  Box,
  EditIcon,
  HStack,
  Text,
  VStack,
} from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useDispatch } from "react-redux";

import { usePollForClassifications } from "~/features/common/classifications";
import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { DATASET_DETAIL_ROUTE } from "~/features/common/nav/routes";
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
import EditDatasetDrawer from "~/features/dataset/EditDatasetDrawer";
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

  const [isEditingDataset, setIsEditingDataset] = useState(false);
  const [selectedDatasetForEditing, setSelectedDatasetForEditing] = useState<
    Dataset | undefined
  >();

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

  const onRowClick = useCallback(
    (dataset: Dataset) => {
      dispatch(setActiveDatasetFidesKey(dataset.fides_key));
      router.push({
        pathname: DATASET_DETAIL_ROUTE,
        query: {
          datasetId: encodeURIComponent(dataset.fides_key),
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
          cell: (props) => (
            <DefaultCell value={props.getValue()} fontWeight="semibold" />
          ),
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
          cell: (props) => (
            <DefaultCell value={props.getValue()} cellProps={props} />
          ),
          header: (props) => (
            <DefaultHeaderCell value="Description" {...props} />
          ),
          size: 300,
          meta: {
            showHeaderMenu: true,
          },
        }),

        columnHelper.display({
          id: "actions",
          header: "Actions",
          cell: ({ row }) => {
            const dataset = row.original;
            return (
              <HStack spacing={0} data-testid={`dataset-${dataset.fides_key}`}>
                <Button
                  size="small"
                  icon={<EditIcon />}
                  onClick={() => {
                    setSelectedDatasetForEditing(dataset);
                    setIsEditingDataset(true);
                  }}
                >
                  Edit
                </Button>
              </HStack>
            );
          },
          meta: {
            disableRowClick: true,
          },
        }),
      ].filter(Boolean) as ColumnDef<Dataset, any>[],
    [],
  );

  const tableInstance = useReactTable<Dataset>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columns,
    data,
    columnResizeMode: "onChange",
  });

  return (
    <Layout title="Datasets">
      <Box data-testid="system-management">
        <PageHeader
          heading="Datasets"
          breadcrumbItems={[
            {
              title: "All datasets",
            },
          ]}
          rightContent={
            <NextLink href="/dataset/new" passHref legacyBehavior>
              <Button data-testid="create-dataset-btn">+ Add dataset</Button>
            </NextLink>
          }
        />

        {isLoading ? (
          <TableSkeletonLoader rowHeight={36} numRows={15} />
        ) : (
          <Box data-testid="dataset-table">
            <TableActionBar>
              <GlobalFilterV2
                globalFilter={globalFilter}
                setGlobalFilter={updateGlobalFilter}
                placeholder="Search"
                testid="dataset-search"
              />
            </TableActionBar>
            <FidesTableV2
              tableInstance={tableInstance}
              emptyTableNotice={<EmptyTableNotice />}
              onRowClick={onRowClick}
            />
          </Box>
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

        <EditDatasetDrawer
          dataset={selectedDatasetForEditing}
          isOpen={isEditingDataset}
          onClose={() => {
            setSelectedDatasetForEditing(undefined);
            setIsEditingDataset(false);
          }}
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
