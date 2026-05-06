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
  Button,
  ChakraBox as Box,
  ChakraHStack as HStack,
  ChakraText as Text,
  ChakraVStack as VStack,
  CUSTOM_TAG_COLOR,
  Icons,
  Tag,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  TableActionBar,
} from "~/features/common/table/v2";
import { DatasetDetailHeader } from "~/features/dataset-mock/DatasetDetailHeader";
import { LinkedActionCenterSection } from "~/features/dataset-mock/LinkedActionCenterSection";
import {
  findDatasetByKey,
  MockCollection,
} from "~/features/dataset-mock/mock-data";
import { TryDsrDrawer } from "~/features/dataset-mock/TryDsrDrawer";

const columnHelper = createColumnHelper<MockCollection>();

const collectionStatusTag = (status: MockCollection["status"]) => {
  if (status === "needs-dsr-wiring") {
    return <Tag color={CUSTOM_TAG_COLOR.ERROR}>Needs DSR wiring</Tag>;
  }
  if (status === "skipped") {
    return <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>Skipped</Tag>;
  }
  return <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>OK</Tag>;
};

const DatasetMockDetailPage: NextPage = () => {
  const router = useRouter();
  const datasetIdParam = router.query.datasetId as string | undefined;
  const datasetId = datasetIdParam
    ? decodeURIComponent(datasetIdParam)
    : "legacy_orders_pg";
  const dataset = findDatasetByKey(datasetId);

  const [globalFilter, setGlobalFilter] = useState<string>("");
  const [tryDsrOpen, setTryDsrOpen] = useState<boolean>(
    router.query.tryDsr === "open",
  );

  const collections = dataset?.collections ?? [];

  const filtered = useMemo(() => {
    if (!globalFilter.trim()) {
      return collections;
    }
    const needle = globalFilter.toLowerCase();
    return collections.filter(
      (c) =>
        c.name.toLowerCase().includes(needle) ||
        c.description.toLowerCase().includes(needle),
    );
  }, [collections, globalFilter]);

  const columns = useMemo(
    () =>
      [
        columnHelper.accessor((row) => row.name, {
          id: "name",
          cell: (props) => (
            <DefaultCell value={props.getValue()} fontWeight="semibold" />
          ),
          header: (props) => (
            <DefaultHeaderCell value="Collection Name" {...props} />
          ),
          size: 180,
        }),
        columnHelper.accessor((row) => row.status, {
          id: "status",
          cell: (props) => collectionStatusTag(props.getValue()),
          header: (props) => <DefaultHeaderCell value="Status" {...props} />,
          size: 160,
        }),
        columnHelper.accessor((row) => row.fieldCount, {
          id: "fieldCount",
          cell: (props) => <DefaultCell value={String(props.getValue())} />,
          header: (props) => <DefaultHeaderCell value="Fields" {...props} />,
          size: 90,
        }),
        columnHelper.accessor((row) => row.approvedFieldPct, {
          id: "approved",
          cell: (props) => <DefaultCell value={`${props.getValue()}%`} />,
          header: (props) => <DefaultHeaderCell value="Approved" {...props} />,
          size: 110,
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
          meta: { showHeaderMenu: true },
        }),
        columnHelper.display({
          id: "actions",
          header: "Actions",
          cell: ({ row }) => (
            <HStack spacing={0} data-testid={`collection-${row.original.name}`}>
              <Button size="small" icon={<Icons.Edit />}>
                Edit
              </Button>
            </HStack>
          ),
          meta: { disableRowClick: true },
        }),
      ].filter(Boolean) as ColumnDef<MockCollection, any>[],
    [],
  );

  const tableInstance = useReactTable<MockCollection>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columns,
    data: filtered,
    columnResizeMode: "onChange",
  });

  if (!dataset) {
    return (
      <Layout title="Dataset not found">
        <Box p={6}>
          <Text>Dataset not found.</Text>
        </Box>
      </Layout>
    );
  }

  return (
    <Layout title={`Dataset — ${dataset.name}`}>
      <Box data-testid="dataset-mock-detail">
        <PageHeader
          heading="Datasets"
          breadcrumbItems={[
            { title: "All datasets", href: "/dataset-mock" },
            { title: dataset.fidesKey },
          ]}
          rightContent={
            <Button icon={<Icons.Flow />} data-testid="visual-editor-btn">
              Visual editor
            </Button>
          }
        />

        <DatasetDetailHeader
          dataset={dataset}
          onTryDsr={() => setTryDsrOpen(true)}
        />

        <LinkedActionCenterSection dataset={dataset} />

        <Box data-testid="collections-table">
          <TableActionBar>
            <GlobalFilterV2
              globalFilter={globalFilter}
              setGlobalFilter={(v) => setGlobalFilter(v)}
              placeholder="Search collections"
              testid="collections-search"
            />
          </TableActionBar>
          <FidesTableV2
            tableInstance={tableInstance}
            emptyTableNotice={<EmptyTableNotice />}
            onRowClick={(c) =>
              router.push(
                `/dataset-mock/${encodeURIComponent(dataset.fidesKey)}/${encodeURIComponent(c.name)}`,
              )
            }
          />
        </Box>

        <TryDsrDrawer
          open={tryDsrOpen}
          onClose={() => setTryDsrOpen(false)}
          dataset={dataset}
          onFixFailures={(name) =>
            router.push(
              `/dataset-mock/${encodeURIComponent(dataset.fidesKey)}/${encodeURIComponent(name)}?wire=open`,
            )
          }
        />
      </Box>
    </Layout>
  );
};

const EmptyTableNotice = () => (
  <VStack mt={6} p={10} spacing={4} textAlign="center">
    <Text>No collections found.</Text>
  </VStack>
);

export default DatasetMockDetailPage;
