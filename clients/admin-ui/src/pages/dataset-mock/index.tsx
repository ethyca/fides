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
  ChakraFlex as Flex,
  ChakraHStack as HStack,
  ChakraText as Text,
  ChakraVStack as VStack,
  Icons,
  Select,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  TableActionBar,
} from "~/features/common/table/v2";
import { HealthBadges } from "~/features/dataset-mock/HealthBadges";
import {
  HEALTH_BADGE_LABELS,
  HealthBadge,
  MOCK_DATASETS,
  MockDataset,
  sortDatasetsByHealth,
} from "~/features/dataset-mock/mock-data";

const HEALTH_FILTER_OPTIONS = [
  { value: "all", label: "All health states" },
  ...(
    Object.entries(HEALTH_BADGE_LABELS) as [HealthBadge, string][]
  ).map(([value, label]) => ({ value, label })),
];

const DATA_CATEGORY_FILTER_OPTIONS = [
  { value: "all", label: "All data categories" },
  { value: "user.contact", label: "user.contact (email, phone, address)" },
  { value: "user.financial", label: "user.financial" },
  { value: "user.name", label: "user.name" },
  { value: "user.unique_id", label: "user.unique_id" },
  { value: "system.operations", label: "system.operations" },
];

const columnHelper = createColumnHelper<MockDataset>();

const INTEGRATION_FILTER_OPTIONS = [
  { value: "all", label: "All integrations" },
  ...Array.from(
    new Set(MOCK_DATASETS.map((d) => d.integration).filter(Boolean)),
  ).map((i) => ({ value: i as string, label: i as string })),
  { value: "__manual__", label: "(manual)" },
];

const DataSetsMock: NextPage = () => {
  const router = useRouter();
  const [globalFilter, setGlobalFilter] = useState<string>("");
  const [healthFilter, setHealthFilter] = useState<string>(
    (router.query.health as string) ?? "all",
  );
  const [integrationFilter, setIntegrationFilter] = useState<string>(
    (router.query.integration as string) ?? "all",
  );
  const [dataCategoryFilter, setDataCategoryFilter] = useState<string>(
    (router.query.dataCategory as string) ?? "all",
  );

  const onRowClick = useCallback(
    (dataset: MockDataset) => {
      router.push(`/dataset-mock/${encodeURIComponent(dataset.fidesKey)}`);
    },
    [router],
  );

  const data = useMemo(() => {
    let sorted = sortDatasetsByHealth(MOCK_DATASETS);

    if (healthFilter !== "all") {
      sorted = sorted.filter((d) =>
        d.healthBadges.includes(healthFilter as HealthBadge),
      );
    }

    if (integrationFilter !== "all") {
      sorted = sorted.filter((d) => {
        if (integrationFilter === "__manual__") {
          return d.integration === null;
        }
        return d.integration === integrationFilter;
      });
    }

    // dataCategoryFilter is illustrative — in this mock, every dataset has at
    // least one collection so we don't actually narrow the list. The control is
    // present to communicate the requirement.

    if (!globalFilter.trim()) {
      return sorted;
    }
    const needle = globalFilter.toLowerCase();
    return sorted.filter(
      (d) =>
        d.name.toLowerCase().includes(needle) ||
        d.fidesKey.toLowerCase().includes(needle) ||
        d.description.toLowerCase().includes(needle),
    );
  }, [globalFilter, healthFilter, integrationFilter, dataCategoryFilter]);

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
          size: 220,
        }),
        columnHelper.accessor((row) => row.fidesKey, {
          id: "fides_key",
          cell: (props) => <DefaultCell value={props.getValue()} />,
          header: (props) => <DefaultHeaderCell value="Fides Key" {...props} />,
          size: 180,
        }),
        columnHelper.accessor((row) => row.healthBadges, {
          id: "health",
          cell: (props) => <HealthBadges badges={props.getValue()} />,
          header: (props) => <DefaultHeaderCell value="Health" {...props} />,
          size: 320,
          meta: { disableRowClick: false },
        }),
        columnHelper.accessor((row) => row.integration, {
          id: "integration",
          cell: (props) => (
            <DefaultCell value={props.getValue() ?? "—"} cellProps={props} />
          ),
          header: (props) => (
            <DefaultHeaderCell value="Integration" {...props} />
          ),
          size: 180,
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
            <HStack spacing={0} data-testid={`dataset-${row.original.fidesKey}`}>
              <Button size="small" icon={<Icons.Edit />}>
                Edit
              </Button>
            </HStack>
          ),
          meta: { disableRowClick: true },
        }),
      ].filter(Boolean) as ColumnDef<MockDataset, any>[],
    [],
  );

  const tableInstance = useReactTable<MockDataset>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columns,
    data,
    columnResizeMode: "onChange",
  });

  return (
    <Layout title="Datasets — Mock">
      <Box data-testid="dataset-mock-page">
        <PageHeader
          heading="Datasets"
          breadcrumbItems={[{ title: "All datasets" }]}
          rightContent={
            <Button data-testid="create-dataset-btn">+ Add dataset</Button>
          }
        />

        <Box data-testid="dataset-mock-table">
          <TableActionBar>
            <Flex gap={2} align="center" wrap="wrap" w="100%">
              <Box minW="220px" maxW="320px" flex={1}>
                <GlobalFilterV2
                  globalFilter={globalFilter}
                  setGlobalFilter={(v) => setGlobalFilter(v)}
                  placeholder="Search datasets / collections"
                  testid="dataset-search"
                />
              </Box>
              <Select
                value={healthFilter}
                onChange={(v) => setHealthFilter(v as string)}
                options={HEALTH_FILTER_OPTIONS}
                style={{ width: 220 }}
                data-testid="health-filter"
                aria-label="Filter by health badge"
              />
              <Select
                value={integrationFilter}
                onChange={(v) => setIntegrationFilter(v as string)}
                options={INTEGRATION_FILTER_OPTIONS}
                style={{ width: 220 }}
                data-testid="integration-filter"
                aria-label="Filter by integration"
              />
              <Select
                value={dataCategoryFilter}
                onChange={(v) => setDataCategoryFilter(v as string)}
                options={DATA_CATEGORY_FILTER_OPTIONS}
                style={{ width: 240 }}
                data-testid="data-category-filter"
                aria-label="Filter by data category"
              />
              {(healthFilter !== "all" ||
                integrationFilter !== "all" ||
                dataCategoryFilter !== "all") && (
                <Button
                  size="small"
                  icon={<Icons.Close />}
                  onClick={() => {
                    setHealthFilter("all");
                    setIntegrationFilter("all");
                    setDataCategoryFilter("all");
                  }}
                  data-testid="clear-filters"
                >
                  Clear filters
                </Button>
              )}
            </Flex>
          </TableActionBar>
          <FidesTableV2
            tableInstance={tableInstance}
            emptyTableNotice={<EmptyTableNotice />}
            onRowClick={onRowClick}
          />
        </Box>
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
      <Text fontSize="sm">Adjust your search or add a dataset.</Text>
    </VStack>
  </VStack>
);

export default DataSetsMock;
