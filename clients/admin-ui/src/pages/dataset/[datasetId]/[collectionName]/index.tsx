/* eslint-disable react/no-unstable-nested-components */
/* eslint-disable @typescript-eslint/no-use-before-define */
import {
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { AntButton, Box, EditIcon, HStack, Text, VStack } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import { DatabaseIcon } from "~/features/common/Icon/database/DatabaseIcon";
import { DatasetIcon } from "~/features/common/Icon/database/DatasetIcon";
import { TableIcon } from "~/features/common/Icon/database/TableIcon";
import Layout from "~/features/common/Layout";
import {
  DATASET_COLLECTION_SUBFIELD_DETAIL_ROUTE,
  DATASET_DETAIL_ROUTE,
  DATASET_ROUTE,
} from "~/features/common/nav/v2/routes";
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
import {
  useGetDatasetByKeyQuery,
  useUpdateDatasetMutation,
} from "~/features/dataset";
import DatasetBreadcrumbs from "~/features/dataset/DatasetBreadcrumbs";
import EditFieldDrawer from "~/features/dataset/EditFieldDrawer";
import { getUpdatedDatasetFromField } from "~/features/dataset/helpers";
import { DatasetField } from "~/types/api";

const columnHelper = createColumnHelper<DatasetField>();

const FieldsDetailPage: NextPage = () => {
  const router = useRouter();
  const [updateDataset] = useUpdateDatasetMutation();

  const datasetId = router.query.datasetId as string;
  const collectionName = router.query.collectionName as string;

  const { isLoading, data: dataset } = useGetDatasetByKeyQuery(datasetId);
  const collections = useMemo(() => dataset?.collections || [], [dataset]);
  const collection = collections.find((c) => c.name === collectionName);

  const fields: DatasetField[] = useMemo(
    () => collection?.fields || [],
    [collection],
  );

  const [globalFilter, setGlobalFilter] = useState<string>();

  const handleAddDataCategory = useCallback(
    ({
      dataCategory,
      field,
    }: {
      dataCategory: string;
      field: DatasetField;
    }) => {
      const dataCategories = field.data_categories || [];
      const updatedField = {
        ...field!,
        data_categories: [...dataCategories, dataCategory],
      };
      const collectionIndex = collections.indexOf(collection!);
      const fieldIndex = collection!.fields.indexOf(field!);
      const updatedDataset = getUpdatedDatasetFromField(
        dataset!,
        updatedField,
        collectionIndex,
        fieldIndex,
      );
      updateDataset(updatedDataset);
    },
    [collection, collections, dataset, updateDataset],
  );

  const handleRemoveDataCategory = useCallback(
    ({
      dataCategory,
      field,
    }: {
      dataCategory: string;
      field: DatasetField;
    }) => {
      const updatedField = {
        ...field!,
        data_categories: field!.data_categories?.filter(
          (dc) => dc !== dataCategory,
        ),
      };
      const collectionIndex = collections.indexOf(collection!);
      const fieldIndex = collection!.fields.indexOf(field!);
      const updatedDataset = getUpdatedDatasetFromField(
        dataset!,
        updatedField,
        collectionIndex,
        fieldIndex,
      );
      updateDataset(updatedDataset);
    },
    [collection, collections, dataset, updateDataset],
  );

  const handleRowClick = useCallback(
    (row: DatasetField) => {
      router.push({
        pathname: DATASET_COLLECTION_SUBFIELD_DETAIL_ROUTE,
        query: {
          datasetId,
          collectionName,
          subfieldUrn: row.name,
        },
      });
    },
    [datasetId, router, collectionName],
  );

  const columns = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => {
          const hasSubfields =
            props.row.original.fields && props.row.original.fields?.length > 0;
          return (
            <DefaultCell
              fontWeight={hasSubfields ? "semibold" : "normal"}
              value={props.getValue()}
            />
          );
        },
        header: (props) => <DefaultHeaderCell value="Field Name" {...props} />,
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
        cell: (props) => (
          <DefaultCell value={props.getValue()} cellProps={props} />
        ),
        header: (props) => <DefaultHeaderCell value="Description" {...props} />,
        size: 300,
        meta: {
          showHeaderMenu: true,
        },
      }),
      columnHelper.accessor((row) => row.data_categories, {
        id: "data_categories",
        cell: (props) => {
          const field = props.row.original;
          return (
            <TaxonomiesPicker
              selectedTaxonomies={props.getValue() || []}
              onAddTaxonomy={(dataCategory) =>
                handleAddDataCategory({ dataCategory, field })
              }
              onRemoveTaxonomy={(dataCategory) =>
                handleRemoveDataCategory({ dataCategory, field })
              }
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
              <AntButton
                size="small"
                icon={<EditIcon />}
                onClick={() => {
                  setSelectedFieldForEditing(field);
                  setIsEditingField(true);
                }}
              >
                Edit
              </AntButton>
            </HStack>
          );
        },
        meta: {
          disableRowClick: true,
        },
      }),
    ],
    [handleAddDataCategory, handleRemoveDataCategory],
  );

  const filteredFields = useMemo(() => {
    if (!globalFilter) {
      return fields;
    }

    return fields.filter((f) =>
      f.name.toLowerCase().includes(globalFilter.toLowerCase()),
    );
  }, [fields, globalFilter]);

  const tableInstance = useReactTable<DatasetField>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columns,
    data: filteredFields,
    columnResizeMode: "onChange",
  });

  const [isEditingField, setIsEditingField] = useState(false);
  const [selectedFieldForEditing, setSelectedFieldForEditing] = useState<
    DatasetField | undefined
  >();

  return (
    <Layout title={`Dataset - ${datasetId}`} mainProps={{ paddingTop: 0 }}>
      <PageHeader breadcrumbs={[{ title: "Datasets" }]}>
        <DatasetBreadcrumbs
          breadcrumbs={[
            {
              title: "All datasets",
              icon: <DatabaseIcon boxSize={4} />,
              link: DATASET_ROUTE,
            },
            {
              title: datasetId,
              link: {
                pathname: DATASET_DETAIL_ROUTE,
                query: { datasetId },
              },
              icon: <DatasetIcon boxSize={5} />,
            },
            {
              title: collectionName,
              icon: <TableIcon boxSize={5} />,
            },
          ]}
        />
      </PageHeader>

      {isLoading ? (
        <TableSkeletonLoader rowHeight={36} numRows={15} />
      ) : (
        <Box data-testid="fields-table">
          <TableActionBar>
            <GlobalFilterV2
              globalFilter={globalFilter}
              setGlobalFilter={setGlobalFilter}
              placeholder="Search"
              testid="fields-search"
            />
          </TableActionBar>
          <FidesTableV2
            tableInstance={tableInstance}
            emptyTableNotice={<EmptyTableNotice />}
            onRowClick={handleRowClick}
            getRowIsClickable={(row) => {
              const hasSubfields = Boolean(
                row.fields && row.fields?.length > 0,
              );
              return hasSubfields;
            }}
          />
          <EditFieldDrawer
            isOpen={isEditingField}
            onClose={() => {
              setIsEditingField(false);
              setSelectedFieldForEditing(undefined);
            }}
            field={selectedFieldForEditing}
            dataset={dataset!}
            collectionName={collectionName}
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
