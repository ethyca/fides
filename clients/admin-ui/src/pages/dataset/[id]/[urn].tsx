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
import { Box, Button, EditIcon, HStack, Text, VStack } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import { DATASET_URL_DETAIL_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  BadgeCell,
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  TableActionBar,
  TableSkeletonLoader,
} from "~/features/common/table/v2";
import TaxonomiesPicker from "~/features/common/TaxonomiesPicker";
import { useGetDatasetByKeyQuery } from "~/features/dataset";
import EditFieldDrawer from "~/features/dataset/EditFieldDrawer";
import { Dataset, DatasetCollection, DatasetField } from "~/types/api";

const columnHelper = createColumnHelper<DatasetCollection>();

const FieldsDetailPage: NextPage = () => {
  const router = useRouter();
  const { id: idParam, urn: urnParam } = router.query;
  const datasetId = Array.isArray(idParam) ? idParam[0] : idParam;
  const urn = Array.isArray(urnParam) ? urnParam[0] : urnParam;
  const collectionName = urn?.split(".")[0];

  const { isLoading, data: dataset } = useGetDatasetByKeyQuery(
    datasetId as string,
  );
  const collections = dataset?.collections || [];
  const collection = collections.find((c) => c.name === collectionName);
  const fields: DatasetField[] = collection?.fields || [];

  const [globalFilter, setGlobalFilter] = useState<string>();

  console.log("field", fields);

  const columns = useMemo(
    () =>
      [
        columnHelper.accessor((row) => row.name, {
          id: "name",
          cell: (props) => <DefaultCell value={props.getValue()} />,
          header: (props) => (
            <DefaultHeaderCell value="Field Name" {...props} />
          ),
          size: 180,
        }),
        columnHelper.accessor((row) => row.fides_meta?.data_type, {
          id: "type",
          cell: (props) =>
            props.getValue() ? (
              <BadgeCell value={props.getValue()!} />
            ) : (
              <DefaultCell value={undefined} />
            ),
          header: (props) => <DefaultHeaderCell value="Type" {...props} />,
          size: 80,
        }),
        columnHelper.accessor((row) => row.description, {
          id: "description",
          cell: (props) => <DefaultCell value={props.getValue()} />,
          header: (props) => (
            <DefaultHeaderCell value="Description" {...props} />
          ),
          size: 300,
        }),
        columnHelper.accessor((row) => row.data_categories, {
          id: "data_categories",
          cell: (props) => {
            return (
              <TaxonomiesPicker
                selectedTaxonomies={props.getValue() || []}
                onAddTaxonomy={() => {}}
                onRemoveTaxonomy={() => {}}
              />
            );
          },
          header: (props) => (
            <DefaultHeaderCell value="Data categories" {...props} />
          ),
          size: 300,
        }),

        columnHelper.display({
          id: "actions",
          header: "Actions",
          cell: ({ row }) => {
            const field = row.original;
            return (
              <HStack spacing={0} data-testid={`field-${field.name}`}>
                <Button
                  variant="outline"
                  size="xs"
                  leftIcon={<EditIcon />}
                  onClick={() => {
                    setSelectedFieldForEditing(field);
                    setIsEditingField(true);
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

  const tableInstance = useReactTable<DatasetField>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columns,
    data: fields,
  });

  const [isEditingField, setIsEditingField] = useState(false);
  const [selectedFieldForEditing, setSelectedFieldForEditing] = useState<
    DatasetField | undefined
  >();

  const handleRowClick = (field: DatasetField) => {
    // router.push({
    //   pathname: DATASET_URL_DETAIL_ROUTE,
    //   query: {
    //     id: datasetId,
    //     urn: collection.name,
    //   },
    // });
  };

  return (
    <Layout title={`Dataset - ${datasetId}`}>
      <PageHeader breadcrumbs={[{ title: "Datasets" }, { title: datasetId }]} />
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
          <EditFieldDrawer
            isOpen={isEditingField}
            onClose={() => {
              setIsEditingField(false);
              setSelectedFieldForEditing(undefined);
            }}
            field={selectedFieldForEditing}
            dataset={dataset!}
            collection={collection!}
          />
        </Box>
      )}
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
        No fields found.
      </Text>
    </VStack>
  </VStack>
);

export default FieldsDetailPage;
