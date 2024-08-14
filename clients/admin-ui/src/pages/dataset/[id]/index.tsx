/* eslint-disable react/no-unstable-nested-components */
/* eslint-disable @typescript-eslint/no-use-before-define */
import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  Box,
  Breadcrumb,
  Button,
  EditIcon,
  HStack,
  Text,
  VStack,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";
import { DatabaseIcon } from "~/features/common/Icon/database/DatabaseIcon";
import { DatasetIcon } from "~/features/common/Icon/database/DatasetIcon";

import Layout from "~/features/common/Layout";
import {
  DATASET_ROUTE,
  DATASET_URL_DETAIL_ROUTE,
} from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  TableActionBar,
  TableSkeletonLoader,
} from "~/features/common/table/v2";
import { useGetDatasetByKeyQuery } from "~/features/dataset";
import DatasetBreadcrumbs from "~/features/dataset/DatasetBreadcrumbs";
import EditCollectionDrawer from "~/features/dataset/EditCollectionDrawer";
import { Dataset, DatasetCollection } from "~/types/api";

const columnHelper = createColumnHelper<DatasetCollection>();

const DatasetDetailPage: NextPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const datasetId = Array.isArray(id) ? id[0] : id!;

  const { isLoading, data } = useGetDatasetByKeyQuery(datasetId);
  const collections = data?.collections || [];

  const [isEditingCollection, setIsEditingCollection] = useState(false);
  const [selectedCollectionForEditing, setSelectedCollectionForEditing] =
    useState<DatasetCollection | undefined>();

  const [globalFilter, setGlobalFilter] = useState<string>();

  const columns = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Collection Name" {...props} />
        ),
        size: 180,
      }),
      columnHelper.accessor((row) => row.description, {
        id: "description",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Description" {...props} />,
        size: 300,
      }),

      columnHelper.display({
        id: "actions",
        header: "Actions",
        cell: ({ row }) => {
          const dataset = row.original;
          return (
            <HStack spacing={0} data-testid={`collection-${dataset.name}`}>
              <Button
                variant="outline"
                size="xs"
                leftIcon={<EditIcon />}
                onClick={() => {
                  setSelectedCollectionForEditing(dataset);
                  setIsEditingCollection(true);
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
    ],
    [],
  );

  const tableInstance = useReactTable<DatasetCollection>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columns,
    data: collections,
  });

  const handleRowClick = (collection: DatasetCollection) => {
    router.push({
      pathname: DATASET_URL_DETAIL_ROUTE,
      query: {
        id: datasetId,
        urn: collection.name,
      },
    });
  };

  return (
    <Layout title={`Dataset - ${datasetId}`} mainProps={{ paddingTop: 0 }}>
      <PageHeader breadcrumbs={[{ title: "Datasets" }]}>
        <DatasetBreadcrumbs
          breadcrumbs={[
            {
              title: "All datasets",
              icon: <DatabaseIcon />,
              link: DATASET_ROUTE,
            },
            {
              title: datasetId,
              icon: <DatasetIcon />,
            },
          ]}
        />
      </PageHeader>

      {isLoading ? (
        <TableSkeletonLoader rowHeight={36} numRows={15} />
      ) : (
        <Box data-testid="collections-table">
          <TableActionBar>
            <GlobalFilterV2
              globalFilter={globalFilter}
              setGlobalFilter={setGlobalFilter}
              placeholder="Search"
              testid="system-search"
            />
          </TableActionBar>
          <FidesTableV2
            tableInstance={tableInstance}
            emptyTableNotice={<EmptyTableNotice />}
            onRowClick={handleRowClick}
          />
        </Box>
      )}

      <EditCollectionDrawer
        collection={selectedCollectionForEditing}
        isOpen={isEditingCollection}
        onClose={() => setIsEditingCollection(false)}
      />
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
        No collections found.
      </Text>
    </VStack>
  </VStack>
);

export default DatasetDetailPage;
