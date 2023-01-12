import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Button,
  Heading,
  Spinner,
} from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";

import Layout from "~/features/common/Layout";
import { useGetAllDatasetsQuery } from "~/features/dataset/dataset.slice";
import DatasetsTable from "~/features/dataset/DatasetTable";

const DataSets: NextPage = () => {
  const { isLoading } = useGetAllDatasetsQuery();

  return (
    <Layout title="Datasets">
      <Heading mb={2} fontSize="2xl" fontWeight="semibold">
        Datasets
      </Heading>
      <Box mb={8}>
        <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
          <BreadcrumbItem>
            <NextLink href="/dataset">Datasets</NextLink>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <NextLink href="#">Select dataset</NextLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>
      <Box mb={4}>{isLoading ? <Spinner /> : <DatasetsTable />}</Box>
      <Box>
        <Button
          size="sm"
          mr={2}
          variant="outline"
          data-testid="create-dataset-btn"
        >
          <NextLink href="/dataset/new">Create new dataset</NextLink>
        </Button>
      </Box>
    </Layout>
  );
};

export default DataSets;
