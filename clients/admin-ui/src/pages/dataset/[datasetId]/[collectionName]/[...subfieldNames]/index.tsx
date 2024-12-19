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
  EditIcon,
  HStack,
  Text,
  VStack,
} from "fidesui";
import { cloneDeep, set } from "lodash";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import { NextBreadcrumbProps } from "~/features/common/nav/v2/NextBreadcrumb";
import {
  DATASET_COLLECTION_DETAIL_ROUTE,
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
import { DATA_BREADCRUMB_ICONS } from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import {
  useGetDatasetByKeyQuery,
  useUpdateDatasetMutation,
} from "~/features/dataset";
import EditFieldDrawer from "~/features/dataset/EditFieldDrawer";
import { getDatasetPath } from "~/features/dataset/helpers";
import { DatasetField } from "~/types/api";

const columnHelper = createColumnHelper<DatasetField>();

const FieldsDetailPage: NextPage = () => {
  const router = useRouter();
  const [updateDataset] = useUpdateDatasetMutation();

  const datasetId = decodeURIComponent(router.query.datasetId as string);
  const collectionName = decodeURIComponent(
    router.query.collectionName as string,
  );
  const subfieldNames = (router.query.subfieldNames as string[]).map(
    decodeURIComponent,
  );

  const { isLoading, data: dataset } = useGetDatasetByKeyQuery(datasetId);
  const collections = useMemo(() => dataset?.collections || [], [dataset]);
  const collection = collections.find((c) => c.name === collectionName);

  const fields: DatasetField[] = useMemo(
    () => collection?.fields || [],
    [collection],
  );

  const subfields: DatasetField[] = useMemo(() => {
    let currentSubfields = fields;
    subfieldNames.forEach((subfield) => {
      const field = currentSubfields.find((f) => f.name === subfield);
      currentSubfields = field?.fields || [];
    });
    return currentSubfields;
  }, [fields, subfieldNames]);

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
      const pathToField = getDatasetPath({
        dataset: dataset!,
        collectionName,
        subfields: [...subfieldNames, field.name],
      });

      const updatedDataset = cloneDeep(dataset!);
      set(updatedDataset, `${pathToField}.data_categories`, [
        ...dataCategories,
        dataCategory,
      ]);
      updateDataset(updatedDataset);
    },
    [dataset, updateDataset, collectionName, subfieldNames],
  );

  const handleRemoveDataCategory = useCallback(
    ({
      dataCategory,
      field,
    }: {
      dataCategory: string;
      field: DatasetField;
    }) => {
      const dataCategories = field.data_categories || [];
      const pathToField = getDatasetPath({
        dataset: dataset!,
        collectionName,
        subfields: [...subfieldNames, field?.name],
      });

      const updatedDataset = cloneDeep(dataset!);
      set(
        updatedDataset,
        `${pathToField}.data_categories`,
        dataCategories.filter((dc) => dc !== dataCategory),
      );
      updateDataset(updatedDataset);
    },
    [dataset, updateDataset, collectionName, subfieldNames],
  );

  const handleRowClick = useCallback(
    (row: DatasetField) => {
      const subfieldQuery = [
        ...subfieldNames.map(encodeURIComponent),
        row.name,
      ];
      router.push({
        pathname: DATASET_COLLECTION_SUBFIELD_DETAIL_ROUTE,
        query: {
          datasetId,
          collectionName,
          subfieldNames: subfieldQuery,
        },
      });
    },
    [datasetId, router, collectionName, subfieldNames],
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
          // TODO: HJ-20 remove this check when data categories can be added to subfields
          const hasSubfields =
            props.row.original.fields && props.row.original.fields?.length > 0;
          return (
            !hasSubfields && (
              <TaxonomiesPicker
                selectedTaxonomies={props.getValue() || []}
                onAddTaxonomy={(dataCategory) =>
                  handleAddDataCategory({ dataCategory, field })
                }
                onRemoveTaxonomy={(dataCategory) =>
                  handleRemoveDataCategory({ dataCategory, field })
                }
              />
            )
          );
        },
        header: (props) => (
          <DefaultHeaderCell value="Data categories" {...props} />
        ),
        size: 300,
        meta: { disableRowClick: true },
      }),

      columnHelper.display({
        id: "actions",
        header: "Actions",
        cell: ({ row }) => {
          const field = row.original;
          return (
            <HStack spacing={0} data-testid={`field-${field.name}`}>
              <Button
                size="small"
                icon={<EditIcon />}
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
    ],
    [handleAddDataCategory, handleRemoveDataCategory],
  );

  const filteredSubfields = useMemo(() => {
    if (!globalFilter) {
      return subfields;
    }

    return subfields.filter((f) =>
      f.name.toLowerCase().includes(globalFilter.toLowerCase()),
    );
  }, [subfields, globalFilter]);

  const tableInstance = useReactTable<DatasetField>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columns,
    data: filteredSubfields,
    columnResizeMode: "onChange",
  });

  const [isEditingField, setIsEditingField] = useState(false);
  const [selectedFieldForEditing, setSelectedFieldForEditing] = useState<
    DatasetField | undefined
  >();

  const breadcrumbs = useMemo(() => {
    const baseBreadcrumbs: NextBreadcrumbProps["items"] = [
      {
        title: "All datasets",
        href: DATASET_ROUTE,
      },
      {
        title: datasetId,
        href: {
          pathname: DATASET_DETAIL_ROUTE,
          query: { datasetId },
        },
        icon: DATA_BREADCRUMB_ICONS[1],
      },
      {
        title: collectionName,
        icon: DATA_BREADCRUMB_ICONS[2],
        href: {
          pathname: DATASET_COLLECTION_DETAIL_ROUTE,
          query: { datasetId, collectionName },
        },
      },
    ];
    subfieldNames.forEach((subfield, index) => {
      baseBreadcrumbs.push({
        title: subfield,
        href:
          index < subfieldNames.length - 1
            ? {
                pathname: DATASET_COLLECTION_SUBFIELD_DETAIL_ROUTE,
                query: {
                  datasetId,
                  collectionName,
                  subfieldNames: subfieldNames
                    .slice(0, index + 1)
                    .map(encodeURIComponent),
                },
              }
            : undefined,
        icon: DATA_BREADCRUMB_ICONS[3],
      });
    });
    return baseBreadcrumbs;
  }, [datasetId, collectionName, subfieldNames]);

  return (
    <Layout title={`Dataset - ${datasetId}`}>
      <PageHeader heading="Datasets" breadcrumbItems={breadcrumbs} />

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
            subfields={subfieldNames}
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
